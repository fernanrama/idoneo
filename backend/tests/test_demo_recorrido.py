"""Recorrido único: la demo guiada crea una copia propia de Carmen y la entidad la ve en su bandeja.

DATOS SIMULADOS: fixture carmen-68. Sin Claude ni ElevenLabs.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import limites
from app.main import app
from app.perfil import store
from app.perfil.modelos import EstadoPerfil

TOKEN = "admin-de-prueba-recorrido-0123456789"


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
    monkeypatch.delenv("LIMITE_DEMOS_DIA", raising=False)
    limites.reiniciar()
    yield TestClient(app)
    limites.reiniciar()


def bearer(alta):
    return {"Authorization": f"Bearer {alta['access_token']}"}


def test_cada_demo_es_un_cliente_nuevo_con_el_perfil_de_carmen(web):
    a = web.post("/api/demo/sessions").json()
    b = web.post("/api/demo/sessions").json()
    assert a["client_id"] != b["client_id"] and a["client_id"].startswith("carmen-")
    assert a["demo"] is True and a["session_id"].startswith("s-")
    p = web.get(f"/api/clients/{a['client_id']}/profile", headers=bearer(a)).json()
    fijo = web.get("/api/demo/profile").json()
    valores = lambda d: {r: f["value"] for r, f in d["mifid"].items()}  # noqa: E731
    assert valores(p) == valores(fijo)
    assert p["status"] == "pending_validation" and p["assessments"]["suitability"]["complete"]
    # Las evidencias siguen apuntando a la entrevista simulada (s-demo), que suena con los audios grabados.
    assert any(e["session_id"] == "s-demo" for f in p["mifid"].values() for e in f["evidence"])


def test_la_copia_sigue_el_mismo_recorrido_que_un_cliente(web):
    a = web.post("/api/demo/sessions").json()
    cid, h = a["client_id"], bearer(a)
    # La credencial es solo de su copia: no abre la Carmen fija ni otra copia.
    otra = web.post("/api/demo/sessions").json()
    assert web.get(f"/api/clients/{otra['client_id']}/profile", headers=h).status_code in (401, 403, 404)
    # Memoria personal, igual que tras una entrevista real.
    assert web.get(f"/api/sessions/{a['session_id']}/memory", headers=h).status_code == 200
    # La entidad la ve en su bandeja y la valida.
    bandeja = web.get("/api/entidad/clientes", headers={"X-Admin-Token": TOKEN}).json()["clients"]
    assert bandeja[0]["client_id"] == otra["client_id"] and cid in {c["client_id"] for c in bandeja}
    r = web.post(f"/api/entidad/clientes/{cid}/validar", headers={"X-Admin-Token": TOKEN}, json={})
    assert r.status_code == 200 and store.perfil(cid).status == EstadoPerfil.active
    # Ya validado, «ha cambiado algo» funciona como para cualquier cliente.
    r = web.post(f"/api/clients/{cid}/review/preview", headers=h, json={"reasons": ["income_change"]})
    assert r.status_code == 200 and r.json()["questions"]


def test_bandeja_solo_con_token_de_entidad(web):
    assert web.get("/api/entidad/clientes").status_code in (401, 403)
    assert web.get("/api/entidad/clientes", headers={"X-Admin-Token": "otro"}).status_code in (401, 403)


def test_la_bandeja_ordena_por_ultima_version(web):
    a = web.post("/api/demo/sessions").json()
    b = web.post("/api/demo/sessions").json()
    web.post(f"/api/entidad/clientes/{a['client_id']}/validar", headers={"X-Admin-Token": TOKEN}, json={})
    filas = store.clientes(10)
    assert [f["client_id"] for f in filas[:2]] == [a["client_id"], b["client_id"]]
    assert filas[0]["status"] == EstadoPerfil.active and filas[0]["version"] == 2


def test_demo_con_tope_diario_y_apagable(web, monkeypatch):
    monkeypatch.setenv("LIMITE_DEMOS_DIA", "1")
    assert web.post("/api/demo/sessions").status_code == 200
    assert web.post("/api/demo/sessions").status_code == 429
    monkeypatch.setenv("DEMO_ENDPOINTS", "0")
    assert web.post("/api/demo/sessions").status_code == 404


def test_copiar_fixture_no_pisa_un_cliente_existente(carmen):
    with pytest.raises(store.Conflicto):
        store.copiar_fixture("carmen-68", "carmen-68")
