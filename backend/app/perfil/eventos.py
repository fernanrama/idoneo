"""Bus de eventos en memoria. Base del SSE que pinta el perfil en vivo (contrato 04, "Eventos").

Sirve con un único proceso del backend. Si un suscriptor se queda atrás y su cola se llena,
se descartan eventos para él: el panel puede recuperarse releyendo el perfil.
"""

from __future__ import annotations

import queue
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evento:
    tipo: str  # profile.patch | flag.raised | profile.status
    client_id: str
    version: int
    datos: dict[str, Any] = field(default_factory=dict)


class BusEventos:
    def __init__(self, capacidad: int = 500):
        self._capacidad = capacidad
        self._suscriptores: dict[str, set[queue.Queue]] = defaultdict(set)
        self._candado = threading.Lock()

    def suscribir(self, client_id: str) -> queue.Queue:
        cola: queue.Queue = queue.Queue(maxsize=self._capacidad)
        with self._candado:
            self._suscriptores[client_id].add(cola)
        return cola

    def cancelar(self, client_id: str, cola: queue.Queue) -> None:
        with self._candado:
            self._suscriptores[client_id].discard(cola)

    def publicar(self, evento: Evento) -> None:
        with self._candado:
            colas = list(self._suscriptores.get(evento.client_id, ()))
        for cola in colas:
            try:
                cola.put_nowait(evento)
            except queue.Full:
                pass
