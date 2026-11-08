"""Almacén en base de datos: Postgres (Supabase) en despliegue y SQLite en local y tests.

El registro MiFID y la transcripción son de solo añadir: este código solo inserta, y la propia base
bloquea UPDATE, DELETE y TRUNCATE (migraciones en backend/migraciones/; en SQLite, triggers propios).
La concurrencia es optimista: la clave (client_id, version) impide que dos escrituras creen la misma
versión; la segunda recibe ConflictoVersion y `store` relee y reintenta.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, delete, func, insert, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from ..modelos import EstadoPerfil, Perfil, Turno
from ..persistencia import db, migrar
from ..persistencia.tablas import clients, metadata, personal_versions, profile_versions, sessions, turns
from ..personal import CapaPersonal
from .base import ConflictoVersion, id_turno


def _utc(momento: datetime | None) -> datetime | None:
    """SQLite devuelve fechas sin zona; se interpretan como UTC."""
    if momento is not None and momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


class AlmacenBD:
    tipo = "bd"

    def __init__(self, motor: Engine):
        self.motor = motor

    @classmethod
    def desde_url(cls, url: str | None = None) -> AlmacenBD:
        """Sin url usa DATABASE_URL (o SQLite local). En Postgres exige las migraciones aplicadas."""
        motor = db.crear_motor(url)
        db.preparar(motor)
        return cls(motor)

    # ---------- perfil (capa MiFID) ----------

    @staticmethod
    def _fila(perfil: Perfil) -> dict[str, Any]:
        return {"client_id": perfil.client_id, "version": perfil.version, "status": perfil.status.value,
                "reason": perfil.reason, "author": perfil.author,
                "snapshot": perfil.model_dump(mode="json"), "created_at": perfil.created_at}

    def crear(self, perfil: Perfil) -> bool:
        """Crea el cliente y su versión 1 en una transacción. False si ya existía."""
        try:
            with self.motor.begin() as c:
                c.execute(insert(clients).values(client_id=perfil.client_id, created_at=perfil.created_at))
                c.execute(insert(profile_versions).values(**self._fila(perfil)))
            return True
        except IntegrityError:
            if self.ultima(perfil.client_id) is not None:
                return False
            raise

    def insertar(self, perfil: Perfil) -> None:
        try:
            with self.motor.begin() as c:
                c.execute(insert(profile_versions).values(**self._fila(perfil)))
        except IntegrityError as e:
            # Solo es conflicto si otra escritura ya creó esa versión; otra violación se propaga.
            if self.version(perfil.client_id, perfil.version) is not None:
                raise ConflictoVersion(f"La versión {perfil.version} de {perfil.client_id} ya existe") from e
            raise

    def _un_perfil(self, consulta) -> Perfil | None:
        with self.motor.connect() as c:
            fila = c.execute(consulta).first()
        return None if fila is None else Perfil.model_validate(fila.snapshot)

    def ultima(self, client_id: str) -> Perfil | None:
        t = profile_versions.c
        return self._un_perfil(select(t.snapshot).where(t.client_id == client_id)
                               .order_by(t.version.desc()).limit(1))

    def version(self, client_id: str, version: int) -> Perfil | None:
        t = profile_versions.c
        return self._un_perfil(select(t.snapshot).where(t.client_id == client_id, t.version == version))

    def ultima_activa(self, client_id: str, desde: int) -> Perfil | None:
        t = profile_versions.c
        return self._un_perfil(select(t.snapshot).where(
            t.client_id == client_id, t.status == EstadoPerfil.active.value, t.version >= desde,
        ).order_by(t.version.desc()).limit(1))

    def ultima_de_autor(self, client_id: str, autor: str) -> int | None:
        t = profile_versions.c
        with self.motor.connect() as c:
            return c.execute(select(func.max(t.version)).where(t.client_id == client_id, t.author == autor)).scalar()

    def historial(self, client_id: str) -> list[dict[str, Any]]:
        t = profile_versions.c
        consulta = (select(t.version, t.created_at, t.reason, t.author, t.status)
                    .where(t.client_id == client_id).order_by(t.version))
        with self.motor.connect() as c:
            return [{**f._asdict(), "created_at": _utc(f.created_at), "status": EstadoPerfil(f.status)}
                    for f in c.execute(consulta)]

    # ---------- capa personal ----------

    def ultima_personal(self, client_id: str) -> CapaPersonal | None:
        t = personal_versions.c
        with self.motor.connect() as c:
            fila = c.execute(select(personal_versions).where(t.client_id == client_id)
                             .order_by(t.version.desc()).limit(1)).first()
        if fila is None:
            return None
        d = fila._asdict()
        d["consent_at"], d["created_at"] = _utc(d["consent_at"]), _utc(d["created_at"])
        return CapaPersonal.model_validate(d)

    def insertar_personal(self, capa: CapaPersonal) -> None:
        try:
            with self.motor.begin() as c:
                c.execute(insert(personal_versions).values(
                    client_id=capa.client_id, version=capa.version, consent_given=capa.consent_given,
                    consent_at=capa.consent_at, data=capa.data, author=capa.author, created_at=capa.created_at))
        except IntegrityError as e:
            raise ConflictoVersion(f"La versión personal {capa.version} de {capa.client_id} ya existe") from e

    def borrar_personal(self, client_id: str) -> int:
        """Derecho de supresión (RGPD): borra la capa personal del cliente. El registro MiFID no se toca."""
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

    def insertar_turno(self, session_id: str, turno: Turno, momento: datetime) -> tuple[Turno, bool]:
        t = turns.c
        for _ in range(5):
            try:
                with self.motor.begin() as c:
                    if turno.turn_id:
                        previo = c.execute(select(t.turn_id, t.speaker, t.text, t.t_start, t.t_end).where(
                            t.session_id == session_id, t.turn_id == turno.turn_id)).first()
                        if previo is not None:
                            return Turno.model_validate(previo._asdict()), False
                    idx = c.execute(select(func.count()).select_from(turns)
                                    .where(t.session_id == session_id)).scalar_one()
                    nuevo = turno
                    if not turno.turn_id:
                        candidato = id_turno(idx)
                        existe = c.execute(select(t.turn_id).where(
                            t.session_id == session_id, t.turn_id == candidato)).first()
                        nuevo = turno.model_copy(update={
                            "turn_id": candidato if existe is None else f"{candidato}-{uuid.uuid4().hex[:4]}"})
                    c.execute(insert(turns).values(
                        session_id=session_id, turn_id=nuevo.turn_id, idx=idx, speaker=nuevo.speaker,
                        text=nuevo.text, t_start=nuevo.t_start, t_end=nuevo.t_end, created_at=momento))
                    return nuevo, True
            except IntegrityError:
                continue  # otro turno tomó el mismo índice a la vez: se reintenta
        raise ConflictoVersion(f"No se pudo guardar el turno en {session_id}")

    def turnos(self, session_id: str) -> list[Turno]:
        t = turns.c
        consulta = (select(t.turn_id, t.speaker, t.text, t.t_start, t.t_end)
                    .where(t.session_id == session_id).order_by(t.idx))
        with self.motor.connect() as c:
            return [Turno.model_validate(f._asdict()) for f in c.execute(consulta)]

    # ---------- utilidades ----------

    def reiniciar(self) -> None:
        """SOLO TESTS. Vacía la base recreándola; se niega fuera de una base local de pruebas."""
        u = self.motor.url
        if u.get_backend_name() == "sqlite":
            if u.database not in (None, "", ":memory:") and "test" not in Path(u.database).name:
                raise RuntimeError("reiniciar() solo se permite en SQLite en memoria o de pruebas")
            metadata.drop_all(self.motor)
            db.preparar(self.motor)
            return
        host = u.host or ""
        if "supabase" in str(u) or host not in ("", "localhost", "127.0.0.1") or "test" not in (u.database or ""):
            raise RuntimeError("reiniciar() solo se permite en un Postgres local de pruebas, nunca en Supabase")
        with self.motor.begin() as c:
            c.execute(text("drop schema public cascade"))
            c.execute(text("create schema public"))
        migrar.aplicar(self.motor)
        inspect(self.motor).clear_cache()

    def cerrar(self) -> None:
        self.motor.dispose()


def url_de_prueba(url: str) -> str:
    """Utilidad para tests: rechaza cualquier base que no sea local y de pruebas."""
    u = make_url(url)
    if "supabase" in url or (u.host or "") not in ("", "localhost", "127.0.0.1") or "test" not in (u.database or ""):
        raise RuntimeError("Solo un Postgres local de pruebas (nombre con 'test'), nunca Supabase")
    return url
