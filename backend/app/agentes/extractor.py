"""Agente extractor (B1). Convierte los turnos de la entrevista en parches del perfil.

Reparto del trabajo (contrato 04 y docs/REPARTO.md):
- Claude LEE: devuelve, con salida estructurada, qué datos aparecen, en qué turno, con qué cita literal,
  y categorías cerradas (certeza, resultado de una comprobación, reacción ante una caída).
- El CÓDIGO DECIDE, de forma determinista y testeable:
  1. la cita existe de verdad en un turno del cliente (si no, se descarta: nada inventado);
  2. tiempos de la evidencia, tomados del turno;
  3. valor demostrado, confianza y `low_confidence`, con la rúbrica fija de `rubrica.py`;
  4. no pisar un dato corregido por el asesor, ni uno demostrado con uno solo declarado,
     ni reescribir lo mismo (evita versiones vacías).
- Nunca escribe datos calculados (`CALCULADOS`): los pone `calculos.py`.

El resultado pasa además por `store` (`validacion.comprobar_parche`): tipos, autoría y evidencia.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..perfil.modelos import CALCULADOS, CAMPOS, FAMILIAS, Evidencia, Fact, Flag, Fuente, Parche, Perfil, Turno
from ..perfil.validacion import TIPOS
from . import claude, rubrica

log = logging.getLogger("perfil.extractor")

AGENTE = "extractor"
RUTA_ESCENARIO = "risk_tolerance.scenario_score"

# Campos que el modelo puede rellenar como «dato» (los de conocimiento y el escenario van aparte).
CAMPOS_DATO: list[str] = [
    c for c in CAMPOS
    if c not in CALCULADOS and not c.startswith("knowledge.") and c != RUTA_ESCENARIO
]

CampoDato = Literal[tuple(CAMPOS_DATO)]  # type: ignore[valid-type]
Familia = Literal[tuple(FAMILIAS)]  # type: ignore[valid-type]


# ---------- salida estructurada que se pide al modelo ----------

class DatoExtraido(BaseModel):
    campo: CampoDato = Field(description="Ruta del dato en el catálogo")
    valor: str = Field(description="Valor en el formato del catálogo (número sin unidades, true/false u opción)")
    certeza: rubrica.Certeza = Field(description="explicita: lo dijo tal cual; aproximada: «unos», «más o menos»; inferida: se deduce")
    turn_id: str = Field(description="turn_id del turno del CLIENTE del que sale")
    cita: str = Field(description="Fragmento copiado literalmente de ese turno del cliente")


class ConocimientoExtraido(BaseModel):
    familia: Familia
    nivel_declarado: rubrica.Nivel | None = Field(description="Lo que el cliente dice saber (o marcó en un test previo); null si no lo dijo")
    resultado_comprobacion: rubrica.Resultado | None = Field(
        description="Resultado de la respuesta del cliente a una pregunta de comprobación sobre esta familia; null si no hubo")
    turn_id: str = Field(description="turn_id del turno del CLIENTE que lo justifica (la respuesta a la comprobación si la hubo)")
    cita: str = Field(description="Fragmento copiado literalmente de ese turno del cliente")


class EscenarioExtraido(BaseModel):
    reaccion: rubrica.Reaccion
    certeza: rubrica.Certeza
    puntuacion_declarada: int | None = Field(description="Tolerancia 1-5 que el cliente se atribuyó antes (p. ej. en un test previo); null si no")
    turn_id: str
    cita: str


class Extraccion(BaseModel):
    datos: list[DatoExtraido]
    conocimientos: list[ConocimientoExtraido]
    escenario: EscenarioExtraido | None


# ---------- prompt ----------

@lru_cache(maxsize=1)
def _sistema() -> str:
    return (Path(__file__).parent / "prompts" / "extractor.md").read_text(encoding="utf-8")


def _catalogo() -> str:
    lineas = []
    for c in CAMPOS_DATO:
        tipo, opciones = TIPOS[c]
        detalle = {
            "bool": "true|false", "eur": "número en euros", "anios": "número de años", "pct": "porcentaje 0-100",
            "entero": "entero", "texto": "texto breve", "sfdr": "6|8|9",
        }.get(tipo, "|".join(opciones) if opciones else tipo)
        lineas.append(f"- {c}: {detalle}")
    return "\n".join(lineas)


def _estado(perfil: Perfil) -> str:
    if not perfil.mifid:
        return "(vacío)"
    return "\n".join(
        f"- {ruta} = {json.dumps(f.value, ensure_ascii=False)} ({f.source.value})"
        for ruta, f in sorted(perfil.mifid.items())
    )


def mensaje(turnos: list[Turno], perfil: Perfil) -> str:
    conversacion = "\n".join(
        json.dumps({"turn_id": t.turn_id, "speaker": t.speaker, "text": t.text}, ensure_ascii=False) for t in turnos
    )
    return (
        f"## Catálogo de datos\n{_catalogo()}\n\n"
        f"Familias de conocimiento: {', '.join(FAMILIAS)}\n\n"
        f"## Perfil actual\n{_estado(perfil)}\n\n"
        f"## Turnos recientes (JSON por línea)\n{conversacion}\n"
    )


# ---------- comprobaciones deterministas ----------

def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto).casefold()
    texto = re.sub(r"[«»\"“”'‘’.,;:¡!¿?()\-–—…]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def cita_valida(cita: str, texto: str) -> bool:
    """La cita es un fragmento real del turno (ignorando mayúsculas, puntuación y espacios)."""
    c = _normalizar(cita)
    return len(c) >= 2 and c in _normalizar(texto)


_BOOL = {"true": True, "false": False, "sí": True, "si": True, "no": False}


def convertir(campo: str, valor: str):
    """Texto del modelo → tipo del catálogo. Lanza ValueError si no encaja (el dato se descarta)."""
    tipo = TIPOS[campo][0]
    v = valor.strip()
    if tipo == "bool":
        if v.casefold() not in _BOOL:
            raise ValueError(f"{campo}: {valor!r} no es true/false")
        return _BOOL[v.casefold()]
    if tipo in ("eur", "anios", "pct"):
        return float(v.replace("€", "").replace("%", "").replace(" ", "").replace(",", "."))
    if tipo in ("entero", "sfdr"):
        return int(float(v))
    return v


def _protegido(actual: Fact | None, fuente: str, valor, confianza: float) -> bool:
    """True si el parche nuevo no debe escribirse sobre el dato actual."""
    if actual is None:
        return False
    if actual.source == Fuente.advisor:
        return True  # lo corrigió una persona de la entidad
    if actual.source == Fuente.demonstrated and fuente == Fuente.declared.value:
        return True  # lo demostrado manda sobre lo declarado
    return actual.value == valor and actual.source.value == fuente and (actual.confidence or 0) >= confianza


def _parche(ruta: str, valor, fuente: str, confianza: float, base: str, turno: Turno, cita: str,
            session_id: str, declarado=None) -> Parche:
    flags = [Flag.low_confidence] if rubrica.baja(confianza) else []
    return Parche(
        path=ruta, value=valor, source=Fuente(fuente), declared=declarado,
        confidence=confianza, confidence_basis=base, flags=flags,
        evidence=[Evidencia(session_id=session_id, turn_id=turno.turn_id, t=(turno.t_start, turno.t_end), quote=cita.strip())],
    )


def a_parches(extraccion: Extraccion, turnos: list[Turno], perfil: Perfil, session_id: str) -> list[Parche]:
    """Parte determinista: de la salida del modelo a parches seguros. Pública para poder testearla."""
    del_cliente = {t.turn_id: t for t in turnos if t.speaker == "client" and t.turn_id}
    salida: dict[str, Parche] = {}

    def turno_citado(turn_id: str, cita: str, ruta: str) -> Turno | None:
        turno = del_cliente.get(turn_id)
        if turno is None:
            log.debug("descartado %s: el turno %s no es del cliente o no está en la ventana", ruta, turn_id)
            return None
        if not cita_valida(cita, turno.text):
            log.warning("descartado %s: la cita no aparece literalmente en %s", ruta, turn_id)
            return None
        return turno

    def poner(p: Parche) -> None:
        previo = salida.get(p.path)
        # Si el modelo repite un campo, gana lo demostrado y, a igualdad, lo más reciente.
        if previo and previo.source == Fuente.demonstrated and p.source == Fuente.declared:
            return
        if not _protegido(perfil.mifid.get(p.path), p.source.value, p.value, p.confidence or 0):
            salida[p.path] = p

    for d in extraccion.datos:
        turno = turno_citado(d.turn_id, d.cita, d.campo)
        if turno is None:
            continue
        try:
            valor = convertir(d.campo, d.valor)
        except ValueError as e:
            log.info("descartado %s: %s", d.campo, e)
            continue
        confianza, base = rubrica.dato_declarado(d.certeza)
        fuente = Fuente.demonstrated.value if d.campo == "risk_tolerance.past_behaviour" else Fuente.declared.value
        poner(_parche(d.campo, valor, fuente, confianza, base, turno, d.cita, session_id))

    for k in extraccion.conocimientos:
        ruta = f"knowledge.{k.familia}"
        turno = turno_citado(k.turn_id, k.cita, ruta)
        if turno is None:
            continue
        valor, fuente, confianza, base = rubrica.conocimiento(ruta, k.nivel_declarado, k.resultado_comprobacion)
        if valor is None:
            continue
        declarado = k.nivel_declarado if fuente == Fuente.demonstrated.value else None
        poner(_parche(ruta, valor, fuente, confianza, base, turno, k.cita, session_id, declarado))

    e = extraccion.escenario
    if e is not None:
        turno = turno_citado(e.turn_id, e.cita, RUTA_ESCENARIO)
        if turno is not None:
            puntuacion, confianza, base = rubrica.escenario(e.reaccion, e.certeza)
            declarada = e.puntuacion_declarada if e.puntuacion_declarada in range(1, 6) else None
            poner(_parche(RUTA_ESCENARIO, puntuacion, Fuente.demonstrated.value, confianza, base, turno,
                          e.cita, session_id, declarada))

    return list(salida.values())


_aviso_sin_clave = False


async def extraer(turnos: list[Turno], perfil: Perfil, session_id: str) -> list[Parche]:
    """Turnos recientes + perfil actual → parches. Sin clave de Anthropic devuelve [] (modo demo)."""
    global _aviso_sin_clave
    if not any(t.speaker == "client" for t in turnos):
        return []
    if not claude.disponible():
        if not _aviso_sin_clave:
            log.warning("Extractor desactivado: falta ANTHROPIC_API_KEY")
            _aviso_sin_clave = True
        return []
    extraccion, _uso = await claude.estructurado(
        agente=AGENTE, sistema=_sistema(), mensaje=mensaje(turnos, perfil), esquema=Extraccion,
    )
    return a_parches(extraccion, turnos, perfil, session_id)
