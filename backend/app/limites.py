"""Límites de uso para un despliegue público: que nadie gaste los créditos de Claude y ElevenLabs.

Todos están apagados por defecto (0 = sin límite), así que en local y en los tests no cambia nada.
En producción se fijan por variable de entorno:

- `LIMITE_SESIONES_DIA`: entrevistas nuevas al día, entre todos los visitantes.
- `LIMITE_VOZ_DIA`: conexiones de voz al día (cada una abre una llamada de ElevenLabs).
- `LIMITE_TURNOS_SESION`: mensajes del cliente por entrevista (acota lo que cuesta cada una en Claude).

Los contadores viven en memoria del proceso y se reinician cada día (UTC) o al reiniciar el servidor.
Es un tope de gasto para una demo pública, no un control antiabuso por persona.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone

from fastapi import HTTPException

MENSAJE = ("Hoy ya se han hecho todas las entrevistas de prueba de esta demo pública. "
           "Puedes ver la demo guiada o volver mañana.")

_candado = threading.Lock()
_dia: str | None = None
_usados: dict[str, int] = {}


def _limite(variable: str) -> int:
    try:
        return max(0, int(os.getenv(variable, "0") or 0))
    except ValueError:
        return 0


def _hoy() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def consumir(tipo: str, variable: str) -> None:
    """Cuenta un uso de `tipo`; si ya se llegó al límite del día, responde 429 sin contarlo."""
    global _dia
    limite = _limite(variable)
    if not limite:
        return
    with _candado:
        if _dia != _hoy():
            _usados.clear()
            _dia = _hoy()
        if _usados.get(tipo, 0) >= limite:
            raise HTTPException(429, MENSAJE, headers={"Retry-After": "3600"})
        _usados[tipo] = _usados.get(tipo, 0) + 1


def comprobar_turnos(turnos_cliente: int) -> None:
    """429 si la entrevista ya tiene todos los mensajes del cliente permitidos."""
    limite = _limite("LIMITE_TURNOS_SESION")
    if limite and turnos_cliente >= limite:
        raise HTTPException(429, "Esta entrevista de prueba ha llegado a su límite de mensajes.")


def reiniciar() -> None:
    """Solo para tests."""
    global _dia
    with _candado:
        _dia = None
        _usados.clear()
