"""Agente extractor (Dev B). Convierte turnos de la entrevista en actualizaciones del perfil.

Contrato: recibe los últimos turnos y el perfil vigente; devuelve ActualizacionCampo.
- Solo escribe campos de CAMPOS_MIFID. Nunca escribe campos calculados (los rellena el store).
- Cada actualización lleva evidencia: cita literal y tiempos del turno del cliente.
- source=demonstrated solo si el cliente respondió a una pregunta de comprobación.

v0: stub que no extrae nada, para que el resto del sistema funcione sin API.
"""

from __future__ import annotations

from ..perfil.modelos import ActualizacionCampo, Perfil, Turno


async def extraer(turnos: list[Turno], perfil: Perfil, session_id: str) -> list[ActualizacionCampo]:
    return []  # TODO Dev B: llamada a Claude con tool use (modelo: MODEL_EXTRACTOR)
