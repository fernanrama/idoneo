"""Agente verificador (Dev B). Revisa el perfil en segundo plano y genera alertas.

Contrato: recibe el perfil y la transcripción; devuelve Alerta.
Tipos mínimos: "declared_vs_demonstrated", "incoherencia" (p. ej. plazo 1 año + tolerancia alta),
"falta_dato". Cada alerta cita la evidencia que la justifica.

v0: reglas deterministas mínimas; Dev B añade la revisión con Claude (MODEL_VERIFICADOR).
"""

from __future__ import annotations

import uuid

from ..perfil.modelos import Alerta, Perfil, Turno


async def verificar(perfil: Perfil, turnos: list[Turno]) -> list[Alerta]:
    ya = {(a.type, a.field) for a in perfil.alerts}
    nuevas: list[Alerta] = []
    for nombre, campo in perfil.mifid.items():
        if "declared_vs_demonstrated" in campo.flags and ("declared_vs_demonstrated", nombre) not in ya:
            nuevas.append(Alerta(
                id=f"a-{uuid.uuid4().hex[:6]}", type="declared_vs_demonstrated", field=nombre,
                message=f"Declarado '{campo.declared}' frente a demostrado '{campo.value}'.",
                evidence=campo.evidence,
            ))
    return nuevas
