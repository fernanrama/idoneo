import os

os.environ["DATA_PERSIST"] = "0"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.perfil import calculos, store  # noqa: E402


def cliente():
    store.reiniciar()
    store.cargar_fixture("carmen-68")
    return TestClient(app)


def test_calculos_deterministas():
    assert calculos.colchon_emergencia(900) == 5400
    assert calculos.capacidad_perdida(80000, 5400, 0) == 74600
    assert calculos.capacidad_perdida(1000, 5400, 0) == 0


def test_carmen_borrador_no_es_apta():
    c = cliente()
    r = c.get("/api/clients/carmen-68/constraints").json()
    assert r["eligible"] is False
    assert r["missing_fields"] == []
    # tolerancia low -> 3, plazo 10 -> 7, conocimiento none -> 2
    assert r["max_risk_indicator"] == 2
    assert r["loss_capacity_eur"] == 74600


def test_validar_activa_y_versiona():
    c = cliente()
    p = c.post("/api/clients/carmen-68/profile/validate", json={"advisor_id": "asesor-07"}).json()
    assert p["status"] == "active" and p["version"] == 2
    assert c.get("/api/clients/carmen-68/constraints").json()["eligible"] is True
    assert len(c.get("/api/clients/carmen-68/profile/versions").json()) == 2


def test_evidencia_y_contexto():
    c = cliente()
    e = c.get("/api/clients/carmen-68/evidence/knowledge.equity_risk").json()
    assert "banco" in e["evidence"][0]["quote"]
    assert "SRI 2" in c.get("/api/clients/carmen-68/context").json()["text"]


def test_sesion_y_turnos():
    c = cliente()
    s = c.post("/api/sessions", json={}).json()
    r = c.post(f"/api/sessions/{s['session_id']}/turns",
               json={"speaker": "client", "text": "Hola", "t_start": 0, "t_end": 1})
    assert r.status_code == 202
    assert c.get(f"/api/clients/{s['client_id']}/profile").json()["status"] == "draft"
