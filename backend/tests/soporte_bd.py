"""Bases de datos de los tests: SQLite temporal y, si hay TEST_POSTGRES_URL, un Postgres local desechable.

El Postgres debe ser local, llevar `test` en el nombre y estar marcado como desechable en el servidor
(ver app/perfil/persistencia/seguridad.py); si no, los tests que lo vacían se niegan con BaseNoAutorizada.
"""

from __future__ import annotations

import os
from pathlib import Path

POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()
ALMACENES_SQL = ["sqlite"] + (["postgres"] if POSTGRES_TEST else [])


def postgres_vacio() -> str:
    """Deja el Postgres local de pruebas sin ningún objeto en public (sin migrar). Devuelve su URL."""
    from app.perfil.persistencia import db, seguridad

    url = seguridad.comprobar_url_de_pruebas(POSTGRES_TEST)
    motor = db.crear_motor(url)
    try:
        seguridad.vaciar_esquema_publico(motor)
    finally:
        motor.dispose()
    return url


def postgres_recien_migrado() -> str:
    """Vacía el Postgres local de pruebas y aplica las migraciones reales. Devuelve su URL."""
    from app.perfil.persistencia import db, migrar

    url = postgres_vacio()
    motor = db.crear_motor(url)
    try:
        migrar.aplicar(motor)
    finally:
        motor.dispose()
    return url


def url_sql(tipo: str, tmp_path: Path, archivo: str = "almacen_test.db") -> str:
    """URL de un almacén SQL vacío y listo: SQLite en un fichero temporal o el Postgres recién migrado."""
    if tipo == "sqlite":
        return f"sqlite:///{tmp_path / archivo}"
    if tipo == "postgres":
        return postgres_recien_migrado()
    raise ValueError(tipo)
