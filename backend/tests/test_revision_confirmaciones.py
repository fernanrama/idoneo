"""Revisión pedida por el cliente (#46) con las confirmaciones de #45: mismo valor, cita nueva.

Contrato: se ejecuta con cada almacén. Sin Claude ni ElevenLabs. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import pytest

from app.perfil import revision, store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
GASTOS = "financial.fixed_monthly_costs_eur"


def confirmar(ruta: str, cita: str, turno: str = "t-010"):
    f = store.perfil(C).mifid[ruta]
    p = Parche(path=ruta, value=f.value, source=f.source, confidence=f.confidence,
               evidence=[Evidencia(session_id="s-rev", turn_id=turno, t=(1.0, 2.0), quote=cita)])
    return store.aplicar(C, [p], "extractor · s-rev", "agent:extractor")


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def test_una_confirmacion_cierra_su_pregunta(validada):
    revision.abrir(C, ["income_change"])
    antes = store.perfil(C).mifid[GASTOS]
    p = confirmar(GASTOS, "Los gastos siguen en novecientos")
    f = p.mifid[GASTOS]
    assert f.updated_at == antes.updated_at and f.confirmed_at == p.created_at  # #45: solo confirmed_at
    assert {q.path: q.respondida for q in revision.en_curso(C).preguntas}[GASTOS] is True


def test_la_comparacion_muestra_la_confirmacion_con_su_cita_nueva(validada):
    revision.abrir(C, ["income_change"])
    confirmar(GASTOS, "Los gastos siguen en novecientos")
    c = revision.comparar(C)
    [cambio] = [x for x in c.cambios if x.path == GASTOS]
    assert cambio.antes == cambio.ahora == 900
    assert cambio.cita == "Los gastos siguen en novecientos"  # la más reciente, no la de la entrevista inicial
    assert c.perfil_antes == c.perfil_ahora and c.efectos == []  # confirmar no mueve el riesgo


def test_la_revision_sigue_en_borrador_tras_una_confirmacion(validada):
    revision.abrir(C, ["income_change"])
    assert confirmar(GASTOS, "Los gastos siguen en novecientos").status != EstadoPerfil.active
