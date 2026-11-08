"""Lista cerrada de datos de la capa MiFID (contrato 04): ruta, tipo y si es calculado.

Es el único sitio que dice qué rutas existen. Los agentes solo pueden escribir rutas de aquí
que no sean calculadas. `normalizar()` comprueba y convierte el valor al tipo de la ruta.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from .errores import CampoInvalido
from .modelos import Nivel

FAMILIAS: tuple[str, ...] = (
    "deposits_money_market",
    "fixed_income_funds",
    "mixed_funds",
    "equity_funds",
    "etfs",
    "stocks",
    "complex_products",
)

# Familias con equivalencia directa en `search_funds.asset_type` de MyInvestor (docs/proyecto/05).
ASSET_TYPE_POR_FAMILIA: dict[str, str] = {
    "deposits_money_market": "Monetario",
    "fixed_income_funds": "Renta Fija",
    "mixed_funds": "Mixto",
    "equity_funds": "Renta Variable",
}


@dataclass(frozen=True)
class Espec:
    tipo: str  # bool | nivel | eur | anios | entero | pct | puntuacion | texto | opcion | sfdr
    opciones: tuple[str, ...] = ()
    calculado: bool = False
    descripcion: str = ""


def _construir() -> dict[str, Espec]:
    c: dict[str, Espec] = {
        "disclosures.ai_notice_ack": Espec("bool", descripcion="Informado de que habla con una IA"),
        "disclosures.purpose_ack": Espec("bool", descripcion="Entiende para qué sirve la evaluación"),
        "experience.education": Espec("texto", descripcion="Formación"),
        "experience.profession": Espec("texto", descripcion="Profesión"),
        "financial.net_monthly_income_eur": Espec("eur", descripcion="Ingresos netos mensuales"),
        "financial.income_stability": Espec("opcion", ("stable", "variable"), descripcion="Estabilidad de ingresos"),
        "financial.fixed_monthly_costs_eur": Espec("eur", descripcion="Gastos fijos mensuales"),
        "financial.liquid_savings_eur": Espec("eur", descripcion="Ahorro líquido"),
        "financial.other_assets_eur": Espec("eur", descripcion="Otros patrimonios"),
        "financial.debts_eur": Espec("eur", descripcion="Deudas pendientes"),
        "financial.emergency_fund_months": Espec("entero", calculado=True, descripcion="Meses de colchón exigidos"),
        "financial.loss_capacity_eur": Espec("eur", calculado=True, descripcion="Capacidad de soportar pérdidas"),
        "risk_tolerance.scenario_score": Espec("puntuacion", descripcion="Reacción en escenarios (1–5)"),
        "risk_tolerance.max_drawdown_accepted_pct": Espec("pct", descripcion="Caída máxima que acepta (%)"),
        "risk_tolerance.past_behaviour": Espec("texto", descripcion="Qué hizo en caídas pasadas"),
        "sustainability.preference": Espec("opcion", ("none", "some", "strong"), descripcion="Preferencia ESG"),
        "sustainability.min_sfdr_article": Espec("sfdr", descripcion="Artículo SFDR mínimo (8 o 9)"),
        "sustainability.explained": Espec("bool", descripcion="Se le explicó la sostenibilidad"),
    }
    for f in FAMILIAS:
        c[f"knowledge.{f}"] = Espec("nivel", descripcion=f"Conocimiento: {f}")
        c[f"experience.by_family.{f}.years"] = Espec("anios", descripcion=f"Años de experiencia: {f}")
        c[f"experience.by_family.{f}.operations_last_3y"] = Espec("entero", descripcion=f"Operaciones en 3 años: {f}")
    return c


CAMPOS: dict[str, Espec] = _construir()

CAMPOS_OBJETIVO: dict[str, Espec] = {
    "goal": Espec("texto", descripcion="Finalidad"),
    "amount_eur": Espec("eur", descripcion="Importe"),
    "horizon_years": Espec("anios", descripcion="Plazo en años"),
    "liquidity_need": Espec("opcion", ("high", "medium", "low"), descripcion="Necesidad de liquidez"),
    "priority": Espec("entero", descripcion="Prioridad (1 = la más alta)"),
}
_RUTA_OBJETIVO = re.compile(r"^objectives\.(o[1-9][0-9]?)\.([a-z_]+)$")

CALCULADOS: frozenset[str] = frozenset(r for r, e in CAMPOS.items() if e.calculado)


def espec(ruta: str) -> Espec:
    if ruta in CAMPOS:
        return CAMPOS[ruta]
    m = _RUTA_OBJETIVO.match(ruta)
    if m and m.group(2) in CAMPOS_OBJETIVO:
        return CAMPOS_OBJETIVO[m.group(2)]
    raise CampoInvalido(f"Ruta desconocida en la capa MiFID: {ruta!r}")


def id_objetivo(ruta: str) -> str | None:
    m = _RUTA_OBJETIVO.match(ruta)
    return m.group(1) if m else None


def _numero(ruta: str, valor: Any, minimo: float, maximo: float | None = None) -> float:
    if isinstance(valor, bool):
        raise CampoInvalido(f"{ruta}: se esperaba un número, no un booleano")
    if isinstance(valor, str):
        try:
            valor = float(valor.strip())
        except ValueError as e:
            raise CampoInvalido(f"{ruta}: {valor!r} no es un número") from e
    if not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise CampoInvalido(f"{ruta}: se esperaba un número")
    if valor < minimo or (maximo is not None and valor > maximo):
        raise CampoInvalido(f"{ruta}: {valor} fuera de rango [{minimo}, {maximo if maximo is not None else '∞'}]")
    return float(valor)


def _entero(ruta: str, valor: Any, minimo: int, maximo: int | None = None) -> int:
    n = _numero(ruta, valor, minimo, maximo)
    if not n.is_integer():
        raise CampoInvalido(f"{ruta}: se esperaba un entero")
    return int(n)


def normalizar(ruta: str, valor: Any) -> Any:
    """Devuelve el valor con el tipo de la ruta (o None) y lanza CampoInvalido si no encaja."""
    e = espec(ruta)
    if valor is None:
        return None
    match e.tipo:
        case "bool":
            if not isinstance(valor, bool):
                raise CampoInvalido(f"{ruta}: se esperaba true/false")
            return valor
        case "nivel":
            if valor not in {n.value for n in Nivel}:
                raise CampoInvalido(f"{ruta}: nivel {valor!r} no válido (none, basic, medium, high)")
            return str(valor)
        case "opcion":
            if valor not in e.opciones:
                raise CampoInvalido(f"{ruta}: {valor!r} no está entre {list(e.opciones)}")
            return str(valor)
        case "eur":
            return round(_numero(ruta, valor, 0), 2)
        case "anios":
            return _numero(ruta, valor, 0, 100)
        case "pct":
            return _numero(ruta, valor, 0, 100)
        case "entero":
            return _entero(ruta, valor, 0)
        case "puntuacion":
            return _entero(ruta, valor, 1, 5)
        case "sfdr":
            n = _entero(ruta, valor, 6, 9)
            if n not in (6, 8, 9):
                raise CampoInvalido(f"{ruta}: artículo SFDR {n} no válido (6, 8 o 9)")
            return n
        case "texto":
            if not isinstance(valor, str) or not valor.strip():
                raise CampoInvalido(f"{ruta}: se esperaba un texto no vacío")
            if len(valor) > 1000:
                raise CampoInvalido(f"{ruta}: texto demasiado largo (máx. 1000)")
            return valor.strip()
    raise CampoInvalido(f"{ruta}: tipo {e.tipo!r} sin normalizador")  # pragma: no cover
