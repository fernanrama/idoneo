"""Cambios de la integración en la API (main.py): códigos de error, token de administración,
endpoints de demo, canal de la sesión y tolerancia a parches inválidos del extractor."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.perfil import store
from app.perfil.modelos import Evidencia, Parche, Turno

C = "/api/clients/carmen-68"
EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="q")]


@pytest.fixture
def api():
    store.reiniciar()
    store.cargar_fixture("carmen-68")
    return TestClient(app)


def test_sin_admin_token_el_front_funciona_igual(api):
    assert api.post(f"{C}/validate", json={"advisor_id": "asesor-07"}).status_code == 200
    assert api.post("/api/demo/reset").status_code == 200


def test_con_admin_token_las_escrituras_de_la_entidad_lo_exigen(api, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "secreto-de-prueba")
    assert api.post(f"{C}/validate", json={"advisor_id": "a"}).status_code == 401
    assert api.post(f"{C}/validate", json={"advisor_id": "a"}, headers={"X-Admin-Token": "otro"}).status_code == 401
    assert api.post("/api/demo/reset").status_code == 401
    r = api.post(f"{C}/validate", json={"advisor_id": "a"}, headers={"X-Admin-Token": "secreto-de-prueba"})
    assert r.status_code == 200 and r.json()["status"] == "active"
    assert api.get(f"{C}/constraints").status_code == 200  # la lectura no lo pide


def test_endpoints_de_demo_desactivables(api, monkeypatch):
    monkeypatch.setenv("DEMO_ENDPOINTS", "0")
    assert api.post("/api/demo/reset").status_code == 404


def test_entrada_invalida_da_422_y_no_500(api):
    r = api.post(f"{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "financial.debts_eur", "value": "muchísimo", "source": "advisor"}]})
    assert r.status_code == 422
    r = api.post(f"{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "salud.diagnostico", "value": "x", "source": "advisor"}]})
    assert r.status_code == 422
    assert api.post("/api/sessions", json={"client_id": "../../fuera"}).status_code == 422
    assert api.post("/api/sessions", json={"channel": "paloma"}).status_code == 422


def test_revalidar_un_activo_da_409(api):
    assert api.post(f"{C}/validate", json={"advisor_id": "a"}).status_code == 200
    assert api.post(f"{C}/validate", json={"advisor_id": "b"}).status_code == 409


def test_el_canal_llega_a_la_sesion(api):
    s = api.post("/api/sessions", json={"channel": "text"}).json()
    assert s["channel"] == "text" and api.get(f"/api/sessions/{s['session_id']}").json()["channel"] == "text"


def test_un_parche_invalido_del_extractor_no_tira_el_lote(api, monkeypatch):
    s = api.post("/api/sessions", json={"client_id": "carmen-68"}).json()

    async def extraer(_turnos, _perfil, _sid):
        return [Parche(path="experience.education", value="FP", source="declared", evidence=EV),
                Parche(path="salud.diagnostico", value="x", source="declared", evidence=EV),
                Parche(path="financial.debts_eur", value=1, source="declared")]  # sin evidencia

    monkeypatch.setattr(main.extractor, "extraer", extraer)
    store.anadir_turno(s["session_id"], Turno(speaker="client", text="Estudié FP", t_start=0, t_end=1))
    asyncio.run(main._procesar_turno(s["session_id"]))
    p = store.perfil("carmen-68")
    assert p.mifid["experience.education"].value == "FP" and "salud.diagnostico" not in p.mifid
    assert p.mifid["financial.debts_eur"].value == 0  # el parche sin evidencia se descartó


def test_un_error_en_segundo_plano_queda_registrado(api, monkeypatch, caplog):
    async def roto(*_):
        raise RuntimeError("fallo del modelo")

    monkeypatch.setattr(main.extractor, "extraer", roto)
    s = api.post("/api/sessions", json={"client_id": "carmen-68"}).json()
    asyncio.run(main._procesar_turno(s["session_id"]))  # no revienta
    assert "Error procesando el turno" in caplog.text


def test_el_mcp_sigue_montado_y_la_api_tiene_prioridad(api):
    assert api.get("/api/health").json() == {"status": "ok"}
    assert any(getattr(r, "path", "") == "" or getattr(r, "path", None) == "/" for r in app.routes[-1:])
