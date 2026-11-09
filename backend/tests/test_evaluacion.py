"""La evaluación del extractor: casos bien formados y puntuación correcta (sin llamar a Claude)."""

import pytest

from app.agentes import evaluacion
from app.perfil.modelos import Fact, Flag, Fuente

CASOS = evaluacion.casos()


def fact(valor, fuente=Fuente.declared, flags=()):
    return Fact(value=valor, source=fuente, flags=list(flags), updated_by="agent:extractor")


def test_hay_casos_de_evaluacion():
    assert len(CASOS) >= 5


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c.nombre)
def test_cada_caso_esta_bien_formado(caso):
    assert evaluacion.comprobar_caso(caso) == []


def caso(**kw):
    base = dict(nombre="x", que_prueba="", turnos=[], esperado={}, prohibido=[], prohibido_valores={})
    return evaluacion.Caso(**{**base, **kw})


def test_puntuacion_distingue_acierto_error_falta_y_prohibido():
    c = caso(
        esperado={"financial.net_monthly_income_eur": 2500, "financial.debts_eur": 0,
                  "objectives.o1.goal": {"presente": True}, "financial.liquid_savings_eur": 1000},
        prohibido=["financial.other_assets_eur"],
        prohibido_valores={"knowledge.stocks": ["high"]},
    )
    mifid = {
        "financial.net_monthly_income_eur": fact(2500.0),
        "financial.debts_eur": fact(10.0),
        "objectives.o1.goal": fact("jubilación"),
        "financial.other_assets_eur": fact(5.0),
        "knowledge.stocks": fact("high"),
    }
    r = evaluacion.puntuar(c, mifid)
    estados = {li.ruta: li.estado for li in r.lineas}
    assert estados == {
        "financial.net_monthly_income_eur": "ok", "financial.debts_eur": "mal", "objectives.o1.goal": "ok",
        "financial.liquid_savings_eur": "falta", "financial.other_assets_eur": "prohibido", "knowledge.stocks": "prohibido",
    }
    s = evaluacion.resumen([r])
    assert (s["aciertos"], s["esperados"], s["prohibidos"]) == (2, 4, 2)
    assert s["precision"] == pytest.approx(2 / 5)


def test_puntuacion_exige_fuente_flags_y_acepta_alternativas():
    c = caso(esperado={
        "knowledge.equity_funds": {"uno_de": ["medium", "high"], "fuente": "demonstrated"},
        "financial.net_monthly_income_eur": {"valor": 500000, "flags": ["needs_advisor"]},
    })
    bien = {"knowledge.equity_funds": fact("high", Fuente.demonstrated),
            "financial.net_monthly_income_eur": fact(500000, flags=[Flag.needs_advisor, Flag.low_confidence])}
    assert {li.estado for li in evaluacion.puntuar(c, bien).lineas} == {"ok"}
    mal = {"knowledge.equity_funds": fact("high", Fuente.declared),
           "financial.net_monthly_income_eur": fact(500000)}
    assert {li.estado for li in evaluacion.puntuar(c, mal).lineas} == {"mal"}


def test_un_caso_con_ruta_inventada_se_detecta():
    assert evaluacion.comprobar_caso(caso(esperado={"financial.inventado": 1})) != []
    assert evaluacion.comprobar_caso(caso(esperado={"financial.emergency_fund_months": 3})) != []
