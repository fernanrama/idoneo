"""Resumen del cliente para que lo lea otro agente (Dev B). v0: plantilla determinista."""

from __future__ import annotations

from ..perfil import calculos
from ..perfil.modelos import Perfil


async def resumen(perfil: Perfil) -> str:
    v = {k: c.value for k, c in perfil.mifid.items()}
    r = calculos.restricciones(perfil)
    alertas = "; ".join(a.message for a in perfil.alerts if a.status == "open") or "ninguna"
    return (
        f"Cliente {perfil.client_id} (perfil v{perfil.version}, estado {perfil.status.value}). "
        f"Objetivo: {v.get('objective.goal')} a {v.get('objective.horizon_years')} años. "
        f"Conocimiento demostrado: fondos {v.get('knowledge.investment_funds')}, "
        f"renta variable {v.get('knowledge.equity_risk')}. Tolerancia: {v.get('risk.tolerance')}. "
        f"Riesgo máximo SRI {r.max_risk_indicator}. Alertas: {alertas}. "
        "No recomendar nada que supere estas restricciones; explicar en lenguaje sencillo."
    )
