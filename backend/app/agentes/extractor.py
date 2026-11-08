"""Agente extractor (B1, Hammad). Convierte turnos de la entrevista en parches del perfil.

Contrato (docs/proyecto/04_CONTRATO_PERFIL.md, implementado en app/perfil/modelos.py):
- Devuelve `Parche` con `path` de `CAMPOS` (nunca de `CALCULADOS`: el store los rellena).
- Cada parche lleva evidencia: `turn_id`, `t` [inicio, fin] y cita literal del turno del cliente.
- `source="demonstrated"` solo si el cliente respondió a una pregunta de comprobación.
- `confidence` sale de una rúbrica fija (aciertos sobre preguntas de comprobación) e indica
  `confidence_basis`; nunca es la opinión del modelo. Si no llega al mínimo, añadir `low_confidence`.

v1: stub que no extrae nada, para que el resto del sistema funcione sin API.
"""

from __future__ import annotations

from ..perfil.modelos import Parche, Perfil, Turno


async def extraer(turnos: list[Turno], perfil: Perfil, session_id: str) -> list[Parche]:
    return []  # TODO Hammad: Claude con tool use (MODEL_EXTRACTOR)
