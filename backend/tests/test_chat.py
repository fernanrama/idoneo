"""Modo texto (POST /api/sessions/{id}/chat) con Claude simulado."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agentes import chat, claude
from app.agentes.extractor import Extraccion
from app.main import app
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
    cliente = TestClient(app)
    sid = cliente.post("/api/sessions", json={"client_id": "texto-1", "channel": "text"}).json()["session_id"]
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
