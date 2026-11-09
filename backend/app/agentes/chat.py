"""Entrevistador en modo texto (B1): la misma entrevista que el agente de voz, sin ElevenLabs.

Usa el mismo prompt (`prompts/entrevistador.md`, la parte tras `---`) y le añade lo que aún falta en el
perfil, para que dirija la conversación hacia los datos pendientes o poco fiables. El perfil lo siguen
escribiendo el extractor y el verificador a partir de los turnos, igual que en la voz.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from ..perfil.modelos import OBLIGATORIOS, Flag, Fuente, Perfil, Turno
from . import claude

AGENTE = "entrevistador"
ETIQUETA_HABLANTE = {"agent": "Asistente", "client": "Cliente"}


class Respuesta(BaseModel):
    texto: str = Field(description="Lo que dice el asistente al cliente: una sola pregunta o el cierre")
    terminada: bool = Field(description="true solo al despedirse (entrevista completa, el cliente no consiente o quiere parar)")


@lru_cache(maxsize=1)
def _sistema() -> str:
    texto = (Path(__file__).parent / "prompts" / "entrevistador.md").read_text(encoding="utf-8")
    return texto.split("\n---\n", 1)[-1].strip()


def pendientes(perfil: Perfil) -> list[str]:
    """Qué falta o hay que repreguntar, en el orden del guion. Determinista."""
    faltan = [c for c in OBLIGATORIOS if c not in perfil.mifid or perfil.mifid[c].value is None]
    # «No sé qué es un ETF» no se comprueba: no hay nada que verificar y alarga la entrevista.
    no_lo_conoce = {c for c, f in perfil.mifid.items()
                    if c.startswith("knowledge.") and f.source == Fuente.declared and f.value == "none"}
    dudosos = [c for c, f in perfil.mifid.items() if Flag.low_confidence in f.flags and c not in no_lo_conoce]
    sin_comprobar = [c for c, f in perfil.mifid.items()
                     if c.startswith("knowledge.") and f.source == Fuente.declared and c not in no_lo_conoce]
    vistos: set[str] = set()
    return [c for c in faltan + dudosos + sin_comprobar if not (c in vistos or vistos.add(c))]


def mensaje(turnos: list[Turno], perfil: Perfil) -> str:
    conversacion = "\n".join(f"{ETIQUETA_HABLANTE[t.speaker]}: {t.text}" for t in turnos) or "(aún no ha empezado)"
    pend = "\n".join(f"- {c}" for c in pendientes(perfil)) or "- nada: puedes cerrar la entrevista"
    return (
        f"## Conversación hasta ahora\n{conversacion}\n\n"
        f"## Datos pendientes o que conviene repreguntar (rutas internas, no las digas)\n{pend}\n\n"
        "Escribe el siguiente mensaje del asistente."
    )


async def responder(turnos: list[Turno], perfil: Perfil) -> Respuesta:
    salida, _uso = await claude.estructurado(
        agente=AGENTE, sistema=_sistema(), mensaje=mensaje(turnos, perfil), esquema=Respuesta,
        max_tokens=4000, esfuerzo_por_defecto="low",
    )
    return salida
