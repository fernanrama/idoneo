"""Validación estricta de lo que se escribe en el perfil (rol A).

Todo lo que entra por `store` pasa por aquí, con cualquier almacén:
- la ruta existe en `modelos.CAMPOS` y el valor tiene su tipo (si no: DatoInvalido → HTTP 422);
- nadie escribe datos calculados (Conflicto → HTTP 409, como en la PR #7);
- solo una persona de la entidad escribe `source="advisor"`;
- un dato sacado de la conversación (autor `agent:*`) lleva evidencia (regla 4 del contrato 04);
- `declared` solo se guarda si difiere del valor, y entonces se marca `declared_vs_demonstrated`.

No decide nada financiero: los resultados siguen saliendo de `calculos.py`.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .modelos import CALCULADOS, CAMPOS, FAMILIAS, NIVELES, Alerta, Flag, Fuente, Parche


class DatoInvalido(ValueError):
    """La entrada no cumple el esquema o las reglas de autoría (HTTP 422)."""


class EscrituraCalculada(ValueError):
    """Se intentó escribir un dato calculado. `store` lo convierte en Conflicto (HTTP 409)."""


# Tipo de cada ruta de `modelos.CAMPOS`. Un test comprueba que ambas listas tienen las mismas rutas.
TIPOS: dict[str, tuple[str, tuple]] = {
    "disclosures.ai_notice_ack": ("bool", ()),
    "disclosures.purpose_ack": ("bool", ()),
    **{f"knowledge.{f}": ("opcion", tuple(NIVELES)) for f in FAMILIAS},
    **{f"experience.{f}.operations_last_3y": ("entero", ()) for f in FAMILIAS},
    "experience.education": ("texto", ()),
    "experience.profession": ("texto", ()),
    "financial.net_monthly_income_eur": ("eur", ()),
    "financial.income_stability": ("opcion", ("stable", "variable")),
    "financial.fixed_monthly_costs_eur": ("eur", ()),
    "financial.liquid_savings_eur": ("eur", ()),
    "financial.other_assets_eur": ("eur", ()),
    "financial.debts_eur": ("eur", ()),
    "financial.mortgage_eur": ("eur", ()),
    "financial.emergency_fund_months": ("calculado", ()),
    "financial.loss_capacity_eur": ("calculado", ()),
    "objectives.o1.goal": ("texto", ()),
    "objectives.o1.amount_eur": ("eur", ()),
    "objectives.o1.horizon_years": ("anios", ()),
    "objectives.o1.liquidity_need": ("opcion", ("high", "medium", "low")),
    "risk_tolerance.scenario_score": ("puntuacion", ()),
    "risk_tolerance.max_drawdown_accepted_pct": ("pct", ()),
    "risk_tolerance.past_behaviour": ("texto", ()),
    "sustainability.preference": ("opcion", ("none", "some", "strong")),
    "sustainability.min_sfdr_article": ("sfdr", ()),
    "sustainability.explained": ("bool", ()),
}

_AUTOR = re.compile(r"^(agent:[a-z_]{1,32}|advisor:[A-Za-z0-9._-]{1,64}|fn:[a-z_]{1,64}|fixture|system)$")
_CLIENT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
LIMITE_TEXTO = 1000


def comprobar_autor(autor: str) -> str:
    if not isinstance(autor, str) or not _AUTOR.match(autor):
        raise DatoInvalido(f"Autor no válido: {autor!r} (agent:<x>, advisor:<id>, fn:<x>, fixture o system)")
    return autor


def comprobar_client_id(client_id: str) -> str:
    """Minúsculas, números, '-' y '_' (también evita rutas de fichero raras en el almacén en memoria)."""
    if not isinstance(client_id, str) or not _CLIENT_ID.match(client_id):
        raise DatoInvalido(f"client_id no válido: {client_id!r} (a-z, 0-9, '-' y '_', máx. 64)")
    return client_id


def comprobar_ruta(ruta: str) -> str:
    if ruta not in CAMPOS:
        raise DatoInvalido(f"Ruta desconocida en la capa MiFID: {ruta!r}")
    return ruta


def _numero(ruta: str, valor: Any, minimo: float, maximo: float | None = None) -> float:
    if isinstance(valor, bool):
        raise DatoInvalido(f"{ruta}: se esperaba un número")
    if isinstance(valor, str):
        try:
            valor = float(valor.strip())
        except ValueError as e:
            raise DatoInvalido(f"{ruta}: {valor!r} no es un número") from e
    if not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise DatoInvalido(f"{ruta}: se esperaba un número")
    if valor < minimo or (maximo is not None and valor > maximo):
        raise DatoInvalido(f"{ruta}: {valor} fuera de rango")
    return float(valor)


def _entero(ruta: str, valor: Any, minimo: int, maximo: int | None = None) -> int:
    n = _numero(ruta, valor, minimo, maximo)
    if not n.is_integer():
        raise DatoInvalido(f"{ruta}: se esperaba un entero")
    return int(n)


def normalizar(ruta: str, valor: Any) -> Any:
    """Valor con el tipo de la ruta, o None. Lanza DatoInvalido si no encaja."""
    tipo, opciones = TIPOS[comprobar_ruta(ruta)]
    if valor is None:
        return None
    if tipo == "calculado":
        raise EscrituraCalculada(f"{ruta} es calculado: no se escribe a mano")
    if tipo == "bool":
        if not isinstance(valor, bool):
            raise DatoInvalido(f"{ruta}: se esperaba true/false")
        return valor
    if tipo == "opcion":
        if valor not in opciones:
            raise DatoInvalido(f"{ruta}: {valor!r} no está entre {list(opciones)}")
        return valor
    if tipo == "eur":
        return round(_numero(ruta, valor, 0), 2)
    if tipo in ("anios", "pct"):
        return _numero(ruta, valor, 0, 100)
    if tipo == "entero":
        return _entero(ruta, valor, 0)
    if tipo == "puntuacion":
        return _entero(ruta, valor, 1, 5)
    if tipo == "sfdr":
        n = _entero(ruta, valor, 6, 9)
        if n not in (6, 8, 9):
            raise DatoInvalido(f"{ruta}: artículo SFDR {n} no válido (6, 8 o 9)")
        return n
    if tipo == "texto":
        if not isinstance(valor, str) or not valor.strip() or len(valor) > LIMITE_TEXTO:
            raise DatoInvalido(f"{ruta}: se esperaba un texto no vacío de hasta {LIMITE_TEXTO} caracteres")
        return valor.strip()
    raise DatoInvalido(f"{ruta}: tipo {tipo!r} sin validar")  # pragma: no cover


def comprobar_parche(parche: Parche, autor: str) -> Parche:
    """Devuelve el parche normalizado o lanza DatoInvalido / EscrituraCalculada."""
    comprobar_autor(autor)
    ruta = comprobar_ruta(parche.path)
    if ruta in CALCULADOS or parche.source == Fuente.calculated:
        raise EscrituraCalculada(f"{ruta} es calculado: no se escribe a mano")

    if autor.startswith("advisor:"):
        fuente = Fuente.advisor
    elif parche.source == Fuente.advisor:
        raise DatoInvalido(f"{ruta}: solo una persona de la entidad escribe source=advisor")
    else:
        fuente = parche.source

    valor = normalizar(ruta, parche.value)
    declarado = normalizar(ruta, parche.declared)
    if autor.startswith("agent:") and valor is not None and not parche.evidence:
        raise DatoInvalido(f"{ruta}: un dato sacado de la conversación necesita su evidencia")

    flags = set(parche.flags)
    if declarado is not None and declarado == valor:
        declarado = None
    if declarado is not None and fuente == Fuente.demonstrated:
        flags.add(Flag.declared_vs_demonstrated)
    if declarado is None:
        flags.discard(Flag.declared_vs_demonstrated)
    return parche.model_copy(update={
        "source": fuente, "value": valor, "declared": declarado,
        "flags": sorted(flags, key=list(Flag).index),
    })


def comprobar_alerta(alerta: Alerta) -> Alerta:
    if alerta.path is not None:
        comprobar_ruta(alerta.path)
    if not alerta.message.strip():
        raise DatoInvalido("Una alerta necesita un mensaje")
    return alerta
