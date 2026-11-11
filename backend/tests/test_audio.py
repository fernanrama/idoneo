"""Pruebas de audio: descarga desde ElevenLabs (simulado), alineación, guardado de solo añadir y fragmentos."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import audio
from app.main import app
from app.perfil import store
from app.perfil.almacenes.base import AudioSesion
from app.perfil.almacenes.bd import AlmacenBD
from app.perfil.almacenes.memoria import AlmacenMemoria
from app.perfil.modelos import Evidencia, Fuente, Parche, Perfil, Turno
from tests.soporte_acceso import cabeceras_cliente
from tests.soporte_bd import POSTGRES_TEST, postgres_recien_migrado

AGENTE = "agent_de_prueba"
MP3 = b"ID3" + b"\x00" * 64
_CLIENTE_HTTP = httpx.AsyncClient

OFICIAL = [
    {"role": "agent", "message": "Hola, soy una inteligencia artificial. ¿Grabamos?", "time_in_call_secs": 0},
    {"role": "user", "message": "Sí, de acuerdo, puede grabar.", "time_in_call_secs": 6},
    {"role": "agent", "message": None, "time_in_call_secs": 8},  # llamada a una herramienta: sin texto
    {"role": "agent", "message": "¿Qué pasa si la bolsa cae un veinte por ciento?", "time_in_call_secs": 9},
    {"role": "user", "message": "Eso no puede pasar, el fondo es del banco.", "time_in_call_secs": 14},
]


@pytest.fixture
def voz(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-sintetica")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", AGENTE)
    audio._estado.clear()
    audio._en_curso.clear()
    yield


def _sesion_con_turnos(cid: str = "cliente-audio") -> str:
    store.reiniciar()
    store.crear_nuevo(cid)
    sid = store.crear_sesion(cid, "voice")["session_id"]
    for speaker, texto, t in [("agent", "Hola, soy una inteligencia artificial. ¿Grabamos?", 0),
                              ("client", "Sí, de acuerdo, puede grabar", 5),
                              ("agent", "¿Qué pasa si la bolsa cae un 20 %?", 10),
                              ("client", "Eso no puede pasar, el fondo es del banco.", 13)]:
        store.anadir_turno(sid, Turno(speaker=speaker, text=texto, t_start=t, t_end=t + 2))
    return sid


def _elevenlabs(monkeypatch, sid: str, *, agente: str = AGENTE, estado: str = "done", audio_status: int = 200,
                llamadas: list | None = None):
    def manejador(peticion: httpx.Request) -> httpx.Response:
        if llamadas is not None:
            llamadas.append(peticion.url.path)
        assert peticion.headers["xi-api-key"] == "clave-sintetica"
        if peticion.url.path.endswith("/audio"):
            return httpx.Response(audio_status, content=MP3 if audio_status == 200 else b"",
                                  headers={"content-type": "audio/mpeg"})
        return httpx.Response(200, json={
            "agent_id": agente, "conversation_id": "conv_1", "status": estado, "has_audio": True,
            "transcript": OFICIAL, "metadata": {"call_duration_secs": 20},
            "conversation_initiation_client_data": {"dynamic_variables": {"session_id": sid}},
        })

    monkeypatch.setattr(audio.httpx, "AsyncClient",
                        lambda **kw: _CLIENTE_HTTP(transport=httpx.MockTransport(manejador), **kw))


# ---------- alineación ----------

def test_mensajes_oficiales_calcula_el_fin_y_quita_los_vacios():
    m = audio.mensajes_oficiales(OFICIAL, 20)
    assert [x["start"] for x in m] == [0, 6, 9, 14]
    assert [x["end"] for x in m] == [6, 9, 14, 20]


def test_alinear_empareja_por_hablante_y_texto_en_orden():
    turnos = [Turno(turn_id="t-001", speaker="agent", text="Hola, soy una inteligencia artificial. ¿Grabamos?", t_start=0, t_end=1),
              Turno(turn_id="t-002", speaker="client", text="Sí, de acuerdo, puede grabar", t_start=0, t_end=1),
              Turno(turn_id="t-003", speaker="client", text="algo que ElevenLabs no transcribió", t_start=0, t_end=1),
              Turno(turn_id="t-004", speaker="client", text="eso no puede pasar el fondo es del banco", t_start=0, t_end=1)]
    tiempos = audio.alinear(turnos, audio.mensajes_oficiales(OFICIAL, 20))
    assert tiempos == {"t-001": [0, 6], "t-002": [6, 9], "t-004": [14, 20]}


# ---------- descarga ----------

def test_recuperar_guarda_audio_y_tiempos_reales(monkeypatch, voz):
    sid = _sesion_con_turnos()
    _elevenlabs(monkeypatch, sid)
    assert asyncio.run(audio.recuperar(sid, "conv_1")) is True
    info, datos = store.audio(sid)
    assert datos == MP3 and info.content_type == "audio/mpeg" and info.duration_s == 20
    assert info.timings == {"t-001": [0, 6], "t-002": [6, 9], "t-003": [9, 14], "t-004": [14, 20]}
    assert store.sesion(sid)["conversation_id"] == "conv_1"
    # De solo añadir: un segundo intento no sustituye nada.
    assert asyncio.run(audio.recuperar(sid, "conv_1")) is False


@pytest.mark.parametrize("agente, sesion_ajena", [("otro_agente", False), (AGENTE, True)])
def test_no_acepta_la_conversacion_de_otro(monkeypatch, voz, agente, sesion_ajena):
    sid = _sesion_con_turnos()
    _elevenlabs(monkeypatch, "s-de-otra-persona" if sesion_ajena else sid, agente=agente)
    asyncio.run(audio.recuperar_con_reintentos(sid, "conv_1", esperas=()))
    assert audio.estado(sid)["status"] == "failed"
    assert store.info_audio([sid]) == {}
    assert store.sesion(sid)["conversation_id"] is None


def test_reintenta_mientras_elevenlabs_procesa(monkeypatch, voz):
    sid = _sesion_con_turnos()
    llamadas: list = []
    _elevenlabs(monkeypatch, sid, estado="processing", llamadas=llamadas)
    asyncio.run(audio.recuperar_con_reintentos(sid, "conv_1", esperas=(0.0, 0.0)))
    assert len(llamadas) == 3 and audio.estado(sid)["status"] == "failed"
    _elevenlabs(monkeypatch, sid)
    asyncio.run(audio.recuperar_con_reintentos(sid, "conv_1", esperas=()))
    assert audio.estado(sid)["status"] == "ready"


def test_rechaza_un_audio_demasiado_grande(monkeypatch, voz):
    sid = _sesion_con_turnos()
    monkeypatch.setattr(audio, "MAX_AUDIO_BYTES", 10)
    _elevenlabs(monkeypatch, sid)
    with pytest.raises(RuntimeError, match="tamaño"):
        asyncio.run(audio.recuperar(sid, "conv_1"))
    assert store.info_audio([sid]) == {}


# ---------- fragmentos de cada evidencia ----------

def _evidencia(sid: str, turn_id: str, t=(50.0, 52.0)) -> Evidencia:
    return Evidencia(session_id=sid, turn_id=turn_id, t=t, quote="Eso no puede pasar, el fondo es del banco.")


def test_fragmento_usa_tiempos_reales_o_los_del_navegador():
    info = AudioSesion(session_id="s1", conversation_id="c", content_type="audio/mpeg", size_bytes=1,
                       duration_s=20, timings={"t-004": [14, 20]})
    exacto = audio.fragmento(_evidencia("s1", "t-004"), info)
    assert (exacto.start, exacto.end, exacto.exact) == (13.6, 20, True)  # margen, sin pasar del final
    aproximado = audio.fragmento(_evidencia("s1", "t-009", t=(3.0, 5.0)), info)
    assert (aproximado.start, aproximado.end, aproximado.exact) == (2.6, 5.4, False)
    assert audio.fragmento(_evidencia("s1", "t-004"), None) is None


# ---------- API ----------

def _con_evidencia(sid: str, cid: str = "cliente-audio") -> None:
    store.aplicar(cid, [Parche(path="knowledge.equity_funds", value="none", source=Fuente.demonstrated,
                               confidence=0.9, evidence=[_evidencia(sid, "t-004")])],
                  "prueba de audio", "agent:extractor")


def test_api_de_punta_a_punta(monkeypatch, voz):
    sid = _sesion_con_turnos()
    _elevenlabs(monkeypatch, sid)
    _con_evidencia(sid)
    api = TestClient(app, headers=cabeceras_cliente("cliente-audio", servicio=False))

    r = api.post(f"/api/sessions/{sid}/audio", json={"conversation_id": "conv_1"})
    assert r.status_code == 202 and r.json()["status"] == "pending"  # la tarea corre tras responder
    assert api.get(f"/api/sessions/{sid}/audio/status").json()["status"] == "ready"

    r = api.get(f"/api/sessions/{sid}/audio")
    assert r.status_code == 200 and r.content == MP3 and r.headers["cache-control"] == "no-store"

    clips = api.get("/api/clients/cliente-audio/audio").json()["evidence"]["knowledge.equity_funds"]
    assert clips == [{"session_id": sid, "turn_id": "t-004", "start": 13.6, "end": 20.0, "exact": True,
                      "url": f"/api/sessions/{sid}/audio"}]
    ev = api.get("/api/clients/cliente-audio/evidence/knowledge.equity_funds").json()["evidence"]
    assert ev[0]["audio"]["start"] == 13.6

    # Otra persona no puede ni pedirlo ni escucharlo.
    ajeno = TestClient(app, headers=cabeceras_cliente("carmen-68", servicio=False))
    assert ajeno.get(f"/api/sessions/{sid}/audio").status_code == 404
    assert ajeno.post(f"/api/sessions/{sid}/audio", json={"conversation_id": "conv_1"}).status_code == 404


def test_api_sin_voz_configurada_o_en_texto(voz, monkeypatch):
    store.reiniciar()
    store.crear_nuevo("cliente-texto")
    sid = store.crear_sesion("cliente-texto", "text")["session_id"]
    api = TestClient(app, headers=cabeceras_cliente("cliente-texto", servicio=False))
    assert api.post(f"/api/sessions/{sid}/audio", json={"conversation_id": "c1"}).status_code == 409
    sid = store.crear_sesion("cliente-texto", "voice")["session_id"]
    assert api.post(f"/api/sessions/{sid}/audio", json={"conversation_id": "no válido"}).status_code == 422
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    assert api.post(f"/api/sessions/{sid}/audio", json={"conversation_id": "c1"}).status_code == 503
    assert api.get(f"/api/sessions/{sid}/audio").status_code == 404


def test_mcp_get_evidence_incluye_el_fragmento(monkeypatch, voz):
    from app.mcp import servidor

    sid = _sesion_con_turnos()
    _elevenlabs(monkeypatch, sid)
    _con_evidencia(sid)
    asyncio.run(audio.recuperar(sid, "conv_1"))
    monkeypatch.setattr(servidor, "_autorizar", lambda _cid: None)
    r = servidor.get_evidence("cliente-audio", "knowledge.equity_funds")
    assert r["evidence"][0]["audio"]["url"] == f"/api/sessions/{sid}/audio"


# ---------- almacenes ----------

def _registro(sid: str) -> AudioSesion:
    return AudioSesion(session_id=sid, conversation_id="c", content_type="audio/mpeg", size_bytes=len(MP3),
                       duration_s=3.0, timings={"t-001": [0, 1.5]}, transcript=[{"role": "user", "message": "hola"}])


@pytest.mark.parametrize("tipo", ["memoria", "sqlite", "postgres"])
def test_almacenes_guardan_una_sola_vez(tipo):
    from datetime import datetime, timezone

    if tipo == "postgres" and not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local de pruebas)")
    a = {"memoria": AlmacenMemoria, "sqlite": lambda: AlmacenBD.desde_url("sqlite://"),
         "postgres": lambda: AlmacenBD.desde_url(postgres_recien_migrado())}[tipo]()
    ahora = datetime.now(timezone.utc)
    if tipo != "memoria":
        a.crear(Perfil(client_id="c1"))
    a.crear_sesion("s1", "c1", "voice", ahora)
    assert a.audio_disponible()
    assert a.guardar_audio(_registro("s1"), MP3, ahora) is True
    assert a.guardar_audio(_registro("s1"), b"otro", ahora) is False
    info, datos = a.audio("s1")
    assert datos == MP3 and info.timings == {"t-001": [0, 1.5]} and info.transcript[0]["message"] == "hola"
    assert set(a.info_audio(["s1", "s2"])) == {"s1"}
    if tipo != "memoria":
        with pytest.raises(Exception, match="solo añadir"), a.motor.begin() as c:
            c.execute(text("update session_audio set content_type = 'x'"))


def test_bd_sin_la_tabla_de_audio_sigue_funcionando():
    a = AlmacenBD.desde_url("sqlite://")
    with a.motor.begin() as c:
        c.execute(text("drop table session_audio"))
    a._con_audio = None
    assert a.audio_disponible() is False
    assert a.audio("s1") is None and a.info_audio(["s1"]) == {}
