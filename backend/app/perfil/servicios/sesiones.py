"""Sesiones de entrevista y su transcripción (de solo añadir)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from ..dominio.errores import CampoInvalido, EscrituraNoPermitida, NoEncontrado
from ..dominio.modelos import AUTOR_SISTEMA, EstadoPerfil, Turno, ahora
from ..persistencia.repositorio import Repositorio
from .perfiles import ServicioPerfiles

CANALES = ("voice", "text")


class ServicioSesiones:
    def __init__(self, repo: Repositorio, perfiles: ServicioPerfiles, reloj: Callable = ahora):
        self.repo = repo
        self.perfiles = perfiles
        self._reloj = reloj

    def crear(self, client_id: str | None = None, canal: str = "voice") -> dict[str, Any]:
        """Empieza una entrevista. Si el perfil estaba pendiente de revisión, vuelve a borrador."""
        if canal not in CANALES:
            raise CampoInvalido(f"Canal {canal!r} no válido: {list(CANALES)}")
        p = self.perfiles.crear(client_id)
        if p.status == EstadoPerfil.review_due:
            p = self.perfiles.reabrir(p.client_id, AUTOR_SISTEMA)
        sid, momento = f"s-{uuid.uuid4().hex[:12]}", self._reloj()
        self.repo.crear_sesion(sid, p.client_id, canal, momento)
        return {"session_id": sid, "client_id": p.client_id, "channel": canal, "started_at": momento}

    def _sesion(self, session_id: str) -> dict[str, Any]:
        s = self.repo.sesion(session_id)
        if s is None:
            raise NoEncontrado(f"sesión {session_id}")
        return s

    def sesion(self, session_id: str) -> dict[str, Any]:
        s = self._sesion(session_id)
        return {**s, "turns": [t.model_dump() for t in self.repo.turnos(session_id)]}

    def turnos(self, session_id: str) -> list[Turno]:
        self._sesion(session_id)
        return self.repo.turnos(session_id)

    def anadir_turno(self, session_id: str, turno: Turno) -> tuple[int, bool]:
        """Devuelve (índice, es_nuevo). Con turn_id, reenviar el mismo turno no lo duplica."""
        if self._sesion(session_id)["ended_at"] is not None:
            raise EscrituraNoPermitida(f"La sesión {session_id} ya terminó")
        if turno.turn_id is None:
            turno = turno.model_copy(update={"turn_id": f"t-{uuid.uuid4().hex[:12]}"})
        return self.repo.insertar_turno(session_id, turno, self._reloj())

    def cerrar(self, session_id: str, conversation_id: str | None = None) -> dict[str, Any]:
        if self._sesion(session_id)["ended_at"] is None:
            self.repo.cerrar_sesion(session_id, self._reloj(), conversation_id)
        return self._sesion(session_id)
