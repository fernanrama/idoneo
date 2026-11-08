"""Resumen del cliente para otro agente, ≤150 palabras (B2, Pablo). v1: plantilla determinista."""

from __future__ import annotations

from ..perfil.calculos import valor
from ..perfil.modelos import Perfil


async def resumen(perfil: Perfil) -> str:
    s, conv = perfil.assessments.suitability, perfil.assessments.appropriateness
    no_conv = [f for f, v in conv.items() if v == "not_appropriate"]
    alertas = "; ".join(a.message for a in perfil.alerts if a.status == "open") or "ninguna abierta"
    return (
        f"Cliente {perfil.client_id} (perfil v{perfil.version}, estado {perfil.status.value}). "
        f"Objetivo: {valor(perfil, 'objectives.o1.goal')} a {valor(perfil, 'objectives.o1.horizon_years')} años. "
        f"Idoneidad: perfil {s.risk_profile.value if s.risk_profile else '—'}, SRI máximo {s.max_sri}. "
        f"No conveniente: {', '.join(no_conv) or 'ninguna familia evaluada'}. Alertas: {alertas}. "
        "No proponer nada fuera de estas restricciones; hablar en lenguaje sencillo."
    )
