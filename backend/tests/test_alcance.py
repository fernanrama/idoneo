"""Alcance de una revisión (app/perfil/alcance.py). Puro: sin almacén, sin red, sin modelo.

Usa el fixture ficticio carmen-68 (DATOS SIMULADOS) leído y recalculado en memoria.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.perfil import alcance, calculos
from app.perfil.alcance import (
    DEPENDENCIAS,
    MAX_PREGUNTAS,
    SEMILLAS,
    VARIABLES,
    Motivo,
    Peticion,
    TipoPregunta,
    es_material,
    planificar,
    plazo_restante,
    vencimientos,
)
from app.perfil.modelos import CALCULADOS, CAMPOS, Alerta, Evidencia, Fact, Flag, Fuente, Perfil
from app.perfil.validacion import DatoInvalido

HOY = date(2026, 11, 11)
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "carmen-68.json"
AHORRO, GASTOS = "financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur"
PLAZO, LIQUIDEZ = "objectives.o1.horizon_years", "objectives.o1.liquidity_need"
C, R, K = TipoPregunta.confirmar, TipoPregunta.repreguntar, TipoPregunta.comprobar


def _hace(dias: float) -> datetime:
    return datetime(HOY.year, HOY.month, HOY.day, 12, tzinfo=timezone.utc) - timedelta(days=dias)


@pytest.fixture
def carmen() -> Perfil:
    datos = json.loads(FIXTURE.read_text("utf-8"))
    datos.pop("personal", None)
    p = Perfil.model_validate(datos)
    for ruta, f in p.mifid.items():
        p.mifid[ruta] = f.model_copy(update={"updated_at": _hace(0)})
    calculos.recalcular(p)
    return p


def cambiar(p: Perfil, ruta: str, valor=None, **otros) -> Perfil:
    n = p.model_copy(deep=True)
    previo = n.mifid.get(ruta)
    campos = {"value": valor, **otros} if valor is not None else otros
    n.mifid[ruta] = (previo.model_copy(update=campos) if previo
                     else Fact(source=Fuente.declared, updated_by="advisor:test", **campos))
    calculos.recalcular(n)
    return n


def resumen(a: alcance.Alcance) -> list[tuple[str, TipoPregunta]]:
    return [(q.path, q.tipo) for q in a.preguntas]


ANUAL = Peticion(motivo=Motivo.next_review_due, rutas=alcance._REVISION_ANUAL)


# ---------- catálogo y dependencias ----------

def test_cada_motivo_tiene_una_sola_definicion():
    assert set(SEMILLAS) | set(VARIABLES) == set(Motivo)
    assert not set(SEMILLAS) & set(VARIABLES)


@pytest.mark.parametrize("motivo", list(SEMILLAS))
def test_las_semillas_son_rutas_revisables(motivo):
    repreguntar, confirmar = SEMILLAS[motivo]
    for ruta in repreguntar + confirmar:
        alcance._comprobar_ruta(ruta)  # no lanza


def test_las_dependencias_son_rutas_revisables():
    for ruta, deps in DEPENDENCIAS.items():
        for r in [ruta, *deps]:
            alcance._comprobar_ruta(r)


def test_las_dependencias_cubren_las_entradas_de_cada_calculado(carmen):
    """Vigila que la tabla no se desincronice de calculos.recalcular."""
    for calc in CALCULADOS:
        entradas = carmen.mifid[calc].inputs
        assert entradas, calc
        for e in entradas:
            assert set(entradas) - {e} <= set(DEPENDENCIAS[e]), (calc, e)


# ---------- planificar ----------

def test_carmen_cambio_de_liquidez_son_tres_preguntas(carmen):
    a = planificar(carmen, [Peticion(motivo=Motivo.liquidity_change)])
    assert resumen(a) == [(LIQUIDEZ, R), (AHORRO, C), (PLAZO, C)]
    assert a.preguntas[1].valor_vigente == 80000
    assert a.aplazadas == [] and not a.reevaluacion_completa and a.razones == []


def test_conocimiento_no_evaluado_se_comprueba_y_arrastra_la_experiencia(carmen):
    a = planificar(carmen, [Peticion(motivo=Motivo.knowledge_not_assessed, rutas=["knowledge.etfs"])])
    # La experiencia es una dependencia, pero falta en el perfil: no se puede confirmar, se pregunta.
    assert resumen(a) == [("knowledge.etfs", K), ("experience.etfs.operations_last_3y", R)]


def test_no_lo_conozco_no_se_comprueba(carmen):
    p = cambiar(carmen, "knowledge.etfs", "none")
    a = planificar(p, [Peticion(motivo=Motivo.advisor_request, rutas=["knowledge.etfs"])])
    assert a.preguntas[0].path == "knowledge.etfs" and a.preguntas[0].tipo == R


def test_un_dato_dudoso_no_se_confirma(carmen):
    p = cambiar(carmen, AHORRO, flags=[Flag.low_confidence])
    a = planificar(p, [Peticion(motivo=Motivo.planned_expense)])
    assert (AHORRO, R) in resumen(a)


def test_peticiones_sobre_la_misma_ruta_se_agrupan(carmen):
    a = planificar(carmen, [ANUAL, Peticion(motivo=Motivo.liquidity_change)])
    rutas = [q.path for q in a.preguntas]
    assert len(rutas) == len(set(rutas)) == 6 and a.aplazadas == []
    liquidez = next(q for q in a.preguntas if q.path == LIQUIDEZ)
    assert liquidez.tipo == R and liquidez.motivos == [Motivo.next_review_due, Motivo.liquidity_change]
    assert a.preguntas[0].path == LIQUIDEZ  # lo que cambia va antes que lo que se confirma


def test_se_recorta_a_max_preguntas_en_orden_del_guion(carmen):
    rutas = [r for r in CAMPOS if r.startswith("financial.") and r not in CALCULADOS]
    rutas += ["objectives.o1.goal", "objectives.o1.amount_eur"]
    a = planificar(carmen, [Peticion(motivo=Motivo.advisor_request, rutas=rutas)])
    assert len(a.preguntas) == MAX_PREGUNTAS
    assert [q.path for q in a.preguntas] + a.aplazadas == rutas
    assert not a.reevaluacion_completa  # dos bloques


def test_cambios_en_tres_bloques_amplian_a_reevaluacion_completa(carmen):
    a = planificar(carmen, [Peticion(motivo=Motivo.retirement), Peticion(motivo=Motivo.behaviour_vs_tolerance),
                            Peticion(motivo=Motivo.knowledge_not_assessed, rutas=["knowledge.etfs"])])
    assert a.reevaluacion_completa and "bloques" in a.razones[0]


def test_una_alerta_needs_advisor_abierta_amplia(carmen):
    p = carmen.model_copy(deep=True)
    p.alerts.append(Alerta(id="a-x", flag=Flag.needs_advisor, message="DATOS SIMULADOS"))
    a = planificar(p, [Peticion(motivo=Motivo.liquidity_change)])
    assert a.reevaluacion_completa and len(a.preguntas) == 3


def test_reevaluacion_pedida_explicitamente(carmen):
    a = planificar(carmen, [Peticion(motivo=Motivo.full_reassessment_requested)])
    assert a.reevaluacion_completa and a.preguntas == []


@pytest.mark.parametrize("peticion", [
    {"motivo": "knowledge_not_assessed"},                                          # faltan rutas
    {"motivo": "knowledge_not_assessed", "rutas": [AHORRO]},                       # fuera de su prefijo
    {"motivo": "advisor_request", "rutas": ["financial.loss_capacity_eur"]},       # calculado
    {"motivo": "advisor_request", "rutas": ["financial.salario_secreto"]},         # desconocida
    {"motivo": "advisor_request", "rutas": ["disclosures.ai_notice_ack"]},         # se recoge en cada sesión
    {"motivo": "liquidity_change", "rutas": [AHORRO]},                             # motivo de rutas fijas
])
def test_peticiones_invalidas(carmen, peticion):
    with pytest.raises(DatoInvalido):
        planificar(carmen, [Peticion(**peticion)])


# ---------- dato cambiado (sesión de revisión) ----------

INGRESOS, DEUDAS = "financial.net_monthly_income_eur", "financial.debts_eur"


def cambio(*rutas):
    return Peticion(motivo=Motivo.value_changed, rutas=list(rutas))


def test_cambio_de_ahorro_confirma_gastos_y_deudas_sin_repreguntar_el_ahorro(carmen):
    a = planificar(carmen, [cambio(AHORRO)])
    assert resumen(a) == [(GASTOS, C), (DEUDAS, C)]  # entradas de colchón y capacidad de pérdida
    assert all(q.motivos == [Motivo.value_changed] for q in a.preguntas)


def test_cambio_de_liquidez_confirma_el_plazo(carmen):
    assert resumen(planificar(carmen, [cambio(LIQUIDEZ)])) == [(PLAZO, C)]


def test_cambio_de_horizonte_confirma_la_liquidez(carmen):
    assert resumen(planificar(carmen, [cambio(PLAZO)])) == [(LIQUIDEZ, C)]


def test_caida_de_ingresos_pide_confirmar_los_gastos_fijos(carmen):
    """Única dependencia justificada hoy: la regla del verificador gastos fijos >= ingresos."""
    a = planificar(cambiar(carmen, INGRESOS, 800), [cambio(INGRESOS)])
    assert resumen(a) == [(GASTOS, C)] and a.preguntas[0].valor_vigente == 900
    assert not a.reevaluacion_completa


def test_caida_de_ingresos_no_cambia_el_perfil_de_riesgo_ni_las_restricciones(carmen):
    """Se actualiza el hecho financiero, pero calculos.py no usa los ingresos: no hay recálculo nuevo."""
    nueva = cambiar(carmen, INGRESOS, 800)
    assert alcance.cambiados(carmen, nueva) == [INGRESOS]  # el hecho sí cambia (y se avisaría)
    assert es_material(carmen, nueva) == []  # pero no mueve ningún resultado
    assert nueva.assessments == carmen.assessments


def test_si_los_ingresos_caen_por_debajo_de_los_gastos_lo_detecta_el_verificador(carmen):
    from app.agentes import verificador  # reglas deterministas, sin Claude

    alertas = [(a.path, a.flag) for a in verificador.reglas(cambiar(carmen, INGRESOS, 800))]
    assert (GASTOS, Flag.needs_advisor) in alertas
    assert not [a for a in verificador.reglas(carmen) if a.path == GASTOS]


def test_la_dependencia_ingresos_gastos_es_simetrica():
    assert GASTOS in DEPENDENCIAS[INGRESOS] and INGRESOS in DEPENDENCIAS[GASTOS]


def test_un_dato_cambiado_que_queda_dudoso_se_repregunta(carmen):
    p = cambiar(carmen, AHORRO, 10000, flags=[Flag.low_confidence])
    assert resumen(planificar(p, [cambio(AHORRO)]))[0] == (AHORRO, R)


def test_un_dato_ya_cambiado_no_se_pregunta_aunque_lo_pida_otro_motivo(carmen):
    a = planificar(carmen, [ANUAL, cambio(LIQUIDEZ, AHORRO)])
    rutas = [q.path for q in a.preguntas]
    assert LIQUIDEZ not in rutas and AHORRO not in rutas and PLAZO in rutas


def test_cambios_en_tres_bloques_amplian(carmen):
    a = planificar(carmen, [cambio(AHORRO, PLAZO, "risk_tolerance.scenario_score")])
    assert a.reevaluacion_completa and "bloques" in a.razones[0]


@pytest.mark.parametrize("rutas", [[], ["financial.loss_capacity_eur"], ["disclosures.purpose_ack"]])
def test_dato_cambiado_invalido(carmen, rutas):
    with pytest.raises(DatoInvalido):
        planificar(carmen, [cambio(*rutas)])


def test_el_catalogo_de_motivos_es_cerrado():
    with pytest.raises(ValidationError):
        Peticion(motivo="compruebalo_todo")


def test_no_modifica_el_perfil(carmen):
    antes = carmen.model_dump()
    planificar(carmen, [ANUAL, Peticion(motivo=Motivo.liquidity_change)])
    vencimientos(carmen, HOY + timedelta(days=4000))
    assert carmen.model_dump() == antes


# ---------- vencimientos ----------

def test_perfil_reciente_sin_vencimientos(carmen):
    assert vencimientos(carmen, HOY) == []


def test_next_review_vencido(carmen):
    for ruta, f in carmen.mifid.items():  # datos dados antes de que venciera la revisión
        carmen.mifid[ruta] = f.model_copy(update={"updated_at": _hace(30)})
    carmen.review.next_review = "2026-11-01"
    assert vencimientos(carmen, HOY) == [ANUAL]
    carmen.review.next_review = "2027-11-11"
    assert vencimientos(carmen, HOY) == []


def test_la_revision_anual_no_repite_lo_confirmado_tras_el_vencimiento(carmen):
    for ruta, f in carmen.mifid.items():
        carmen.mifid[ruta] = f.model_copy(update={"updated_at": _hace(30)})
    carmen.review.next_review = "2026-11-01"
    # En esta misma sesión confirma gastos y ahorro: ya no se le vuelven a pedir.
    for ruta in (GASTOS, AHORRO):
        carmen.mifid[ruta] = carmen.mifid[ruta].model_copy(update={"confirmed_at": _hace(0)})
    [anual] = vencimientos(carmen, HOY)
    assert GASTOS not in anual.rutas and AHORRO not in anual.rutas and len(anual.rutas) == 4


def test_la_revision_anual_desaparece_si_todo_esta_confirmado(carmen):
    for ruta, f in carmen.mifid.items():
        carmen.mifid[ruta] = f.model_copy(update={"updated_at": _hace(30), "confirmed_at": _hace(1)})
    carmen.review.next_review = "2026-11-01"
    assert vencimientos(carmen, HOY) == []


def test_la_revision_anual_pregunta_lo_que_falta(carmen):
    for ruta, f in carmen.mifid.items():
        carmen.mifid[ruta] = f.model_copy(update={"updated_at": _hace(0)})
    del carmen.mifid[LIQUIDEZ]
    carmen.review.next_review = "2026-11-01"
    [anual] = vencimientos(carmen, HOY)
    assert anual.rutas == [LIQUIDEZ]
    assert resumen(planificar(carmen, [anual])) == [(LIQUIDEZ, R)]  # lo que falta se pregunta, no se confirma


def test_bloque_caducado(carmen):
    for ruta in [r for r in carmen.mifid if r.startswith("financial.")]:
        carmen.mifid[ruta] = carmen.mifid[ruta].model_copy(update={"updated_at": _hace(400)})
    assert vencimientos(carmen, HOY) == [Peticion(motivo=Motivo.stale_block, rutas=[
        "financial.net_monthly_income_eur", "financial.income_stability", GASTOS, AHORRO, "financial.debts_eur"])]


def test_un_dato_confirmado_no_caduca(carmen):
    for ruta in [r for r in carmen.mifid if r.startswith("financial.")]:
        carmen.mifid[ruta] = carmen.mifid[ruta].model_copy(update={"updated_at": _hace(400),
                                                                   "confirmed_at": _hace(10)})
    assert vencimientos(carmen, HOY) == []


def test_el_plazo_confirmado_cuenta_desde_la_confirmacion(carmen):
    f = carmen.mifid[PLAZO].model_copy(update={"updated_at": _hace(3 * 365.25), "confirmed_at": _hace(0)})
    assert plazo_restante(f, HOY) == 10.0


def test_plazo_restante(carmen):
    f = carmen.mifid[PLAZO].model_copy(update={"updated_at": _hace(3 * 365.25)})
    assert plazo_restante(f, HOY) == 7.0


@pytest.mark.parametrize("dias, vence", [
    (200, False),             # quedan 9,5 años: mismo perfil por plazo y mismos filtros
    (9.5 * 365.25, True),     # queda medio año: aparece el filtro de renta fija a corto plazo
    (11 * 365.25, True),      # plazo agotado
])
def test_plazo_que_envejece(carmen, dias, vence):
    carmen.mifid[PLAZO] = carmen.mifid[PLAZO].model_copy(update={"updated_at": _hace(dias)})
    motivos = [p.motivo for p in vencimientos(carmen, HOY)]
    assert (Motivo.horizon_elapsed in motivos) is vence


# ---------- cambios entre versiones ----------

def test_cambiados_valor_declarado_y_flags_en_orden_del_guion(carmen):
    nueva = cambiar(cambiar(carmen, LIQUIDEZ, "high"), AHORRO, flags=[Flag.low_confidence])
    nueva = cambiar(nueva, "knowledge.equity_funds", declared="medium")  # el fixture declara "high"
    assert alcance.cambiados(carmen, nueva) == ["knowledge.equity_funds", AHORRO, LIQUIDEZ]


def test_una_confirmacion_no_es_un_cambio(carmen):
    cita = Evidencia(session_id="s-2", turn_id="t-001", t=(0, 1), quote="Sí, sigo igual")
    nueva = cambiar(carmen, GASTOS, evidence=[cita], confidence=0.99, confirmed_at=_hace(0))
    assert alcance.cambiados(carmen, nueva) == []


def test_los_calculados_no_son_cambios_propios(carmen):
    assert alcance.cambiados(carmen, cambiar(carmen, AHORRO, 10000)) == [AHORRO]


# ---------- materialidad ----------

def test_sin_cambios_no_es_material(carmen):
    assert es_material(carmen, carmen.model_copy(deep=True)) == []


def test_confirmar_con_otra_cita_no_es_material(carmen):
    cita = Evidencia(session_id="s-1", turn_id="t-001", t=(0, 2), quote="Sí, sigo gastando unos 900 €")
    assert es_material(carmen, cambiar(carmen, GASTOS, evidence=[cita])) == []


def test_liquidez_alta_cambia_el_filtro_de_reembolso(carmen):
    assert es_material(carmen, cambiar(carmen, LIQUIDEZ, "high")) == ["filter:redemption_lag_days"]


def test_caida_del_ahorro_cambia_la_capacidad_de_perdida(carmen):
    # 80.000 → 10.000 €: la capacidad cae de 74.600 a 4.600 €; manda la tolerancia, el perfil no cambia.
    assert es_material(carmen, cambiar(carmen, AHORRO, 10000)) == ["loss_capacity"]


def test_salto_de_perfil(carmen):
    cambios = es_material(carmen, cambiar(carmen, "risk_tolerance.scenario_score", 4))
    assert "risk_profile" in cambios and "risk_profile_jump" in cambios


def test_conveniencia_y_sostenibilidad(carmen):
    assert "appropriateness:equity_funds" in es_material(carmen, cambiar(carmen, "knowledge.equity_funds", "high"))
    assert "esg_only" in es_material(carmen, cambiar(carmen, "sustainability.preference", "strong"))
