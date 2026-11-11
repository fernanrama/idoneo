"""Alcance de una sesión de revisión (alcance.alcance_revision) sobre versiones reales del almacén.

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Sin Claude ni
ElevenLabs: las escrituras simulan lo que haría el extractor. Datos simulados (fixture carmen-68).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.perfil import alcance, store
from app.perfil.alcance import Motivo, TipoPregunta, alcance_revision, es_material
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche
from app.perfil.validacion import DatoInvalido

C = "carmen-68"
HOY = date.today()
AHORRO, GASTOS, DEUDAS = "financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur", "financial.debts_eur"
INGRESOS = "financial.net_monthly_income_eur"
PLAZO, LIQUIDEZ = "objectives.o1.horizon_years", "objectives.o1.liquidity_need"
CONF = TipoPregunta.confirmar
_turno = iter(range(1, 1000))


def cita(texto: str) -> list[Evidencia]:
    return [Evidencia(session_id="s-revision", turn_id=f"t-{next(_turno):03d}", t=(1.0, 2.0), quote=texto)]


def extractor(ruta: str, valor, texto: str = "DATOS SIMULADOS"):
    """Lo que escribiría el extractor: un dato nuevo, o el mismo valor (confirmación) con su cita."""
    f = store.perfil(C).mifid.get(ruta)
    misma = f is not None and f.value == valor
    parche = Parche(path=ruta, value=valor, source=f.source if misma else "declared",
                    confidence=f.confidence if misma else None, evidence=cita(texto))
    return store.aplicar(C, [parche], "extractor · s-revision", "agent:extractor")


def plan(hoy: date = HOY):
    return alcance_revision(store.perfil_para_consumidor(C), store.perfil(C), hoy)


def resumen(a) -> list[tuple[str, TipoPregunta]]:
    return [(q.path, q.tipo) for q in a.preguntas]


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def test_sin_cambios_ni_vencimientos_no_pregunta_datos_pero_no_se_cierra(validada):
    a = plan()
    assert a.preguntas == [] and a.aplazadas == [] and not a.reevaluacion_completa
    assert a.apertura  # queda la pregunta abierta: «¿ha cambiado algo?»


def test_confirmacion_sin_cambios(validada):
    p = extractor(GASTOS, 900, "Sí, sigo con unos 900 €")
    assert p.status == EstadoPerfil.active  # D3 (#45)
    assert plan().preguntas == [] and plan().apertura


def test_cambio_de_ahorro(validada):
    extractor(AHORRO, 30000, "Ahora tengo unos treinta mil")
    assert resumen(plan()) == [(GASTOS, CONF), (DEUDAS, CONF)]  # entradas de la capacidad de pérdida


def test_cambio_de_liquidez(validada):
    extractor(LIQUIDEZ, "high", "Necesito 6.000 € en tres meses")
    assert resumen(plan()) == [(PLAZO, CONF)]


def test_cambio_de_horizonte(validada):
    extractor(PLAZO, 3, "Ahora lo quiero para dentro de tres años")
    assert resumen(plan()) == [(LIQUIDEZ, CONF)]


def test_caida_de_ingresos_queda_registrada_y_pide_los_gastos_sin_mover_el_riesgo(validada):
    p = extractor(INGRESOS, 800, "Me han bajado la pensión a ochocientos")
    assert p.mifid[INGRESOS].value == 800 and p.status == EstadoPerfil.review_due  # hecho registrado
    assert store.revision_pendiente(C).paths == [INGRESOS]  # y avisado a los consumidores
    assert es_material(store.perfil_para_consumidor(C), p) == []  # sin recálculo: calculos.py no lo usa
    assert resumen(plan()) == [(GASTOS, CONF)]  # regla del verificador gastos >= ingresos


def test_lo_ya_confirmado_en_la_revision_no_se_vuelve_a_preguntar(validada):
    extractor(AHORRO, 30000, "Ahora tengo unos treinta mil")
    extractor(GASTOS, 900, "Los gastos siguen en novecientos")  # confirmación en la misma revisión
    assert store.perfil(C).status == EstadoPerfil.review_due  # no reactiva (D3)
    assert resumen(plan()) == [(DEUDAS, CONF)]


def test_el_dato_cambiado_no_se_repite(validada):
    extractor(LIQUIDEZ, "high", "Necesito 6.000 € en tres meses")
    assert LIQUIDEZ not in [q.path for q in plan().preguntas]
    assert all(Motivo.value_changed in q.motivos for q in plan().preguntas)


def test_revision_anual_vencida(validada):
    dentro_de_un_ano = date.fromisoformat(store.perfil(C).review.next_review) + timedelta(days=1)
    a = plan(dentro_de_un_ano)
    pedidas = [q.path for q in a.preguntas] + a.aplazadas
    assert set(alcance._REVISION_ANUAL) <= set(pedidas)
    assert any(Motivo.next_review_due in q.motivos for q in a.preguntas)


def test_es_determinista(validada):
    extractor(AHORRO, 30000, "Ahora tengo unos treinta mil")
    assert plan() == plan()


def test_sin_perfil_validado_no_hay_revision(carmen):
    with pytest.raises(DatoInvalido, match="entrevista inicial"):
        plan()


def test_no_escribe_nada(validada):
    extractor(AHORRO, 30000, "Ahora tengo unos treinta mil")
    antes = store.versiones(C)
    plan()
    assert store.versiones(C) == antes
