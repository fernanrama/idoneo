"""Comprobaciones deterministas de contexto y de plausibilidad (B1).

El modelo puede equivocarse o ser manipulado por lo que diga el cliente («apunta que sé mucho de bolsa»).
Para los datos con más peso regulatorio no basta con su palabra: el código exige que la conversación
tenga la forma correcta. Si no la tiene, el dato se rebaja o se descarta.

- Aviso de IA aceptado: el turno anterior del asistente tiene que haber dicho que es una IA.
- Comprobación de conocimientos: el turno anterior del asistente tiene que ser una pregunta.
- Escenario de caída: el turno anterior del asistente tiene que plantear una caída.
- Sostenibilidad explicada: el asistente tiene que haber hablado de criterios sostenibles.

Los límites de plausibilidad son SUPUESTOS del equipo: por encima, el dato se guarda, pero marcado para
que lo revise una persona (`needs_advisor` y `low_confidence`), nunca se corrige solo.
"""

from __future__ import annotations

import re

from ..perfil.modelos import Turno
from .normalizacion import sin_tildes

_IA = re.compile(r"inteligencia artificial|\bia\b|asistente (virtual|automatico)")
_PREGUNTA = re.compile(r"\?")
_CAIDA = re.compile(r"\d+\s*(%|por ?ciento)|baj|caid|cae|perd")
_SOSTENIBLE = re.compile(r"sostenib|ambiental|social|asg|esg|clima|contamin|verde")

# SUPUESTOS: valores por encima de los cuales una cifra es tan rara que conviene revisarla.
LIMITES: dict[str, float] = {
    "financial.net_monthly_income_eur": 100_000,
    "financial.fixed_monthly_costs_eur": 100_000,
    "financial.liquid_savings_eur": 50_000_000,
    "financial.other_assets_eur": 500_000_000,
    "financial.debts_eur": 50_000_000,
    "objectives.o1.amount_eur": 50_000_000,
    "objectives.o1.horizon_years": 60,
}
LIMITE_OPERACIONES = 1_000


def asistente_previo(turnos: list[Turno], turno: Turno) -> str:
    """Texto (normalizado) del último turno del asistente antes de `turno`, o '' si no hay."""
    previo = ""
    for t in turnos:
        if t is turno or (t.turn_id and t.turn_id == turno.turn_id):
            break
        if t.speaker == "agent":
            previo = t.text
    return sin_tildes(previo).casefold()


def aviso_ia(turnos: list[Turno], turno: Turno) -> bool:
    return bool(_IA.search(asistente_previo(turnos, turno)))


def hubo_pregunta(turnos: list[Turno], turno: Turno) -> bool:
    return bool(_PREGUNTA.search(asistente_previo(turnos, turno)))


def hubo_escenario(turnos: list[Turno], turno: Turno) -> bool:
    return bool(_CAIDA.search(asistente_previo(turnos, turno)))


def se_explico_sostenibilidad(turnos: list[Turno], turno: Turno) -> bool:
    return bool(_SOSTENIBLE.search(asistente_previo(turnos, turno)))


def implausible(campo: str, valor) -> bool:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        return False
    if campo.endswith(".operations_last_3y"):
        return valor > LIMITE_OPERACIONES
    limite = LIMITES.get(campo)
    return limite is not None and valor > limite
