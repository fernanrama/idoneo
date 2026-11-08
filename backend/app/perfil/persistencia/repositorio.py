"""Acceso a datos del perfil. Solo inserta y lee versiones: nunca actualiza ni borra el registro MiFID.

La concurrencia es optimista: la clave primaria (client_id, version) impide que dos escrituras
creen la misma versión; la segunda recibe ConflictoVersion y el servicio relee y reintenta.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Engine, delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from ..dominio.errores import ConflictoVersion
from ..dominio.modelos import CapaPersonal, Perfil, Turno
from .tablas import clients, personal_versions, profile_versions, sessions, turns


def _utc(momento: datetime | None) -> datetime | None:
    """SQLite devuelve fechas sin zona; se interpretan como UTC."""
    if momento is not None and momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


class Repositorio:
    def __init__(self, motor: Engine):
        self.motor = motor

    # ---------- perfil (capa MiFID) ----------

    def crear_cliente_con_perfil(self, perfil: Perfil) -> bool:
        """Crea el cliente y su versión 1 en una transacción. False si el cliente ya existía."""
        try:
            with self.motor.begin() as c:
                c.execute(insert(clients).values(client_id=perfil.client_id, created_at=perfil.created_at))
                c.execute(insert(profile_versions).values(**self._fila_version(perfil)))
            return True
        except IntegrityError:
            return False

    def insertar_version(self, perfil: Perfil) -> None:
        try:
            with self.motor.begin() as c:
                c.execute(insert(profile_versions).values(**self._fila_version(perfil)))
        except IntegrityError as e:
            # Solo es conflicto si otra escritura ya creó esa versión; cualquier otra violación se propaga.
            if self.version(perfil.client_id, perfil.version) is not None:
                raise ConflictoVersion(f"La versión {perfil.version} de {perfil.client_id} ya existe") from e
            raise

    @staticmethod
    def _fila_version(perfil: Perfil) -> dict[str, Any]:
        return {
            "client_id": perfil.client_id,
            "version": perfil.version,
            "status": perfil.status.value,
            "reason": perfil.reason,
            "author": perfil.author,
            "snapshot": perfil.model_dump(mode="json"),
            "created_at": perfil.created_at,
        }

    def existe_cliente(self, client_id: str) -> bool:
        with self.motor.connect() as c:
            return c.execute(select(clients.c.client_id).where(clients.c.client_id == client_id)).first() is not None

    def ultima_version(self, client_id: str) -> Perfil | None:
        consulta = (select(profile_versions.c.snapshot)
                    .where(profile_versions.c.client_id == client_id)
                    .order_by(profile_versions.c.version.desc()).limit(1))
        with self.motor.connect() as c:
            fila = c.execute(consulta).first()
        return None if fila is None else Perfil.model_validate(fila.snapshot)

    def version(self, client_id: str, version: int) -> Perfil | None:
        consulta = select(profile_versions.c.snapshot).where(
            profile_versions.c.client_id == client_id, profile_versions.c.version == version)
        with self.motor.connect() as c:
            fila = c.execute(consulta).first()
        return None if fila is None else Perfil.model_validate(fila.snapshot)

    def historial(self, client_id: str) -> list[dict[str, Any]]:
        t = profile_versions.c
        consulta = (select(t.version, t.status, t.reason, t.author, t.created_at)
                    .where(t.client_id == client_id).order_by(t.version))
        with self.motor.connect() as c:
            return [{**f._asdict(), "created_at": _utc(f.created_at)} for f in c.execute(consulta)]

    # ---------- capa personal ----------

    def insertar_personal(self, capa: CapaPersonal) -> None:
        try:
            with self.motor.begin() as c:
                c.execute(insert(personal_versions).values(
                    client_id=capa.client_id, version=capa.version, consent_given=capa.consent_given,
                    consent_at=capa.consent_at, data=capa.data, author=capa.author, created_at=capa.created_at,
                ))
        except IntegrityError as e:
            raise ConflictoVersion(f"La versión personal {capa.version} de {capa.client_id} ya existe") from e

    def ultima_personal(self, client_id: str) -> CapaPersonal | None:
        t = personal_versions.c
        consulta = select(personal_versions).where(t.client_id == client_id).order_by(t.version.desc()).limit(1)
        with self.motor.connect() as c:
            fila = c.execute(consulta).first()
        if fila is None:
            return None
        d = fila._asdict()
        d["consent_at"], d["created_at"] = _utc(d["consent_at"]), _utc(d["created_at"])
        return CapaPersonal.model_validate(d)

    def borrar_personal(self, client_id: str) -> int:
        """Derecho de supresión (RGPD): borra toda la capa personal. No toca el registro MiFID."""
        with self.motor.begin() as c:
            return c.execute(delete(personal_versions).where(personal_versions.c.client_id == client_id)).rowcount

    # ---------- sesiones y transcripción ----------

    def crear_sesion(self, session_id: str, client_id: str, canal: str, momento: datetime) -> None:
        with self.motor.begin() as c:
            c.execute(insert(sessions).values(session_id=session_id, client_id=client_id,
                                              channel=canal, started_at=momento))

    def sesion(self, session_id: str) -> dict[str, Any] | None:
        with self.motor.connect() as c:
            fila = c.execute(select(sessions).where(sessions.c.session_id == session_id)).first()
        if fila is None:
            return None
        d = fila._asdict()
        d["started_at"], d["ended_at"] = _utc(d["started_at"]), _utc(d["ended_at"])
        return d

    def cerrar_sesion(self, session_id: str, momento: datetime, conversation_id: str | None) -> None:
        with self.motor.begin() as c:
            c.execute(update(sessions).where(sessions.c.session_id == session_id)
                      .values(ended_at=momento, conversation_id=conversation_id))

    def _turno_existente(self, c, session_id: str, turn_id: str) -> int | None:
        return c.execute(select(turns.c.idx).where(
            turns.c.session_id == session_id, turns.c.turn_id == turn_id)).scalar()

    def insertar_turno(self, session_id: str, turno: Turno, momento: datetime) -> tuple[int, bool]:
        """Devuelve (índice, es_nuevo). Reenviar el mismo turn_id no lo duplica."""
        assert turno.turn_id, "El servicio asigna turn_id antes de guardar"
        for _ in range(5):
            try:
                with self.motor.begin() as c:
                    previo = self._turno_existente(c, session_id, turno.turn_id)
                    if previo is not None:
                        return previo, False
                    idx = c.execute(select(func.count()).select_from(turns)
                                    .where(turns.c.session_id == session_id)).scalar_one()
                    c.execute(insert(turns).values(
                        session_id=session_id, turn_id=turno.turn_id, idx=idx, speaker=turno.speaker,
                        text=turno.text, t_start=turno.t_start, t_end=turno.t_end, created_at=momento,
                    ))
                    return idx, True
            except IntegrityError:
                continue  # otro turno tomó el mismo índice a la vez: se reintenta
        raise ConflictoVersion(f"No se pudo guardar el turno {turno.turn_id} de {session_id}")

    def turnos(self, session_id: str) -> list[Turno]:
        t = turns.c
        consulta = (select(t.turn_id, t.speaker, t.text, t.t_start, t.t_end)
                    .where(t.session_id == session_id).order_by(t.idx))
        with self.motor.connect() as c:
            return [Turno.model_validate(f._asdict()) for f in c.execute(consulta)]
