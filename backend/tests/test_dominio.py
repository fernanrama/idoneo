"""Dominio puro (sin base de datos): esquema, cálculos, evaluaciones, restricciones y estados."""

from __future__ import annotations

import pytest

from app.perfil.dominio import calculos, esquema, estados, evaluaciones, restricciones
from app.perfil.dominio import supuestos as S
from app.perfil.dominio.errores import CampoInvalido, TransicionNoPermitida
from app.perfil.dominio.modelos import (
    Alerta,
    CapaPersonal,
    Conveniencia,
    EstadoPerfil,
    Evidencia,
    Fact,
    Flag,
    Fuente,
    Perfil,
    PerfilRiesgo,
    anidar,
)


def perfil_con(**valores) -> Perfil:
    """Perfil en memoria con los valores dados (claves con '__' en lugar de '.')."""
    p = Perfil(client_id="prueba")
    for clave, valor in valores.items():
        p.mifid[clave.replace("__", ".")] = Fact(value=valor, source=Fuente.declared, updated_by="test")
    return p


def perfil_completo(**extra) -> Perfil:
    base = dict(
        disclosures__ai_notice_ack=True, disclosures__purpose_ack=True,
        knowledge__equity_funds="medium", knowledge__fixed_income_funds="medium",
        financial__net_monthly_income_eur=3000, financial__fixed_monthly_costs_eur=1000,
        financial__liquid_savings_eur=50000, financial__debts_eur=0,
        objectives__o1__goal="jubilación", objectives__o1__horizon_years=20,
        risk_tolerance__scenario_score=4, sustainability__preference="none",
    )
    base.update(extra)
    p = perfil_con(**base)
    p.mifid.update(calculos.campos_calculados(p.mifid, p.created_at))
    p.assessments = evaluaciones.evaluar(p)
    return p


# ---------- esquema ----------

def test_rutas_conocidas_y_desconocidas():
    assert esquema.espec("knowledge.equity_funds").tipo == "nivel"
    assert esquema.espec("objectives.o2.horizon_years").tipo == "anios"
    assert esquema.espec("financial.loss_capacity_eur").calculado
    for mala in ("knowledge.criptomonedas", "objectives.x1.goal", "objectives.o1.color", "salud.estado"):
        with pytest.raises(CampoInvalido):
            esquema.espec(mala)


@pytest.mark.parametrize("ruta,entrada,esperado", [
    ("financial.debts_eur", "1500", 1500.0),
    ("financial.debts_eur", 99.999, 100.0),
    ("risk_tolerance.scenario_score", 3.0, 3),
    ("knowledge.etfs", "basic", "basic"),
    ("experience.profession", "  enfermera ", "enfermera"),
    ("sustainability.min_sfdr_article", 9, 9),
    ("disclosures.ai_notice_ack", None, None),
])
def test_normalizar_valores_validos(ruta, entrada, esperado):
    assert esquema.normalizar(ruta, entrada) == esperado


@pytest.mark.parametrize("ruta,entrada", [
    ("financial.debts_eur", -1),
    ("financial.debts_eur", True),
    ("financial.debts_eur", "mucho"),
    ("risk_tolerance.scenario_score", 6),
    ("risk_tolerance.scenario_score", 2.5),
    ("knowledge.etfs", "experto"),
    ("disclosures.ai_notice_ack", "sí"),
    ("sustainability.min_sfdr_article", 7),
    ("objectives.o1.horizon_years", 150),
    ("experience.profession", "   "),
])
def test_normalizar_rechaza_valores_invalidos(ruta, entrada):
    with pytest.raises(CampoInvalido):
        esquema.normalizar(ruta, entrada)


# ---------- cálculos ----------

def test_calculos_deterministas():
    assert calculos.colchon_emergencia(900) == 5400
    assert calculos.capacidad_perdida(80000, 5400, 0) == 74600
    assert calculos.capacidad_perdida(1000, 5400, 0) == 0  # nunca negativa
    assert calculos.meses_colchon("variable") == S.MESES_COLCHON["variable"]
    assert calculos.meses_colchon(None) == S.MESES_COLCHON_DEFECTO
    assert calculos.confianza_por_rubrica(2, 3) == 0.67
    with pytest.raises(ValueError):
        calculos.confianza_por_rubrica(4, 3)


def test_campos_calculados_solo_con_entradas_completas():
    p = perfil_con(financial__fixed_monthly_costs_eur=1000)
    calc = calculos.campos_calculados(p.mifid, p.created_at)
    assert set(calc) == {"financial.emergency_fund_months"}  # sin ahorro ni deudas no hay capacidad

    p = perfil_con(financial__fixed_monthly_costs_eur=1000, financial__liquid_savings_eur=20000,
                   financial__debts_eur=2000, financial__income_stability="variable")
    calc = calculos.campos_calculados(p.mifid, p.created_at)
    meses = S.MESES_COLCHON["variable"]
    assert calc["financial.emergency_fund_months"].value == meses
    assert calc["financial.loss_capacity_eur"].value == max(0, 20000 - meses * 1000 - 2000)
    assert all(d.source == Fuente.calculated and d.updated_by.startswith("fn:") for d in calc.values())


# ---------- idoneidad ----------

def test_manda_el_tope_mas_restrictivo():
    p = perfil_completo(risk_tolerance__scenario_score=5, objectives__o1__horizon_years=3)
    ido = p.assessments.suitability
    assert ido.complete
    assert ido.risk_profile == evaluaciones.tope_por_plazo(3)
    assert ido.max_sri == S.SRI_MAX_POR_PERFIL[ido.risk_profile]
    assert "objectives.o1.horizon_years" in ido.rationale_ids


def test_faltan_datos_obligatorios():
    p = perfil_completo()
    del p.mifid["sustainability.preference"]
    ido = evaluaciones.idoneidad(p)
    assert not ido.complete and ido.missing == ["sustainability.preference"]


def test_confianza_baja_cuenta_como_dato_pendiente():
    p = perfil_completo()
    p.mifid["knowledge.equity_funds"].flags.append(Flag.low_confidence)
    ido = evaluaciones.idoneidad(p)
    assert not ido.complete and "knowledge.equity_funds" in ido.missing


def test_sin_datos_de_riesgo_no_hay_perfil():
    ido = evaluaciones.idoneidad(perfil_con(disclosures__ai_notice_ack=True))
    assert ido.risk_profile is None and ido.max_sri is None and not ido.complete


def test_capacidad_de_perdida_limita_el_perfil():
    p = perfil_completo(objectives__o1__amount_eur=200000)  # capacidad 44.000 frente a 200.000
    assert evaluaciones.tope_por_capacidad(44000, 200000) == PerfilRiesgo.DINAMICO
    assert p.assessments.suitability.risk_profile == PerfilRiesgo.DINAMICO


def test_objetivo_principal_por_prioridad():
    p = perfil_con(objectives__o1__goal="a", objectives__o1__priority=2,
                   objectives__o2__goal="b", objectives__o2__priority=1)
    assert evaluaciones.objetivo_principal(p) == "o2"
    p = perfil_con(objectives__o1__goal="a", objectives__o2__goal="b", objectives__o2__priority=0)
    assert evaluaciones.objetivo_principal(p) == "o2"  # prioridad 0 cuenta, no es "sin prioridad"


# ---------- conveniencia ----------

def test_conveniencia_por_conocimiento_y_experiencia():
    p = perfil_con(knowledge__equity_funds="basic", knowledge__etfs="basic", knowledge__stocks="high",
                   experience__by_family__etfs__operations_last_3y=S.OPERACIONES_COMPENSAN_UN_NIVEL)
    assert evaluaciones.conveniencia_familia(p, "equity_funds") == Conveniencia.not_appropriate
    assert evaluaciones.conveniencia_familia(p, "etfs") == Conveniencia.appropriate  # la experiencia compensa
    assert evaluaciones.conveniencia_familia(p, "stocks") == Conveniencia.appropriate
    assert evaluaciones.conveniencia_familia(p, "complex_products") == Conveniencia.unknown


# ---------- restricciones ----------

def test_restricciones_en_formato_myinvestor():
    p = perfil_completo(objectives__o1__horizon_years=1.5, objectives__o1__amount_eur=10000,
                        sustainability__preference="strong", sustainability__min_sfdr_article=9,
                        knowledge__deposits_money_market="basic")
    p.status = EstadoPerfil.active
    capa = CapaPersonal(client_id="prueba", consent_given=True, data={"exclusions": ["tabaco"]})
    r = restricciones.calcular(p, capa)
    assert r.usable and r.max_risk_indicator == r.max_sri == r.funds_query.max_risk
    assert r.funds_query.esg_only and r.funds_query.currency == S.DIVISA_POR_DEFECTO
    # Mixtos sin dato de conocimiento -> "unknown" -> no se incluyen.
    assert set(r.funds_query.asset_type) == {"Monetario", "Renta Fija", "Renta Variable"}
    filtros = {f.field: f for f in r.post_filters}
    assert filtros["redemption_lag_days"].value == S.DIAS_REEMBOLSO_MAX["high"]  # plazo < 2 años
    assert filtros["sustainability_article"].value == 9
    assert filtros["top_sectors"].value == ["tabaco"]
    assert filtros["min_initial"].value == 10000


def test_restricciones_no_usables_sin_validar_ni_consentimiento():
    p = perfil_completo()
    r = restricciones.calcular(p, CapaPersonal(client_id="prueba", consent_given=False))
    assert not r.usable and not r.eligible
    assert all(f.field != "top_sectors" for f in r.post_filters)


# ---------- estados ----------

def test_transiciones():
    E = EstadoPerfil
    estados.comprobar(E.draft, E.pending_validation)
    estados.comprobar(E.pending_validation, E.active)
    estados.comprobar(E.active, E.review_due)
    estados.comprobar(E.review_due, E.draft)
    for de, a in [(E.draft, E.active), (E.active, E.draft), (E.review_due, E.active)]:
        with pytest.raises(TransicionNoPermitida):
            estados.comprobar(de, a)


def test_estado_tras_cambio():
    p = perfil_completo()
    assert estados.tras_cambio(p, por_asesor=False) == EstadoPerfil.pending_validation
    p.alerts.append(Alerta(id="x", type="needs_advisor", field=None, message="revisar"))
    assert estados.tras_cambio(p, por_asesor=False) == EstadoPerfil.draft
    p.status = EstadoPerfil.active
    assert estados.tras_cambio(p, por_asesor=False) == EstadoPerfil.review_due
    assert estados.tras_cambio(p, por_asesor=True) == EstadoPerfil.active


# ---------- modelos ----------

def test_evidencia_acepta_formato_v0_y_valida_tiempos():
    e = Evidencia.model_validate({"session_id": "s", "t_start": 1.0, "t_end": 2.5, "quote": "hola"})
    assert e.t == (1.0, 2.5)
    with pytest.raises(ValueError):
        Evidencia(session_id="s", t=(3.0, 1.0), quote="hola")


def test_anidar_produce_forma_del_contrato():
    d = anidar({"knowledge.etfs": 1, "objectives.o2.goal": "b", "objectives.o1.goal": "a",
                "experience.by_family.etfs.years": 3})
    assert d["knowledge"] == {"etfs": 1}
    assert d["objectives"] == [{"id": "o1", "goal": "a"}, {"id": "o2", "goal": "b"}]
    assert d["experience"]["by_family"]["etfs"]["years"] == 3


def test_capa_personal_exige_consentimiento_y_bloques_conocidos():
    with pytest.raises(ValueError):
        CapaPersonal(client_id="c", consent_given=False, data={"exclusions": ["armas"]})
    with pytest.raises(ValueError):
        CapaPersonal(client_id="c", consent_given=True, data={"salud": "x"})
