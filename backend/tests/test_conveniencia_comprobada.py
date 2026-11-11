"""Conveniencia solo con conocimiento comprobado (bloque A, punto 2).

Lo que el cliente dice saber no basta; la experiencia compensa un conocimiento no comprobado o parcial,
pero nunca una comprobación fallada ni un «no lo conozco».
"""

import pytest

from app.perfil import calculos
from app.perfil.modelos import Conveniencia, Fact, Flag, Fuente, Perfil

A, NA = Conveniencia.appropriate, Conveniencia.not_appropriate


def _conv(fam: str, nivel: str, fuente: Fuente, ops: int | None = None, flags=(), flags_ops=()) -> Conveniencia:
    p = Perfil(client_id="test-conveniencia")
    p.mifid[f"knowledge.{fam}"] = Fact(value=nivel, source=fuente, flags=list(flags), updated_by="fixture")
    if ops is not None:
        p.mifid[f"experience.{fam}.operations_last_3y"] = Fact(
            value=ops, source=Fuente.declared, flags=list(flags_ops), updated_by="fixture")
    return calculos.conveniencia(p)[fam]


@pytest.mark.parametrize("nivel,fuente,ops,esperado", [
    ("high", Fuente.declared, None, NA),        # dice que sabe mucho y nadie lo comprobó
    ("high", Fuente.declared, 0, NA),
    ("medium", Fuente.demonstrated, None, A),   # respondió bien
    ("high", Fuente.demonstrated, None, A),
    ("basic", Fuente.demonstrated, None, NA),   # parcial
    ("basic", Fuente.demonstrated, 5, A),       # parcial + experiencia
    ("high", Fuente.declared, 5, A),            # sin comprobar + experiencia
    ("high", Fuente.declared, 4, NA),
    ("none", Fuente.demonstrated, 30, NA),      # falló la comprobación: la experiencia no lo arregla
    ("none", Fuente.declared, 30, NA),          # «no lo conozco»
    ("medium", Fuente.advisor, None, A),        # lo fija la entidad
])
def test_fondos_renta_variable(nivel, fuente, ops, esperado):
    assert _conv("equity_funds", nivel, fuente, ops) == esperado


def test_dudas_abiertas_no_cuentan():
    assert _conv("equity_funds", "medium", Fuente.demonstrated, flags=[Flag.low_confidence]) == NA
    assert _conv("equity_funds", "medium", Fuente.demonstrated, flags=[Flag.inconsistent]) == NA
    assert _conv("equity_funds", "high", Fuente.declared, 10, flags=[Flag.inconsistent]) == NA
    # Experiencia dudosa no compensa.
    assert _conv("equity_funds", "high", Fuente.declared, 10, flags_ops=[Flag.low_confidence]) == NA
    # La entidad manda aunque quede una marca antigua.
    assert _conv("equity_funds", "medium", Fuente.advisor, flags=[Flag.inconsistent]) == A


def test_complejos_piden_nivel_alto():
    assert _conv("complex_products", "medium", Fuente.demonstrated) == NA
    assert _conv("complex_products", "high", Fuente.demonstrated) == A


def test_depositos_basta_con_conocerlos():
    assert _conv("deposits_money_market", "basic", Fuente.declared) == A
    assert _conv("deposits_money_market", "none", Fuente.declared) == NA
    assert _conv("deposits_money_market", "basic", Fuente.declared, flags=[Flag.inconsistent]) == NA


def test_sin_dato_no_evaluado():
    assert calculos.conveniencia(Perfil(client_id="vacio"))["etfs"] == Conveniencia.not_assessed
