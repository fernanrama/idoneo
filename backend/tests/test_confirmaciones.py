"""Confirmar un dato (diseño 06, §4.3, hueco H4): mismo valor con una cita nueva acumula la evidencia.

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Datos simulados.
"""

from __future__ import annotations

from app.perfil import store
from app.perfil.modelos import Evidencia, Fuente, Parche

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
