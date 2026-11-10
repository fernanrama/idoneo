"""Laboratorio de entrevistas (B1/B2): el sistema entero frente a clientes simulados, sin voz.

Claude hace de cliente con una ficha oculta (`fixtures/laboratorio/*.json`) y habla por texto con el
entrevistador real; cada turno del cliente pasa por el extractor y el verificador como en producción.
Al final se puntúa el perfil contra la ficha (`evaluacion.puntuar`) y se miden cosas que la batería del
extractor no ve: si el asistente avisa de que es una IA, si comprueba conocimientos, si cierra, cuántos
turnos necesita, si se le escapa una recomendación y qué queda pendiente.

No usa ElevenLabs ni el MCP de MyInvestor. Lo ejecuta `scripts/laboratorio.py`.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable

from ..perfil.modelos import Fuente, Turno
from . import chat, cliente_simulado, evaluacion, guardas
from .normalizacion import sin_tildes

CARPETA = Path(__file__).resolve().parents[2] / "fixtures" / "laboratorio"
MAX_TURNOS = 40  # intervenciones del asistente: corta una entrevista que no avanza
_RECOMIENDA = re.compile(r"\b(le|te) (recomiendo|aconsejo|sugiero que invierta)|deberia invertir|le conviene (comprar|invertir)")


@dataclass
class Persona:
    caso: evaluacion.Caso
    ficha: str
    alertas: list[str] = field(default_factory=list)


@dataclass
class Informe:
    persona: str
    resultado: evaluacion.Resultado
    turnos: list[Turno]
    terminada: bool
    aviso_ia_al_inicio: bool
    preguntas_dobles: int  # turnos del asistente con más de una pregunta
    recomendaciones: int  # turnos del asistente que suenan a recomendación (prohibido)
    comprobados: list[str]  # familias con conocimiento demostrado
    alertas_esperadas: dict[str, bool]
    pendientes: list[str]
    # Alertas que salieron sin estar en la ficha: no son por fuerza falsas alarmas, pero hay que mirarlas.
    otras_alertas: list[str] = field(default_factory=list)

    @property
    def intervenciones(self) -> int:
        return sum(1 for t in self.turnos if t.speaker == "agent")


def cargar(ruta: Path) -> Persona:
    d = json.loads(ruta.read_text("utf-8"))
    caso = evaluacion.Caso(
        nombre=d.get("nombre", ruta.stem), que_prueba=d.get("que_prueba", ""), turnos=[],
        esperado=d.get("esperado", {}), prohibido=d.get("prohibido", []),
        prohibido_valores=d.get("prohibido_valores", {}),
    )
    return Persona(caso=caso, ficha=d["ficha"], alertas=d.get("alertas", []))


def personas(carpeta: Path = CARPETA) -> list[Persona]:
    return [cargar(p) for p in sorted(carpeta.glob("*.json"))]


def _preguntas(texto: str) -> int:
    return max(texto.count("?"), texto.count("¿"))


async def entrevistar(
    persona: Persona,
    *,
    sesion_nueva: Callable[[], str],
    anadir_turno: Callable[[str, Turno], Turno],
    procesar_turno: Callable[[str], Awaitable[None]],
    perfil: Callable[[], object],
    max_turnos: int = MAX_TURNOS,
) -> Informe:
    """Una entrevista completa. Las funciones del almacén se inyectan para poder probarlo sin Claude."""
    sid = sesion_nueva()
    turnos: list[Turno] = []
    terminada = False
    reloj = 0.0

    def nuevo(speaker: str, texto: str) -> Turno:
        nonlocal reloj
        t = anadir_turno(sid, Turno(speaker=speaker, text=texto, t_start=reloj, t_end=reloj + 1))
        reloj += 2
        turnos.append(t)
        return t

    # Como en POST /chat: el turno del cliente se procesa en segundo plano mientras el entrevistador ya
    # responde, así que este ve el perfil con un turno de retraso. Se reproduce tal cual.
    procesando: asyncio.Task | None = None
    for _ in range(max_turnos):
        r = await chat.responder(turnos[-40:], perfil())
        if procesando is not None:
            await procesando
        nuevo("agent", r.texto)
        if r.terminada:
            terminada = True
            break
        nuevo("client", await cliente_simulado.responder(persona.ficha, turnos))
        procesando = asyncio.create_task(procesar_turno(sid))
    if procesando is not None and not procesando.done():
        await procesando

    p = perfil()
    resultado = evaluacion.puntuar(persona.caso, p.mifid)
    agente = [t for t in turnos if t.speaker == "agent"]
    return Informe(
        persona=persona.caso.nombre, resultado=resultado, turnos=turnos, terminada=terminada,
        aviso_ia_al_inicio=bool(agente) and guardas.menciona_ia(agente[0].text),
        preguntas_dobles=sum(1 for t in agente if _preguntas(t.text) > 1),
        recomendaciones=sum(1 for t in agente if _RECOMIENDA.search(sin_tildes(t.text).casefold())),
        comprobados=sorted(r.removeprefix("knowledge.") for r, f in p.mifid.items()
                           if r.startswith("knowledge.") and f.source == Fuente.demonstrated),
        # Cada alerta esperada es una ruta («knowledge.equity_funds») o un flag («needs_advisor»).
        alertas_esperadas={e: any(a.path == e or a.flag.value == e for a in p.alerts) for e in persona.alertas},
        pendientes=chat.pendientes(p),
        otras_alertas=[f"{a.flag.value} en {a.path or 'sin dato'}" for a in p.alerts
                       if a.path not in persona.alertas and a.flag.value not in persona.alertas],
    )


def transcripcion(informe: Informe) -> str:
    return "\n".join(f"{'Asistente' if t.speaker == 'agent' else 'Cliente'} ({t.turn_id}): {t.text}" for t in informe.turnos)
