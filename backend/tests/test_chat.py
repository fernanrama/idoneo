"""Modo texto (POST /api/sessions/{id}/chat) con Claude simulado."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agentes import chat, claude
from app.agentes.extractor import Extraccion
from app.main import app
from tests.soporte_acceso import cliente_autorizado
from app.perfil import store
from app.perfil.modelos import OBLIGATORIOS, Perfil


@pytest.fixture
def api(monkeypatch):
    store.reiniciar()
    llamadas: list[dict] = []
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")

    async def falso(**kw):
        llamadas.append(kw)
        if kw["esquema"] is chat.Respuesta:
            n = sum(1 for c in llamadas if c["esquema"] is chat.Respuesta)
            salida = chat.Respuesta(texto=f"Pregunta {n}", terminada=False)
        else:
            salida = Extraccion(datos=[], conocimientos=[], escenario=None)
        return salida, claude.Uso(agente=kw["agente"], modelo="simulado", tokens_entrada=1, tokens_salida=1, latencia_s=0)

    monkeypatch.setattr(claude, "estructurado", falso)
    cliente = cliente_autorizado()
    sesion = cliente.post("/api/sessions", json={"channel": "text"}).json()
    sid = sesion["session_id"]
    return cliente, sid, llamadas


def test_el_asistente_empieza_y_luego_responde_al_cliente(api):
    cliente, sid, llamadas = api
    r = cliente.post(f"/api/sessions/{sid}/chat", json={}).json()
    assert r["client_turn"] is None and r["agent_turn"]["text"] == "Pregunta 1" and r["finished"] is False

    r = cliente.post(f"/api/sessions/{sid}/chat", json={"text": "  Quiero complementar la pensión.  "}).json()
    assert r["client_turn"]["text"] == "Quiero complementar la pensión."
    assert r["agent_turn"]["text"] == "Pregunta 2"

    turnos = cliente.get(f"/api/sessions/{sid}").json()["turns"]
    assert [t["speaker"] for t in turnos] == ["agent", "client", "agent"]
    # El entrevistador recibe el guion y la conversación; el extractor se lanzó con el turno del cliente.
    entrevistas = [c for c in llamadas if c["esquema"] is chat.Respuesta]
    assert "asistente de perfil inversor" in entrevistas[0]["sistema"]
    assert "Cliente: Quiero complementar la pensión." in entrevistas[1]["mensaje"]
    assert any(c["esquema"] is Extraccion for c in llamadas)


def test_sin_clave_responde_503(api, monkeypatch):
    cliente, sid, _ = api
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert cliente.post(f"/api/sessions/{sid}/chat", json={"text": "hola"}).status_code == 503


def test_sesion_inexistente_404(api):
    cliente, _, _ = api
    assert cliente.post("/api/sessions/s-nope/chat", json={}).status_code == 404


def test_texto_demasiado_largo_422(api):
    cliente, sid, _ = api
    assert cliente.post(f"/api/sessions/{sid}/chat", json={"text": "x" * 2001}).status_code == 422


def test_pendientes_sigue_el_orden_del_guion():
    assert chat.pendientes(Perfil(client_id="x")) == OBLIGATORIOS


def test_lo_que_el_cliente_no_conoce_no_se_vuelve_a_comprobar():
    from app.perfil.modelos import Fact, Flag, Fuente

    perfil = Perfil(client_id="x", mifid={
        "knowledge.etfs": Fact(value="none", source=Fuente.declared, confidence=0.5,
                               flags=[Flag.low_confidence], updated_by="agent:extractor"),
        "knowledge.stocks": Fact(value="medium", source=Fuente.declared, confidence=0.5,
                                 flags=[Flag.low_confidence], updated_by="agent:extractor"),
    })
    pend = chat.pendientes(perfil)
    assert "knowledge.etfs" not in pend
    assert "knowledge.stocks" in pend


def test_pendientes_para_voz_en_palabras_y_sin_rutas():
    from app.perfil.modelos import Fact, Flag, Fuente

    texto = chat.pendientes_para_voz(Perfil(client_id="x"))
    assert texto.startswith("Falta preguntar:") and "ingresos netos al mes" in texto
    assert "qué sabe de fondos de renta variable" in texto and "financial." not in texto

    hecho = {c: Fact(value=1, source=Fuente.declared, confidence=0.9, updated_by="agent:extractor") for c in OBLIGATORIOS}
    hecho["knowledge.equity_funds"] = Fact(value="medium", source=Fuente.declared, confidence=0.9, updated_by="agent:extractor")
    hecho["knowledge.fixed_income_funds"] = Fact(value="basic", source=Fuente.demonstrated, confidence=0.9, updated_by="agent:extractor")
    hecho["financial.debts_eur"] = Fact(value=0, source=Fuente.declared, confidence=0.5, flags=[Flag.low_confidence],
                                        updated_by="agent:extractor")
    texto = chat.pendientes_para_voz(Perfil(client_id="x", mifid=hecho))
    assert "Falta preguntar" not in texto
    assert "vuelve a preguntar con otras palabras: deudas" in texto
    assert "falta la pregunta de comprobación: qué sabe de fondos de renta variable." in texto


def test_pendientes_para_voz_sin_nada_pendiente():
    from app.perfil.modelos import Fact, Fuente

    hecho = {c: Fact(value=1, source=Fuente.demonstrated, confidence=0.9, updated_by="agent:extractor") for c in OBLIGATORIOS}
    assert chat.pendientes_para_voz(Perfil(client_id="x", mifid=hecho)) == "No falta nada: puedes cerrar la entrevista."


def test_cada_ruta_del_perfil_tiene_descripcion():
    from app.perfil.modelos import CALCULADOS, CAMPOS

    sin = [c for c in CAMPOS if c not in CALCULADOS and chat.describir(c) == c]
    assert sin == []


def test_endpoint_de_pendientes_para_el_agente_de_voz(api):
    cliente, sid, _ = api
    r = cliente.get(f"/api/sessions/{sid}/pending")
    assert r.status_code == 200
    assert r.json()["pending"] == OBLIGATORIOS and r.json()["text"].startswith("Falta preguntar:")
    assert cliente.get("/api/sessions/s-nope/pending").status_code == 404
