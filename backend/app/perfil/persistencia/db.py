"""Creación del motor de base de datos.

- `DATABASE_URL` de Supabase (`postgresql://...`): se usa el driver psycopg 3. Las tablas deben
  existir: se crean SOLO con las migraciones de backend/migraciones/ (nunca automáticamente).
- Sin `DATABASE_URL`, o con `sqlite://...`: SQLite local, que se crea solo. Es lo que usan los tests
  y lo que permite arrancar el ZIP de entrega sin cuenta de Supabase.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

from .tablas import SIN_UPDATE, SOLO_ANADIR, metadata

DIR_DATOS_POR_DEFECTO = Path(__file__).resolve().parents[3] / "data"


def url_desde_entorno() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    directorio = Path(os.getenv("DATA_DIR", DIR_DATOS_POR_DEFECTO))
    return f"sqlite:///{directorio / 'perfil.db'}"


def normalizar_url(url: str) -> str:
    u = make_url(url)
    if u.drivername in ("postgres", "postgresql"):
        u = u.set(drivername="postgresql+psycopg")
    return u.render_as_string(hide_password=False)


def es_sqlite(motor: Engine) -> bool:
    return motor.dialect.name == "sqlite"


def crear_motor(url: str | None = None) -> Engine:
    url = normalizar_url(url or url_desde_entorno())
    u = make_url(url)
    if u.get_backend_name() == "sqlite":
        en_memoria = u.database in (None, "", ":memory:")
        if not en_memoria:
            Path(u.database).parent.mkdir(parents=True, exist_ok=True)
        opciones: dict = {"connect_args": {"check_same_thread": False}}
        if en_memoria:
            opciones["poolclass"] = StaticPool  # una sola conexión compartida: si no, cada una ve otra base
        motor = create_engine(url, **opciones)

        @event.listens_for(motor, "connect")
        def _claves_ajenas(conexion, _registro):  # SQLite no comprueba FKs si no se le pide
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return motor
    # Supabase Session pooler: pocas conexiones y comprobación antes de usar cada una.
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=2)


def preparar(motor: Engine) -> None:
    """SQLite: crea tablas y protecciones. Postgres: solo comprueba que las migraciones están aplicadas."""
    if es_sqlite(motor):
        metadata.create_all(motor)
        with motor.begin() as c:
            for tabla in SOLO_ANADIR + SIN_UPDATE:
                c.execute(text(
                    f"CREATE TRIGGER IF NOT EXISTS {tabla}_sin_update BEFORE UPDATE ON {tabla} "
                    f"BEGIN SELECT RAISE(ABORT, '{tabla} es de solo añadir'); END"
                ))
            for tabla in SOLO_ANADIR:
                c.execute(text(
                    f"CREATE TRIGGER IF NOT EXISTS {tabla}_sin_delete BEFORE DELETE ON {tabla} "
                    f"BEGIN SELECT RAISE(ABORT, '{tabla} es de solo añadir'); END"
                ))
        return
    existentes = set(inspect(motor).get_table_names())
    faltan = sorted(set(metadata.tables) - existentes)
    if faltan:
        raise RuntimeError(
            f"Faltan tablas en la base de datos: {faltan}. "
            "Aplica las migraciones de backend/migraciones/ (python -m app.perfil.persistencia.migrar)."
        )
