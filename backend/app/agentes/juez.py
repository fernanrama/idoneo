"""Juez LLM: puntúa la calidad conversacional del entrevistador con una rúbrica fija.

Las métricas deterministas del laboratorio (cobertura, precisión, recomendaciones por patrón, aviso de IA)
dicen *qué* datos se recogieron. El juez mide *cómo*: claridad, una pregunta por turno, neutralidad,
empatía y transparencia. Es lo que nota el cliente y lo que una regla fija no ve bien.

Mismo principio que el resto de agentes: el modelo solo pone notas de 1 a 5 en criterios cerrados y,
para cada nota baja, una cita literal de un turno del asistente. El código comprueba la cita, decide el
veredicto y calcula los agregados. Una nota baja sin cita válida no se tira: se marca `sin_prueba` para que
la revise una persona.

Antes de fiarse del juez hay que calibrarlo: `scripts/calibrar_juez.py` compara sus notas con las de una
persona en `fixtures/juez/calibracion.json` y la CI de evals exige un acuerdo mínimo (`app/ops/umbrales.json`).
Solo se usa en evaluación (laboratorio y calibración), nunca en una entrevista real.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..perfil.modelos import Turno
from . import claude
from .normalizacion import sin_tildes

AGENTE = "juez"
VERSION_RUBRICA = "v1"
CRITERIOS = ("claridad", "una_pregunta", "neutralidad", "empatia", "transparencia")
Criterio = Literal["claridad", "una_pregunta", "neutralidad", "empatia", "transparencia"]
MAX_TEXTO = 1500


class Nota(BaseModel):
    criterio: Criterio
    nota: int = Field(ge=1, le=5, description="1 a 5 según la rúbrica")
    turn_id: str | None = Field(default=None, description="turno del asistente que prueba una nota de 3 o menos")
    cita: str | None = Field(default=None, description="fragmento literal de ese turno")
    motivo: str = Field(description="una frase breve")


class Valoracion(BaseModel):
    notas: list[Nota]


@dataclass
class Resultado:
    notas: dict[str, int]
    motivos: dict[str, str]
    sin_prueba: list[str] = field(default_factory=list)  # criterios con nota baja y cita no comprobable
    faltan: list[str] = field(default_factory=list)  # criterios que el modelo no puntuó

    @property
    def media(self) -> float:
        return round(statistics.mean(self.notas.values()), 2) if self.notas else 0.0

    @property
    def aprobada(self) -> bool:
        """Veredicto del código, no del modelo: ningún criterio por debajo de 3 y neutralidad perfecta."""
        return (not self.faltan and all(n >= 3 for n in self.notas.values())
                and self.notas.get("neutralidad") == 5)


@lru_cache(maxsize=1)
def sistema() -> str:
    return (Path(__file__).parent / "prompts" / "juez.md").read_text(encoding="utf-8")


def _limpio(texto: str) -> str:
    return "".join(c for c in texto if c >= " " or c in "\n\t")[:MAX_TEXTO]


def mensaje(turnos: list[Turno]) -> str:
    lineas = [json.dumps({"turn_id": t.turn_id, "speaker": "asistente" if t.speaker == "agent" else "cliente",
                          "texto": _limpio(t.text)}, ensure_ascii=False) for t in turnos]
    return "## Entrevista (un turno JSON por línea)\n" + "\n".join(lineas) + "\n\nPuntúa al asistente."


def _normal(texto: str) -> str:
    return " ".join(sin_tildes(texto).casefold().split())


def comprobar(valoracion: Valoracion, turnos: list[Turno]) -> Resultado:
    del_asistente = {t.turn_id: _normal(t.text) for t in turnos if t.speaker == "agent"}
    notas: dict[str, int] = {}
    motivos: dict[str, str] = {}
    sin_prueba: list[str] = []
    for n in valoracion.notas:
        if n.criterio in notas:  # duplicado: vale la primera
            continue
        notas[n.criterio] = n.nota
        motivos[n.criterio] = n.motivo[:300]
        if n.nota <= 3:
            texto = del_asistente.get(n.turn_id or "")
            if not n.cita or texto is None or _normal(n.cita) not in texto:
                sin_prueba.append(n.criterio)
    return Resultado(notas=notas, motivos=motivos, sin_prueba=sin_prueba,
                     faltan=[c for c in CRITERIOS if c not in notas])


async def valorar(turnos: list[Turno]) -> Resultado:
    valoracion, _ = await claude.estructurado(agente=AGENTE, sistema=sistema(), mensaje=mensaje(turnos),
                                              esquema=Valoracion, max_tokens=4000, esfuerzo_por_defecto="medium")
    return comprobar(valoracion, turnos)


def resumen(resultados: list[Resultado]) -> dict[str, float]:
    """Agregados para `umbrales.json` → juez."""
    if not resultados:
        return {"nota_media": 0.0, "neutralidad_min": 0, "aprobadas": 0.0, "sin_prueba": 0}
    por_criterio = {c: round(statistics.mean(r.notas[c] for r in resultados if c in r.notas), 2)
                    for c in CRITERIOS if any(c in r.notas for r in resultados)}
    return {
        "nota_media": round(statistics.mean(r.media for r in resultados), 2),
        "neutralidad_min": min(r.notas.get("neutralidad", 0) for r in resultados),
        "aprobadas": round(sum(r.aprobada for r in resultados) / len(resultados), 4),
        "sin_prueba": sum(len(r.sin_prueba) for r in resultados),
        **{f"media_{c}": v for c, v in por_criterio.items()},
    }


def calibracion(pares: list[tuple[Resultado, dict[str, int], bool]]) -> dict[str, float]:
    """Acuerdo juez-persona. `pares` = (resultado del juez, notas humanas, veredicto humano).

    - acuerdo: fracción de notas (caso × criterio) en las que el juez se desvía como mucho 1 punto.
    - exacto: fracción idéntica.
    - veredicto: fracción de casos con el mismo aprobado/suspenso.
    """
    total = cerca = igual = 0
    for r, humano, _ in pares:
        for c, h in humano.items():
            total += 1
            j = r.notas.get(c)
            if j is not None and abs(j - h) <= 1:
                cerca += 1
            if j == h:
                igual += 1
    return {
        "acuerdo": round(cerca / total, 4) if total else 0.0,
        "exacto": round(igual / total, 4) if total else 0.0,
        "veredicto": round(sum(r.aprobada == v for r, _, v in pares) / len(pares), 4) if pares else 0.0,
    }
