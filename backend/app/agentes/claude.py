"""Cliente común de Claude para los agentes (B1; lo reutiliza el verificador de B2).

Una sola puerta de entrada a la API de Anthropic, para que todos los agentes compartan:
- configuración por variables de entorno (`ANTHROPIC_API_KEY`, `MODEL_<AGENTE>`, `EFFORT_<AGENTE>`);
- salida estructurada validada con Pydantic (`messages.parse`): el modelo no puede devolver JSON roto;
- reintentos y tiempo máximo por llamada (los gestiona el SDK);
- métricas de uso por agente (llamadas, tokens, latencia) para la medición de coste y latencia de B2.

Los tests nunca llaman a la API: sustituyen `estructurado` con monkeypatch.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

log = logging.getLogger("perfil.claude")

T = TypeVar("T", bound=BaseModel)

MODELO_POR_DEFECTO = "claude-sonnet-5-5"
ESFUERZOS = {"low", "medium", "high", "xhigh", "max"}


class ClaudeNoDisponible(RuntimeError):
    """No hay credenciales de Anthropic configuradas: el agente debe degradarse sin romper nada."""


class RespuestaNoUtil(RuntimeError):
    """El modelo respondió, pero sin una salida estructurada utilizable (rechazo o corte por longitud)."""


@dataclass(frozen=True)
class Uso:
    agente: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    latencia_s: float
    tokens_cache_leidos: int = 0  # entrada servida desde la caché del prompt (cuesta ~10 %)


def disponible() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def modelo(agente: str) -> str:
    """`MODEL_EXTRACTOR`, `MODEL_VERIFICADOR`, `MODEL_ENTREVISTADOR`… con un valor por defecto común."""
    return os.getenv(f"MODEL_{agente.upper()}", "").strip() or MODELO_POR_DEFECTO


def esfuerzo(agente: str, por_defecto: str) -> str:
    valor = os.getenv(f"EFFORT_{agente.upper()}", "").strip().lower() or por_defecto
    return valor if valor in ESFUERZOS else por_defecto


_cliente = None
_candado = threading.Lock()


def _cliente_async():
    """Cliente único y perezoso: no se importa el SDK ni se exige la clave hasta la primera llamada."""
    global _cliente
    if not disponible():
        raise ClaudeNoDisponible("Falta ANTHROPIC_API_KEY en el entorno")
    with _candado:
        if _cliente is None:
            import anthropic

            _cliente = anthropic.AsyncAnthropic(
                timeout=float(os.getenv("CLAUDE_TIMEOUT_S", "60")),
                max_retries=int(os.getenv("CLAUDE_MAX_RETRIES", "2")),
            )
        return _cliente


# ---------- métricas ----------

_metricas: dict[str, dict[str, float]] = {}
_candado_metricas = threading.Lock()


def _registrar(uso: Uso) -> None:
    with _candado_metricas:
        m = _metricas.setdefault(uso.agente, {"llamadas": 0, "tokens_entrada": 0, "tokens_salida": 0,
                                               "tokens_cache_leidos": 0, "latencia_total_s": 0.0})
        m["llamadas"] += 1
        m["tokens_entrada"] += uso.tokens_entrada
        m["tokens_salida"] += uso.tokens_salida
        m["tokens_cache_leidos"] += uso.tokens_cache_leidos
        m["latencia_total_s"] += uso.latencia_s
    log.info("claude %s · %s · in=%d (caché %d) out=%d · %.2fs", uso.agente, uso.modelo, uso.tokens_entrada,
             uso.tokens_cache_leidos, uso.tokens_salida, uso.latencia_s)


def metricas() -> dict[str, dict[str, float]]:
    """Acumulado por agente desde que arrancó el proceso (para medir coste y latencia)."""
    with _candado_metricas:
        return {k: dict(v) for k, v in _metricas.items()}


def reiniciar_metricas() -> None:
    with _candado_metricas:
        _metricas.clear()


# ---------- llamada ----------

async def estructurado(
    *,
    agente: str,
    sistema: str,
    mensaje: str,
    esquema: type[T],
    max_tokens: int = 8000,
    esfuerzo_por_defecto: str = "low",
) -> tuple[T, Uso]:
    """Una petición con salida validada contra `esquema`. Devuelve el objeto y su uso.

    Lanza ClaudeNoDisponible sin clave, RespuestaNoUtil si el modelo rechaza o se corta, y deja
    pasar los errores tipados del SDK (red, 429, 5xx) tras los reintentos del propio SDK.
    El sistema va marcado para la caché del prompt: es estable entre llamadas (guion, catálogo), así que
    las siguientes llamadas del mismo agente pagan y tardan menos en esa parte.
    """
    cliente = _cliente_async()
    nombre_modelo = modelo(agente)
    inicio = time.perf_counter()
    respuesta = await cliente.messages.parse(
        model=nombre_modelo,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": sistema, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": mensaje}],
        output_format=esquema,
        output_config={"effort": esfuerzo(agente, esfuerzo_por_defecto)},
    )
    uso = Uso(
        agente=agente,
        modelo=nombre_modelo,
        tokens_entrada=getattr(respuesta.usage, "input_tokens", 0) or 0,
        tokens_salida=getattr(respuesta.usage, "output_tokens", 0) or 0,
        latencia_s=round(time.perf_counter() - inicio, 3),
        tokens_cache_leidos=getattr(respuesta.usage, "cache_read_input_tokens", 0) or 0,
    )
    _registrar(uso)
    if respuesta.stop_reason == "refusal":
        raise RespuestaNoUtil(f"{agente}: el modelo rechazó la petición")
    if respuesta.stop_reason == "max_tokens":
        raise RespuestaNoUtil(f"{agente}: respuesta cortada por max_tokens")
    salida = respuesta.parsed_output
    if salida is None:
        raise RespuestaNoUtil(f"{agente}: sin salida estructurada")
    return salida, uso
