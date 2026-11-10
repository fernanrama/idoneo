"""Cambios de la integración en la API (main.py): códigos de error, token de administración,
endpoints de demo, canal de la sesión y tolerancia a parches inválidos del extractor."""

from __future__ import annotations


import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.soporte_acceso import cliente_autorizado
from app.perfil import store
from app.perfil.modelos import Evidencia

C = "/api/clients/carmen-68"
EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="q")]


@pytest.fixture
def api():
    store.reiniciar()
    store.cargar_fixture("carmen-68")
    return cliente_autorizado(servicio=False)


def test_sin_admin_token_las_escrituras_de_entidad_fallan_cerradas(api, monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN")
    assert api.post(f"{C}/validate", json={"advisor_id": "asesor-07"}).status_code == 503
    assert api.post("/api/demo/reset").status_code == 503
    assert api.get(f"{C}/profile").status_code == 200


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
    assert api.post("/api/demo/reset", headers={"X-Admin-Token": "servicio-sintetico-de-pruebas"}).status_code == 404


def test_entrada_invalida_da_422_y_no_500(api):
    api.headers["X-Admin-Token"] = os.environ["ADMIN_TOKEN"]
    r = api.post(f"{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "financial.debts_eur", "value": "muchísimo", "source": "advisor"}]})
    assert r.status_code == 422
    r = api.post(f"{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "salud.diagnostico", "value": "x", "source": "advisor"}]})
    assert r.status_code == 422
    assert api.post("/api/sessions", json={"client_id": "../../fuera"}).status_code == 422
    assert api.post("/api/sessions", json={"channel": "paloma"}).status_code == 422


def test_revalidar_un_activo_da_409(api):
    api.headers["X-Admin-Token"] = os.environ["ADMIN_TOKEN"]
    assert api.post(f"{C}/validate", json={"advisor_id": "a"}).status_code == 200
    assert api.post(f"{C}/validate", json={"advisor_id": "b"}).status_code == 409


def test_el_canal_llega_a_la_sesion(api):
    s = api.post("/api/sessions", json={"channel": "text"}).json()
    assert s["channel"] == "text" and api.get(f"/api/sessions/{s['session_id']}", headers={"Authorization": f"Bearer {s['access_token']}"}).json()["channel"] == "text"




def test_el_mcp_sigue_montado_y_la_api_tiene_prioridad(api):
    assert api.get("/api/health").json() == {"status": "ok"}
    assert any(getattr(r, "path", "") == "" or getattr(r, "path", None) == "/" for r in app.routes[-1:])
