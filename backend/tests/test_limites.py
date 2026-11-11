"""Topes de gasto para la demo pública: apagados por defecto, 429 al llegar al límite."""

import os

os.environ["DATA_PERSIST"] = "0"

import httpx  # noqa: E402
import pytest  # noqa: E402

from app import limites, voz  # noqa: E402
from tests.soporte_acceso import cliente_autorizado  # noqa: E402


@pytest.fixture(autouse=True)
def contadores_limpios():
    limites.reiniciar()
    yield
    limites.reiniciar()


def test_sin_variables_no_hay_limite(monkeypatch):
    for v in ("LIMITE_SESIONES_DIA", "LIMITE_VOZ_DIA", "LIMITE_TURNOS_SESION"):
        monkeypatch.delenv(v, raising=False)
    api = cliente_autorizado()
    assert all(api.post("/api/sessions", json={}).status_code == 200 for _ in range(5))


def test_tope_diario_de_entrevistas_nuevas(monkeypatch):
    monkeypatch.setenv("LIMITE_SESIONES_DIA", "2")
    api = cliente_autorizado()
    assert [api.post("/api/sessions", json={}).status_code for _ in range(3)] == [200, 200, 429]
    r = api.post("/api/sessions", json={})
    assert r.status_code == 429 and "demo guiada" in r.json()["detail"]


def test_el_contador_se_reinicia_cada_dia(monkeypatch):
    monkeypatch.setenv("LIMITE_SESIONES_DIA", "1")
    api = cliente_autorizado()
    assert api.post("/api/sessions", json={}).status_code == 200
    assert api.post("/api/sessions", json={}).status_code == 429
    monkeypatch.setattr(limites, "_hoy", lambda: "2099-01-01")
    assert api.post("/api/sessions", json={}).status_code == 200


def test_tope_de_mensajes_por_entrevista(monkeypatch):
    monkeypatch.setenv("LIMITE_TURNOS_SESION", "2")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    api = cliente_autorizado()
    s = api.post("/api/sessions", json={}).json()
    turno = {"speaker": "client", "text": "hola", "t_start": 0, "t_end": 1}
    url = f"/api/sessions/{s['session_id']}/turns"
    assert [api.post(url, json=turno).status_code for _ in range(3)] == [202, 202, 429]
    # Los turnos del asistente no cuentan.
    assert api.post(url, json={**turno, "speaker": "agent"}).status_code == 202


def test_tope_diario_de_conexiones_de_voz(monkeypatch):
    monkeypatch.setenv("LIMITE_VOZ_DIA", "1")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agente")
    real = httpx.AsyncClient
    monkeypatch.setattr(voz.httpx, "AsyncClient", lambda **kw: real(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"signed_url": "wss://x"})), **kw))
    api = cliente_autorizado()
    s = api.post("/api/sessions", json={}).json()
    assert api.post("/api/voice/bootstrap", json={"session_id": s["session_id"]}).status_code == 200
    assert api.post("/api/voice/bootstrap", json={"session_id": s["session_id"]}).status_code == 429
