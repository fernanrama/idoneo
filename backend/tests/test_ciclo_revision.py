"""Ciclo de una microentrevista MiFID sobre un perfil validado (reglas R1–R6 del 11/11/2026).

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Sin Claude ni
ElevenLabs: las escrituras simulan lo que haría el extractor. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import itertools

import pytest

from app.perfil import revision, store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
AHORRO, GASTOS = "financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur"
PLAZO, LIQUIDEZ = "objectives.o1.horizon_years", "objectives.o1.liquidity_need"
_turnos = itertools.count(1)


def decir(ruta: str, valor, texto: str = "DATOS SIMULADOS") -> "store.Perfil":
    """Lo que escribiría el extractor: un dato nuevo o, con el mismo valor, una confirmación con su cita."""
    f = store.perfil(C).mifid.get(ruta)
    misma = f is not None and f.value == valor
    p = Parche(path=ruta, value=valor, source=f.source if misma else "declared",
               confidence=f.confidence if misma else None,
               evidence=[Evidencia(session_id="s-micro", turn_id=f"t-{next(_turnos):03d}", t=(1.0, 2.0), quote=texto)])
    return store.aplicar(C, [p], "extractor · s-micro", "agent:extractor")


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def test_la_comparacion_parte_de_la_ultima_validacion_de_la_entidad(validada):
    decir(GASTOS, 900, "Los gastos siguen en novecientos")  # confirmación pura: versión active sin validar
    assert store.perfil(C).status == EstadoPerfil.active and store.perfil(C).version == validada.version + 1
    decir(PLAZO, 1, "Lo necesitaré el año que viene")
    c = revision.comparar(C)
    assert c.desde_version == validada.version
    assert {x.path for x in c.cambios} == {GASTOS, PLAZO}  # la confirmación y el cambio, frente a lo validado
