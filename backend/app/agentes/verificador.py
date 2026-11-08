"""Agente verificador (B2, Pablo). Revisa el perfil en segundo plano y genera alertas.

No calcula resultados (eso es determinista): solo marca flags y propone repreguntas.
Flags: declared_vs_demonstrated, inconsistent, low_confidence, needs_advisor.

v1: reglas deterministas mínimas; Pablo añade la revisión con Claude (MODEL_VERIFICADOR).
"""

from __future__ import annotations

import uuid

from ..perfil.modelos import Alerta, Flag, Perfil, Turno


async def verificar(perfil: Perfil, turnos: list[Turno]) -> list[Alerta]:
    ya = {(a.flag, a.path) for a in perfil.alerts}
    nuevas: list[Alerta] = []
    for ruta, f in perfil.mifid.items():
        if Flag.declared_vs_demonstrated in f.flags and (Flag.declared_vs_demonstrated, ruta) not in ya:
            nuevas.append(Alerta(
                id=f"a-{uuid.uuid4().hex[:6]}", path=ruta, flag=Flag.declared_vs_demonstrated,
                message=f"Declarado «{f.declared}» frente a demostrado «{f.value}».", evidence=f.evidence,
            ))
    plazo = perfil.mifid.get("objectives.o1.horizon_years")
    score = perfil.mifid.get("risk_tolerance.scenario_score")
    if plazo and score and plazo.value is not None and score.value is not None:
        if float(plazo.value) < 2 and int(score.value) >= 4 and (Flag.inconsistent, "risk_tolerance.scenario_score") not in ya:
            nuevas.append(Alerta(
                id=f"a-{uuid.uuid4().hex[:6]}", path="risk_tolerance.scenario_score", flag=Flag.inconsistent,
                message="Tolerancia alta con un objetivo a menos de 2 años: conviene repreguntar.",
            ))
    return nuevas
