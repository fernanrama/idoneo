"""Cálculos deterministas del perfil. El modelo de IA nunca pone estos números.

Los parámetros (meses de colchón, umbral de confianza) son supuestos del equipo: ver supuestos.py.
"""

from __future__ import annotations

from datetime import datetime

from . import supuestos as S
from .modelos import Fact, Fuente, autor_funcion


def meses_colchon(estabilidad: str | None) -> int:
    return S.MESES_COLCHON.get(estabilidad or "", S.MESES_COLCHON_DEFECTO)


def colchon_emergencia(gastos_fijos_mensuales: float, meses: int = S.MESES_COLCHON_DEFECTO) -> float:
    return round(meses * gastos_fijos_mensuales, 2)


def capacidad_perdida(ahorro_liquido: float, colchon: float, deudas: float) -> float:
    """Lo que el cliente podría perder sin comprometer su colchón ni sus deudas. Nunca negativa."""
    return round(max(0.0, ahorro_liquido - colchon - deudas), 2)


def confianza_por_rubrica(coherentes: int, preguntas: int) -> float:
    """Proporción de preguntas de comprobación cuya respuesta respalda el nivel asignado."""
    if preguntas <= 0 or not 0 <= coherentes <= preguntas:
        raise ValueError("Se necesita 0 <= coherentes <= preguntas y preguntas > 0")
    return round(coherentes / preguntas, 2)


def es_confianza_baja(confianza: float | None) -> bool:
    return confianza is not None and confianza < S.UMBRAL_CONFIANZA


def campos_calculados(mifid: dict[str, Fact], momento: datetime) -> dict[str, Fact]:
    """Datos calculados a partir de los datos disponibles. Si falta una entrada, no se calcula."""

    def v(ruta: str):
        d = mifid.get(ruta)
        return None if d is None else d.value

    resultado: dict[str, Fact] = {}
    gastos = v("financial.fixed_monthly_costs_eur")
    if gastos is None:
        return resultado

    meses = meses_colchon(v("financial.income_stability"))
    resultado["financial.emergency_fund_months"] = Fact(
        value=meses, source=Fuente.calculated, updated_at=momento,
        updated_by=autor_funcion("meses_colchon"), inputs=["financial.income_stability"],
    )
    ahorro, deudas = v("financial.liquid_savings_eur"), v("financial.debts_eur")
    if ahorro is not None and deudas is not None:
        resultado["financial.loss_capacity_eur"] = Fact(
            value=capacidad_perdida(ahorro, colchon_emergencia(gastos, meses), deudas),
            source=Fuente.calculated, updated_at=momento, updated_by=autor_funcion("capacidad_perdida"),
            inputs=["financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur",
                    "financial.emergency_fund_months", "financial.debts_eur"],
        )
    return resultado
