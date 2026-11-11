"""Entrevista corta del pitch: fixture ficticio `carmen-corta`, casi completo, que se termina en directo.

Sin proveedores: la parte de Claude se simula escribiendo los tres datos que faltan como lo haría el
extractor (con su cita). Se comprueba que el recorrido llega a validar y que el MCP lo sirve como usable.
"""
from __future__ import annotations

import asyncio
import json

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.agentes import chat
from app.main import app
from app.mcp.servidor import mcp
from app.perfil import calculos, store
from app.perfil.modelos import Conveniencia, EstadoPerfil, Fuente, Parche

C = "carmen-corta"
BASE = "/api/demo/asesor"
TOKEN = "asesor-demo-sintetico-solo-para-tests-0123456789"
MCP_TOKEN = "mcp-demo-sintetico-solo-para-tests-0123456789abcdef"
FALTAN = ["knowledge.equity_funds", "risk_tolerance.scenario_score", "sustainability.preference"]


@pytest.fixture
def modo(monkeypatch):
    monkeypatch.setenv("DEMO_ADVISOR_MODE", "1")
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", TOKEN)
    monkeypatch.delenv("DEMO_ADVISOR_CLIENTS", raising=False)
    store.reiniciar()


def local() -> TestClient:
    return TestClient(app, base_url="http://localhost", client=("127.0.0.1", 51000))


def asesor() -> dict[str, str]:
    return {"X-Demo-Advisor-Token": TOKEN}


def empezar(c: TestClient, canal: str = "voice"):
    return c.post(f"{BASE}/clientes/{C}/entrevista", params={"channel": canal}, headers=asesor())


def test_el_fixture_es_ficticio_y_solo_faltan_los_tres_datos_del_directo():
    perfil = store.cargar_fixture(C)
    assert perfil.reason.startswith("DATOS SIMULADOS")
    assert calculos.faltan(perfil) == FALTAN
    assert perfil.status == EstadoPerfil.draft and not perfil.alerts
    # El entrevistador solo tiene que preguntar eso (lo obligatorio primero).
    assert chat.pendientes(perfil)[:3] == FALTAN


def test_apagado_por_defecto_no_existe(monkeypatch):
    monkeypatch.delenv("DEMO_ADVISOR_MODE", raising=False)
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", TOKEN)
    assert empezar(local()).status_code == 404


def test_sin_token_o_desde_fuera_se_rechaza(modo):
    assert local().post(f"{BASE}/clientes/{C}/entrevista").status_code in (401, 403)
    remoto = TestClient(app, base_url="http://localhost", client=("10.0.0.7", 51000))
    assert empezar(remoto).status_code == 403


def test_solo_clientes_de_la_lista_y_canal_valido(modo):
    c = local()
    assert c.post(f"{BASE}/clientes/cliente-cualquiera/entrevista", headers=asesor()).status_code == 404
    assert empezar(c, "fax").status_code == 422


def test_recorrido_completo_entrevista_validar_y_mcp(modo, monkeypatch):
    c = local()
    r = empezar(c)
    assert r.status_code == 200, r.text
    alta = r.json()
    assert alta["client_id"] == C and alta["session_id"] and alta["access_token"]
    # La credencial emitida abre el cliente de la entrevista (y no otro).
    cab = {"Authorization": f"Bearer {alta['access_token']}"}
    assert c.get(f"/api/clients/{C}/profile", headers=cab).status_code == 200
    assert c.get("/api/clients/carmen-68/profile", headers=cab).status_code in (401, 403, 404)

    # Lo que extraería Claude de la conversación en directo (simulado, con cita).
    ev = lambda cita: [{"session_id": alta["session_id"], "turn_id": "t-1", "quote": cita, "t": [0.0, 3.0]}]
    store.aplicar(C, [
        Parche(path="knowledge.equity_funds", value="none", declared="high", source=Fuente.demonstrated,
               confidence=0.85, confidence_basis="rubric:knowledge.equity_funds:v2",
               evidence=ev("Eso no puede pasar, el fondo es del banco.")),
        Parche(path="risk_tolerance.scenario_score", value=1, source=Fuente.demonstrated, confidence=0.85,
               confidence_basis="rubric:risk_tolerance.scenarios:v2", evidence=ev("Lo saco todo.")),
        Parche(path="sustainability.preference", value="some", source=Fuente.declared, confidence=0.9,
               confidence_basis="rubric:certeza.explicita:v2", evidence=ev("Me importa algo, sí.")),
    ], "entrevista corta simulada", "agent:extractor")
    assert store.perfil(C).status == EstadoPerfil.pending_validation

    v = c.post(f"{BASE}/clientes/{C}/validar", headers=asesor())
    assert v.status_code == 200 and v.json()["status"] == "active"

    # Como Claude Code en la demo: MCP_DEMO_TOKEN por cabecera (por defecto incluye carmen-corta).
    monkeypatch.setenv("MCP_DEMO_TOKEN", MCP_TOKEN)
    monkeypatch.delenv("MCP_DEMO_CLIENTS", raising=False)
    peticion = Request({"type": "http", "headers": [(b"authorization", f"Bearer {MCP_TOKEN}".encode())]})
    monkeypatch.setattr(mcp, "get_context", lambda: SimpleNamespace(request_context=SimpleNamespace(request=peticion)))
    res = asyncio.run(mcp.call_tool("get_investment_constraints", {"client_id": C}))
    bloques = res[0] if isinstance(res, tuple) else res
    restr = json.loads(bloques[0].text)
    assert restr["usable"] is True
    assert restr["appropriateness"]["equity_funds"] == Conveniencia.not_appropriate.value

    # Repetir el ensayo: vuelve a empezar desde el fixture, sin borrar el historial.
    version = store.perfil(C).version
    assert empezar(c).status_code == 200
    p = store.perfil(C)
    assert p.status == EstadoPerfil.draft and p.version > version
