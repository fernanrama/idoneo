"""Confirmar un dato (diseño 06, §4.3; decisiones D1 y D3): mismo valor, declarado y fuente acumula la
evidencia; una confirmación pura sobre un perfil active lo deja active.

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Datos simulados.
"""

from __future__ import annotations

from app.perfil import store
from app.perfil.modelos import EstadoPerfil, Evidencia, Flag, Fuente, Parche

C = "carmen-68"
GASTOS = "financial.fixed_monthly_costs_eur"
CITA = Evidencia(session_id="s-revision", turn_id="t-003", t=(4.0, 7.0), quote="Sí, sigo gastando unos 900 €")
EXTRACTOR = "agent:extractor"


def como_estaba(ruta: str, **cambios) -> Parche:
    """El mismo dato que hay ahora en el perfil, con los cambios indicados (p. ej. otra evidencia)."""
    f = store.perfil(C).mifid[ruta]
    datos = {"path": ruta, "value": f.value, "source": f.source, "declared": f.declared,
             "confidence": f.confidence, "confidence_basis": f.confidence_basis,
             "evidence": f.evidence, "flags": f.flags}
    return Parche(**{**datos, **cambios})


def test_confirmar_acumula_la_evidencia_y_anota_la_fecha(carmen):
    antes = store.perfil(C).mifid[GASTOS]
    p = store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión · s-revision", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert p.version == carmen.version + 1  # queda trazado en el historial
    assert f.value == antes.value and f.source == antes.source
    assert f.evidence == [*antes.evidence, CITA]  # la cita anterior no se pierde
    assert f.confirmed_at == p.created_at and f.confirmed_by == EXTRACTOR
    assert (f.updated_at, f.updated_by) == (antes.updated_at, antes.updated_by)  # el valor no cambió


def test_mismo_valor_con_menos_confianza_es_confirmacion_y_conserva_la_mas_alta(carmen):
    antes = store.perfil(C).mifid[GASTOS]  # 0,7 en el fixture
    p = store.aplicar(C, [como_estaba(GASTOS, confidence=0.4, confidence_basis="rubric:aproximada:v1",
                                      evidence=[CITA])], "revisión", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert f.evidence == [*antes.evidence, CITA] and f.confirmed_at == p.created_at
    assert (f.confidence, f.confidence_basis) == (antes.confidence, antes.confidence_basis)


def test_mismo_valor_con_mas_confianza_toma_la_mas_alta_y_acumula(carmen):
    antes = store.perfil(C).mifid[GASTOS]
    p = store.aplicar(C, [como_estaba(GASTOS, confidence=0.95, confidence_basis="rubric:explicita:v1",
                                      evidence=[CITA])], "revisión", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert f.evidence == [*antes.evidence, CITA]
    assert (f.confidence, f.confidence_basis) == (0.95, "rubric:explicita:v1")


def test_reprocesar_la_misma_cita_no_duplica(carmen):
    """El mismo turno citado otra vez (aunque el modelo recorte la cita distinto) no es evidencia nueva."""
    v = store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión", EXTRACTOR).version
    otra_vez = CITA.model_copy(update={"quote": "sigo gastando unos 900 €"})
    p = store.aplicar(C, [como_estaba(GASTOS, confidence=0.95, evidence=[otra_vez])], "reproceso", EXTRACTOR)
    assert p.version == v and p.mifid[GASTOS].evidence[-1] == CITA


def test_si_cambian_los_flags_se_aplican_y_se_conserva_la_evidencia(carmen):
    antes = store.perfil(C).mifid[GASTOS]
    p = store.aplicar(C, [como_estaba(GASTOS, flags=[Flag.low_confidence], evidence=[CITA])], "duda", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert f.flags == [Flag.low_confidence] and f.evidence == [*antes.evidence, CITA] and f.value == antes.value


def test_un_cambio_de_declarado_no_es_confirmacion(carmen):
    p = store.aplicar(C, [como_estaba(GASTOS, declared=1500, evidence=[CITA])], "declara otra cifra", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert f.declared == 1500 and f.evidence == [CITA] and f.confirmed_at is None


def test_repetir_la_misma_confirmacion_no_crea_version(carmen):
    v = store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión", EXTRACTOR).version
    assert store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión", EXTRACTOR).version == v


def test_mismo_valor_sin_cita_no_borra_la_evidencia(carmen):
    # Un agente no puede escribir sin evidencia (validacion.py); el asesor sí. Si el asesor reenvía su
    # mismo dato sin cita, no hay nada nuevo que guardar y la evidencia anterior se conserva.
    asesor = "advisor:asesor-07"
    v = store.aplicar(C, [como_estaba(GASTOS, source=Fuente.advisor, evidence=[CITA])], "corrige", asesor)
    p = store.aplicar(C, [como_estaba(GASTOS, evidence=[])], "reenvía", asesor)
    assert p.version == v.version and p.mifid[GASTOS].evidence == [CITA]


def test_un_cambio_de_valor_sustituye_la_evidencia(carmen):
    p = store.aplicar(C, [como_estaba(GASTOS, value=1200, evidence=[CITA])], "gasta más", EXTRACTOR)
    f = p.mifid[GASTOS]
    assert f.value == 1200 and f.evidence == [CITA] and f.confirmed_at is None
    assert f.updated_at == p.created_at


def test_otra_fuente_no_es_una_confirmacion(carmen):
    p = store.aplicar(C, [como_estaba(GASTOS, source=Fuente.advisor, evidence=[CITA])],
                      "lo revisa la entidad", "advisor:asesor-07")
    f = p.mifid[GASTOS]
    assert f.source == Fuente.advisor and f.evidence == [CITA] and f.confirmed_at is None


def test_la_confirmacion_se_conserva_al_releer_y_no_abre_revision(carmen):
    store.validar(C, "asesor-07", [])
    p = store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión", EXTRACTOR)
    leido = store.perfil(C, p.version).mifid[GASTOS]
    assert leido.confirmed_at == p.created_at and leido.evidence[-1] == CITA
    assert store.restricciones_para_consumidor(C).pending_review is None  # mismo valor: nada en revisión


# ---------- estado del perfil (decisión D3) ----------

LIQUIDEZ = "objectives.o1.liquidity_need"
ESTABILIDAD = "financial.income_stability"


def servidas() -> dict:
    """Lo que recibiría GPTadvisor, sin el número de versión."""
    return store.restricciones_para_consumidor(C).model_dump(mode="json", exclude={"profile_version"})


def test_confirmacion_pura_sobre_active_sigue_active_sin_tocar_riesgo_ni_restricciones(carmen):
    v = store.validar(C, "asesor-07", [])
    antes = servidas()
    p = store.aplicar(C, [como_estaba(GASTOS, confidence=0.4, evidence=[CITA])], "revisión", EXTRACTOR)
    assert p.status == EstadoPerfil.active and p.version == v.version + 1  # versión de trazabilidad
    assert p.review.validated_by == "asesor-07"  # sigue siendo lo que validó la entidad
    assert p.assessments == v.assessments  # mismo perfil de riesgo, SRI, conveniencia
    assert servidas() == antes and antes["pending_review"] is None
    assert store.perfil_para_consumidor(C).version == p.version


def test_una_confirmacion_no_quita_una_revision_pendiente(carmen):
    store.validar(C, "asesor-07", [])
    cambio = store.aplicar(C, [Parche(path=LIQUIDEZ, value="high", source="declared", evidence=[CITA])],
                           "cambio real", EXTRACTOR)
    assert cambio.status == EstadoPerfil.review_due
    otra = CITA.model_copy(update={"turn_id": "t-005"})
    p = store.aplicar(C, [como_estaba(GASTOS, evidence=[otra])], "revisión", EXTRACTOR)
    assert p.status == EstadoPerfil.review_due  # no reactiva
    assert store.revision_pendiente(C).paths == [LIQUIDEZ]  # el cambio real sigue avisado


def test_un_cambio_real_pasa_a_review_due_y_se_avisa(carmen):
    store.validar(C, "asesor-07", [])
    p = store.aplicar(C, [como_estaba(GASTOS, value=1200, evidence=[CITA])], "gasta más", EXTRACTOR)
    assert p.status == EstadoPerfil.review_due and store.revision_pendiente(C).paths == [GASTOS]


def test_si_cambian_los_flags_no_es_pura_y_se_avisa(carmen):
    """Mismo valor, pero ahora con una duda: la entidad debe revisarlo y GPTadvisor saberlo."""
    store.validar(C, "asesor-07", [])
    p = store.aplicar(C, [como_estaba(ESTABILIDAD, flags=[Flag.low_confidence], evidence=[CITA])],
                      "duda", EXTRACTOR)
    assert p.status == EstadoPerfil.review_due
    assert store.revision_pendiente(C).paths == [ESTABILIDAD]


def test_si_la_duda_afecta_a_la_idoneidad_tampoco_es_pura(carmen):
    store.validar(C, "asesor-07", [])
    p = store.aplicar(C, [como_estaba(GASTOS, flags=[Flag.low_confidence], evidence=[CITA])], "duda", EXTRACTOR)
    assert p.status == EstadoPerfil.review_due and not p.assessments.suitability.complete


def test_una_confirmacion_no_activa_un_perfil_sin_validar(carmen):
    assert carmen.status == EstadoPerfil.pending_validation
    p = store.aplicar(C, [como_estaba(GASTOS, evidence=[CITA])], "revisión", EXTRACTOR)
    assert p.status == EstadoPerfil.pending_validation
