"""Importe a invertir frente al colchón (bloque A, punto 4).

Si quiere invertir más de lo que puede perder sin tocar 6 meses de gastos ni sus deudas, el perfil por
capacidad pasa a CONSERVADOR y el verificador lo manda al asesor.
"""

from app.agentes import verificador
from app.perfil import calculos
from app.perfil.modelos import Fact, Flag, Fuente, Perfil, PerfilRiesgo


def _perfil(importe: float | None) -> Perfil:
    # Ahorro 30.000, gastos 1.000 → colchón 6.000; deudas 4.000 → capacidad 20.000 (2/3 → AGRESIVO).
    datos = {"financial.liquid_savings_eur": 30000, "financial.fixed_monthly_costs_eur": 1000,
             "financial.debts_eur": 4000, "risk_tolerance.scenario_score": 5, "objectives.o1.horizon_years": 20}
    if importe is not None:
        datos["objectives.o1.amount_eur"] = importe
    p = Perfil(client_id="test-importe")
    for ruta, v in datos.items():
        p.mifid[ruta] = Fact(value=v, source=Fuente.declared, updated_by="fixture")
    calculos.recalcular(p)
    return p


def test_importe_dentro_del_margen_no_cambia_nada():
    for importe in (None, 10000, 20000):
        p = _perfil(importe)
        assert p.assessments.suitability.risk_profile == PerfilRiesgo.AGRESIVO
        assert not [a for a in verificador.reglas(p) if a.path == "objectives.o1.amount_eur"]


def test_importe_que_toca_el_colchon_es_conservador_y_va_al_asesor():
    p = _perfil(25000)
    s = p.assessments.suitability
    assert s.risk_profile == PerfilRiesgo.CONSERVADOR and s.max_sri == 3
    assert s.rationale_ids == ["objectives.o1.amount_eur"]
    assert any("25,000 €" in m and "20,000 €" in m for m in s.rationale)
    alertas = [a for a in verificador.reglas(p) if a.path == "objectives.o1.amount_eur"]
    assert [a.flag for a in alertas] == [Flag.needs_advisor]
    assert "20.000 €" in alertas[0].message
