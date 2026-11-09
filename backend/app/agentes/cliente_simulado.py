"""Cliente simulado para el laboratorio (B1/B2): Claude hace de cliente con una ficha oculta.

Solo se usa en `scripts/laboratorio.py`, nunca en producción. Habla con el entrevistador real en modo
texto; al final se compara el perfil construido con lo que dice la ficha. Así se mide el sistema entero
(entrevistador + extractor + verificador) sin gastar voz ni tocar servicios de terceros.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from ..perfil.modelos import Turno
from . import claude

AGENTE = "cliente_simulado"
ETIQUETA = {"agent": "Asistente", "client": "Tú"}


class Intervencion(BaseModel):
    texto: str = Field(description="Lo que dice el cliente en su siguiente turno")


@lru_cache(maxsize=1)
def _instrucciones() -> str:
    return (Path(__file__).parent / "prompts" / "cliente_simulado.md").read_text(encoding="utf-8")


def sistema(ficha: str) -> str:
    return f"{_instrucciones()}\n\n## Tu ficha (no la reveles)\n{ficha.strip()}\n"


def mensaje(turnos: list[Turno]) -> str:
    conversacion = "\n".join(f"{ETIQUETA[t.speaker]}: {t.text}" for t in turnos)
    return f"## Conversación hasta ahora\n{conversacion}\n\nEscribe tu siguiente turno."


async def responder(ficha: str, turnos: list[Turno]) -> str:
    salida, _ = await claude.estructurado(
        agente=AGENTE, sistema=sistema(ficha), mensaje=mensaje(turnos), esquema=Intervencion,
        max_tokens=2000, esfuerzo_por_defecto="low",
    )
    return salida.texto.strip()
