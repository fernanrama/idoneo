"""Vista de la entidad en la web (`/api/entidad/...`): solo con ADMIN_TOKEN, para cualquier cliente.

DATOS SIMULADOS: fixture carmen-68. Sin Claude: las respuestas de la microentrevista se simulan con
`store.aplicar`, como en test_ciclo_revision.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.perfil import store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
TOKEN = "admin-de-prueba-entidad-web-0123456789"


@pytest.fixture
def web(carmen, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
    return TestClient(app)


def admin(**extra):
    return {"X-Admin-Token": TOKEN, **extra}


def cambiar_ahorro(valor: int):
    return store.aplicar(C, [Parche(path="financial.liquid_savings_eur", value=valor, source="declared",
                                    evidence=[Evidencia(session_id="s-micro", turn_id="t-001", t=(1.0, 2.0),
                                                        quote="DATOS SIMULADOS")])],
                         "extractor · s-micro", "agent:extractor")


def test_sin_token_o_con_token_malo_no_hay_acceso(web):
    assert web.get(f"/api/entidad/clientes/{C}").status_code in (401, 403)
    assert web.get(f"/api/entidad/clientes/{C}", headers={"X-Admin-Token": "otro"}).status_code in (401, 403)
    assert web.post(f"/api/entidad/clientes/{C}/validar", json={}).status_code in (401, 403)
    assert store.perfil(C).status == EstadoPerfil.pending_validation


def test_sin_admin_token_configurado_responde_503(carmen, monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    r = TestClient(app).get(f"/api/entidad/clientes/{C}", headers={"X-Admin-Token": "lo-que-sea"})
    assert r.status_code == 503


def test_expediente_sin_capa_personal(web):
    r = web.get(f"/api/entidad/clientes/{C}", headers=admin())
    assert r.status_code == 200
    d = r.json()
    assert d["profile"]["client_id"] == C and d["profile"]["personal"] == {}
    assert {"constraints", "versions", "review", "changes"} <= d.keys()


def test_ciclo_completo_validar_microentrevista_y_volver_a_validar(web):
    r = web.post(f"/api/entidad/clientes/{C}/validar", headers=admin(), json={})
    assert r.status_code == 200 and r.json()["status"] == "active"
    assert store.perfil(C).author == "advisor:asesor-web"
    p = cambiar_ahorro(10000)
    assert p.status == EstadoPerfil.review_due
    assert web.post(f"/api/entidad/clientes/{C}/validar", headers=admin(),
                    json={"expected_version": p.version - 1}).status_code == 409
    assert store.perfil(C).status == EstadoPerfil.review_due  # el 409 no escribe
    r = web.post(f"/api/entidad/clientes/{C}/validar", headers=admin(), json={"expected_version": p.version})
    assert r.status_code == 200 and r.json()["status"] == "active"


def test_no_admite_correcciones_ni_otro_asesor(web):
    r = web.post(f"/api/entidad/clientes/{C}/validar", headers=admin(), json={"advisor_id": "intruso"})
    assert r.status_code == 422
    assert store.perfil(C).status == EstadoPerfil.pending_validation


def test_cliente_inexistente_404(web):
    assert web.get("/api/entidad/clientes/no-existe", headers=admin()).status_code == 404
