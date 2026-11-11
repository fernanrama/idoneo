"""Trazas de ejecución: qué hizo cada agente, cuánto tardó y cuánto costó.

Una **ejecución** es una unidad de trabajo completa: procesar un turno del cliente (extractor + verificador)
o una respuesta del entrevistador en modo texto. Dentro de cada ejecución, cada llamada a Claude es una
**llamada** con su agente, modelo, versión del prompt, tokens, latencia, coste estimado y resultado.

Qué NO se guarda: ni texto del cliente ni respuestas del modelo. Solo recuentos, tiempos y versiones,
igual que los logs del resto del backend. Así las trazas se pueden enseñar en un panel sin exponer datos
personales.

Almacenamiento: un búfer en memoria con las últimas `TRAZAS_MAX` ejecuciones (2.000 por defecto) y, si se
define `TRAZAS_ARCHIVO`, una línea JSON por ejecución terminada. Ese archivo se puede cargar en cualquier
herramienta de observabilidad (Langfuse, LangSmith, una hoja de cálculo) sin tocar el código.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import statistics
import threading
import time
import uuid
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

log = logging.getLogger("perfil.trazas")

# ---------- precios ----------

# Dólares por millón de tokens, tarifa de la API de Anthropic (consultada el 2026-11-03).
# Entrada normal, entrada leída de la caché, entrada escrita en la caché (5 min, 1,25×) y salida.
# Es una ESTIMACIÓN para comparar versiones y vigilar desvíos: la factura real es la fuente de verdad.
PRECIOS: dict[str, dict[str, float]] = {
    "claude-opus-5-5": {"entrada": 4.00, "cache_leida": 0.20, "cache_escrita": 5.00, "salida": 20.00},
    "claude-sonnet-5-5": {"entrada": 2.00, "cache_leida": 0.10, "cache_escrita": 2.50, "salida": 10.00},
    "claude-sonnet-5": {"entrada": 2.00, "cache_leida": 0.20, "cache_escrita": 2.50, "salida": 10.00},
    "claude-haiku-5-5": {"entrada": 0.10, "cache_leida": 0.01, "cache_escrita": 0.125, "salida": 0.50},
}
PRECIO_DESCONOCIDO = PRECIOS["claude-sonnet-5-5"]


def coste_usd(modelo: str, entrada: int, cache_leida: int, cache_escrita: int, salida: int) -> float:
    p = PRECIOS.get(modelo, PRECIO_DESCONOCIDO)
    return round((entrada * p["entrada"] + cache_leida * p["cache_leida"] + cache_escrita * p["cache_escrita"]
                  + salida * p["salida"]) / 1_000_000, 6)


def version_prompt(sistema: str) -> str:
    """Huella corta del prompt de sistema: cambia en cuanto cambia una coma del prompt.

    Permite comparar métricas antes y después de tocar un prompt sin llevar un registro aparte.
    """
    return hashlib.sha256(sistema.encode("utf-8")).hexdigest()[:10]


# ---------- modelo de datos ----------

@dataclass
class Llamada:
    agente: str
    modelo: str
    prompt: str
    inicio: str
    latencia_s: float
    tokens_entrada: int = 0
    tokens_cache_leidos: int = 0
    tokens_cache_escritos: int = 0
    tokens_salida: int = 0
    coste_usd: float = 0.0
    resultado: str = "ok"  # ok | rechazo | cortada | sin_salida | error


@dataclass
class Ejecucion:
    id: str
    tipo: str  # turno | chat | evaluacion | laboratorio
    sesion: str | None
    inicio: str
    duracion_s: float = 0.0
    estado: str = "en_curso"  # en_curso | ok | error
    llamadas: list[Llamada] = field(default_factory=list)
    resultado: dict[str, Any] = field(default_factory=dict)  # recuentos: parches, alertas, rechazos…

    @property
    def coste_usd(self) -> float:
        return round(sum(c.coste_usd for c in self.llamadas), 6)

    def a_dict(self, con_sesion: bool = True) -> dict[str, Any]:
        d = asdict(self)
        d["coste_usd"] = self.coste_usd
        d["tokens"] = sum(c.tokens_entrada + c.tokens_cache_leidos + c.tokens_cache_escritos + c.tokens_salida
                          for c in self.llamadas)
        if not con_sesion:
            d.pop("sesion", None)
        return d


# ---------- almacén ----------

_actual: ContextVar[Ejecucion | None] = ContextVar("ejecucion_actual", default=None)
_candado = threading.Lock()
_ejecuciones: deque[Ejecucion] = deque(maxlen=int(os.getenv("TRAZAS_MAX", "2000")))
_sueltas: deque[Llamada] = deque(maxlen=int(os.getenv("TRAZAS_MAX", "2000")))  # llamadas fuera de una ejecución


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _volcar(e: Ejecucion) -> None:
    ruta = os.getenv("TRAZAS_ARCHIVO", "").strip()
    if not ruta:
        return
    try:
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e.a_dict(), ensure_ascii=False) + "\n")
    except OSError:
        log.warning("No se pudo escribir la traza en %s", ruta, exc_info=True)


@contextmanager
def ejecucion(tipo: str, sesion: str | None = None) -> Iterator[Ejecucion]:
    """Agrupa todas las llamadas a Claude que ocurran dentro del bloque (también en corrutinas)."""
    e = Ejecucion(id=uuid.uuid4().hex[:12], tipo=tipo, sesion=sesion, inicio=_ahora())
    with _candado:
        _ejecuciones.append(e)
    token = _actual.set(e)
    t0 = time.perf_counter()
    try:
        yield e
        e.estado = "ok"
    except BaseException:
        e.estado = "error"
        raise
    finally:
        e.duracion_s = round(time.perf_counter() - t0, 3)
        _actual.reset(token)
        _volcar(e)


def registrar_llamada(llamada: Llamada) -> None:
    e = _actual.get()
    with _candado:
        if e is not None:
            e.llamadas.append(llamada)
        else:
            _sueltas.append(llamada)


def reiniciar() -> None:
    with _candado:
        _ejecuciones.clear()
        _sueltas.clear()


# ---------- consultas ----------

def _p(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, round(q * (len(xs) - 1)))], 3)


def _copia() -> tuple[list[Ejecucion], list[Llamada]]:
    with _candado:
        return list(_ejecuciones), list(_sueltas)


def resumen() -> dict[str, Any]:
    """Agregado para el panel: por agente, por tipo de ejecución y por versión de prompt. Sin datos personales."""
    ejecuciones, sueltas = _copia()
    terminadas = [e for e in ejecuciones if e.estado != "en_curso"]
    llamadas = [c for e in ejecuciones for c in e.llamadas] + sueltas

    por_agente: dict[str, dict[str, Any]] = {}
    for agente in sorted({c.agente for c in llamadas}):
        cs = [c for c in llamadas if c.agente == agente]
        lat = [c.latencia_s for c in cs if c.resultado != "error"]
        entrada = sum(c.tokens_entrada for c in cs)
        leidos = sum(c.tokens_cache_leidos for c in cs)
        escritos = sum(c.tokens_cache_escritos for c in cs)
        total_entrada = entrada + leidos + escritos
        fallos = sum(1 for c in cs if c.resultado != "ok")
        por_agente[agente] = {
            "llamadas": len(cs),
            "fallos": fallos,
            "tasa_fallo": round(fallos / len(cs), 4),
            "latencia_p50_s": _p(lat, 0.5),
            "latencia_p95_s": _p(lat, 0.95),
            "tokens_entrada": total_entrada,
            "tokens_salida": sum(c.tokens_salida for c in cs),
            "tasa_cache": round(leidos / total_entrada, 4) if total_entrada else 0.0,
            "coste_usd": round(sum(c.coste_usd for c in cs), 6),
            "coste_medio_usd": round(sum(c.coste_usd for c in cs) / len(cs), 6),
            "modelos": sorted({c.modelo for c in cs}),
            "versiones_prompt": sorted({c.prompt for c in cs}),
        }

    por_tipo: dict[str, dict[str, Any]] = {}
    for tipo in sorted({e.tipo for e in terminadas}):
        es = [e for e in terminadas if e.tipo == tipo]
        dur = [e.duracion_s for e in es]
        por_tipo[tipo] = {
            "ejecuciones": len(es),
            "errores": sum(1 for e in es if e.estado == "error"),
            "duracion_p50_s": _p(dur, 0.5),
            "duracion_p95_s": _p(dur, 0.95),
            "llamadas_media": round(statistics.mean(len(e.llamadas) for e in es), 2),
            "coste_medio_usd": round(statistics.mean(e.coste_usd for e in es), 6),
        }

    por_prompt: dict[str, dict[str, Any]] = {}
    for c in llamadas:
        k = f"{c.agente}@{c.prompt}"
        d = por_prompt.setdefault(k, {"agente": c.agente, "version": c.prompt, "llamadas": 0, "fallos": 0, "_lat": []})
        d["llamadas"] += 1
        d["fallos"] += c.resultado != "ok"
        if c.resultado != "error":
            d["_lat"].append(c.latencia_s)
    for d in por_prompt.values():
        d["latencia_p50_s"] = _p(d.pop("_lat"), 0.5)

    return {
        "generado": _ahora(),
        "totales": {
            "ejecuciones": len(terminadas),
            "llamadas": len(llamadas),
            "fallos": sum(1 for c in llamadas if c.resultado != "ok"),
            "coste_usd": round(sum(c.coste_usd for c in llamadas), 6),
            "tokens": sum(c.tokens_entrada + c.tokens_cache_leidos + c.tokens_cache_escritos + c.tokens_salida
                          for c in llamadas),
        },
        "por_agente": por_agente,
        "por_tipo": por_tipo,
        "por_version_prompt": sorted(por_prompt.values(), key=lambda d: (d["agente"], d["version"])),
        "recientes": [e.a_dict(con_sesion=False) for e in reversed(terminadas[-20:])],
        "aviso": "Costes estimados a partir de los tokens y la tarifa pública; la factura es la fuente de verdad.",
    }


def de_sesion(sesion: str, limite: int = 100) -> list[dict[str, Any]]:
    ejecuciones, _ = _copia()
    return [e.a_dict() for e in ejecuciones if e.sesion == sesion][-limite:]
