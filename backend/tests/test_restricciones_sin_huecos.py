"""Restricciones sin huecos (bloque A, punto 3): nada conveniente nunca abre una búsqueda libre."""

from app.perfil import calculos
from app.perfil.modelos import Fact, Fuente, Perfil


def _restr(conocimientos: dict[str, str], tolerancia: int = 5, plazo: float = 20):
    p = Perfil(client_id="test-restricciones")
    datos = {"financial.liquid_savings_eur": 100000, "financial.fixed_monthly_costs_eur": 1000,
             "financial.debts_eur": 0, "risk_tolerance.scenario_score": tolerancia,
             "objectives.o1.horizon_years": plazo}
    for ruta, v in datos.items():
        p.mifid[ruta] = Fact(value=v, source=Fuente.declared, updated_by="fixture")
    for fam, nivel in conocimientos.items():
        p.mifid[f"knowledge.{fam}"] = Fact(value=nivel, source=Fuente.demonstrated, updated_by="fixture")
    calculos.recalcular(p)
    return calculos.restricciones(p)


def test_nada_conveniente_bloquea_fondos_sin_consulta_abierta():
    r = _restr({"fixed_income_funds": "none", "equity_funds": "none"})
    assert r.funds_query["asset_type"] == []
    assert {"funds", "etfs", "stocks"} <= set(r.blocked_searches)
    assert "portfolios" not in r.blocked_searches  # gestión delegada: solo idoneidad
    assert any("no se buscan fondos" in m for m in r.rationale)


def test_fondos_convenientes_se_listan_y_no_se_bloquean():
    r = _restr({"fixed_income_funds": "medium", "equity_funds": "none"})
    assert r.funds_query["asset_type"] == ["Renta Fija"] and "funds" not in r.blocked_searches


def test_etf_y_acciones_segun_conveniencia_y_perfil():
    r = _restr({"fixed_income_funds": "medium", "etfs": "medium", "stocks": "high"})
    assert "etfs" not in r.blocked_searches and "stocks" not in r.blocked_searches  # MUY_AGRESIVO, SRI 7
    assert any("SRRI" in m for m in r.rationale)
    # Mismo conocimiento, perfil conservador por tolerancia: acciones sueltas fuera.
    r = _restr({"fixed_income_funds": "medium", "etfs": "medium", "stocks": "high"}, tolerancia=1)
    assert "stocks" in r.blocked_searches and "etfs" not in r.blocked_searches


def test_sin_perfil_de_riesgo_no_se_busca_nada():
    r = calculos.restricciones(Perfil(client_id="vacio"))
    assert set(r.blocked_searches) == {"funds", "portfolios", "etfs", "stocks"}
    assert r.funds_query["asset_type"] == [] and "max_risk" not in r.funds_query
