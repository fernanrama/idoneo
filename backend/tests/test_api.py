import os

os.environ["DATA_PERSIST"] = "0"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.perfil import calculos, store  # noqa: E402
from app.perfil.modelos import Parche  # noqa: E402

C = "/api/clients/carmen-68"


def cliente():
    store.reiniciar()
    store.cargar_fixture("carmen-68")
    return TestClient(app)


def test_calculos_deterministas():
    assert calculos.meses_colchon(80000, 900) == 88.9
    assert calculos.capacidad_perdida(80000, 900, 0) == 74600
    assert calculos.capacidad_perdida(1000, 900, 0) == 0


def test_carmen_completa_queda_pendiente_de_validar():
    c = cliente()
    p = c.get(f"{C}/profile").json()
    assert p["status"] == "pending_validation"
    s = p["assessments"]["suitability"]
    # tolerancia 1/5 → CONSERVADOR manda sobre plazo (AGRESIVO) y capacidad (MUY_AGRESIVO)
    assert s["complete"] and s["risk_profile"] == "CONSERVADOR" and s["max_sri"] == 3
    assert s["rationale_ids"] == ["risk_tolerance.scenario_score"]
    assert p["mifid"]["financial.loss_capacity_eur"]["value"] == 74600


def test_conveniencia_por_familia():
    conv = cliente().get(f"{C}/profile").json()["assessments"]["appropriateness"]
    assert conv["equity_funds"] == "not_appropriate"  # declaró alto, demostró nulo
    assert conv["fixed_income_funds"] == "appropriate"
    assert conv["deposits_money_market"] == "appropriate"
    assert conv["etfs"] == "not_assessed"


def test_restricciones_en_parametros_de_myinvestor():
    c = cliente()
    r = c.get(f"{C}/constraints").json()
    assert r["usable"] is False  # aún no validado
    assert r["funds_query"]["max_risk"] == 3
    assert set(r["funds_query"]["asset_type"]) == {"Monetario", "Renta Fija"}
    assert r["portfolios_query"] == {"profile": "CONSERVADOR", "risk_max": 1}
    assert "knowledge.equity_funds" in r["evidence_refs"]


def test_validar_activa_cierra_alertas_y_versiona():
    c = cliente()
    p = c.post(f"{C}/validate", json={"advisor_id": "asesor-07"}).json()
    assert p["status"] == "active" and p["version"] == 2
    assert all(a["status"] == "resolved" for a in p["alerts"]) and p["review"]["open_flags"] == 0
    assert c.get(f"{C}/constraints").json()["usable"] is True
    assert [v["reason"] for v in c.get(f"{C}/versions").json()][-1] == "validated"


def test_cambio_de_agente_sobre_activo_pide_revision_y_consumidor_ve_el_activo():
    c = cliente()
    c.post(f"{C}/validate", json={"advisor_id": "asesor-07"})
    store.aplicar("carmen-68", [Parche(path="objectives.o1.horizon_years", value=1, source="declared")],
                  "life_event:herencia", "agent:extractor")
    assert c.get(f"{C}/profile").json()["status"] == "review_due"
    r = c.get(f"{C}/constraints").json()
    assert r["usable"] is True and r["profile_version"] == 2  # sigue sirviendo el último activo


def test_no_se_puede_escribir_un_campo_calculado():
    c = cliente()
    r = c.post(f"{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "financial.loss_capacity_eur", "value": 1, "source": "advisor"}]})
    assert r.status_code == 409


def test_validar_incompleto_da_409():
    c = cliente()
    s = c.post("/api/sessions", json={}).json()
    assert c.post(f"/api/clients/{s['client_id']}/validate", json={"advisor_id": "a"}).status_code == 409


def test_evidencia_y_contexto():
    c = cliente()
    e = c.get(f"{C}/evidence/knowledge.equity_funds").json()
    assert "banco" in e["evidence"][0]["quote"] and e["evidence"][0]["t"] == [57.0, 61.0]
    assert "SRI máximo 3" in c.get(f"{C}/context").json()["text"]


def test_sesion_y_turnos_con_id():
    c = cliente()
    s = c.post("/api/sessions", json={}).json()
    r = c.post(f"/api/sessions/{s['session_id']}/turns",
               json={"speaker": "client", "text": "Hola", "t_start": 0, "t_end": 1})
    assert r.status_code == 202 and r.json()["turn_id"] == "t-001"
    assert c.get(f"/api/clients/{s['client_id']}/profile").json()["status"] == "draft"


def test_voz_sin_clave_responde_503(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert cliente().get("/api/voice/signed-url").status_code == 503
