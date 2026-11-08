"""Configuración común de los tests.

- Ningún test puede llegar a Supabase: se vacía DATABASE_URL antes de importar la app (load_dotenv no
  sobrescribe variables existentes) y todo almacén de base de datos se crea con una URL explícita.
- Los tests de contrato (los de la PR #7 y test_store_contrato.py) se repiten con cada almacén:
  memoria, SQLite y, si existe TEST_POSTGRES_URL, un Postgres LOCAL de pruebas con las migraciones
  reales. Esa base se vacía en cada test: se exige 'test' en el nombre y nunca Supabase.
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = ""
os.environ["PERFIL_ALMACEN"] = "memoria"
os.environ["DATA_PERSIST"] = "0"
os.environ.pop("ADMIN_TOKEN", None)

import pytest  # noqa: E402

from app.perfil import store  # noqa: E402
from app.perfil.almacenes.bd import url_de_prueba  # noqa: E402

POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()
ALMACENES = ["memoria", "bd-sqlite"] + (["bd-postgres"] if POSTGRES_TEST else [])
MODULOS_CONTRATO = {"test_api", "test_mcp", "test_store_contrato", "test_procesamiento_turnos"}


def postgres_vacio() -> str:
    """Deja el Postgres local de pruebas sin ningún objeto en public (sin migrar). Devuelve su URL."""
    from sqlalchemy import text

    from app.perfil.persistencia import db

    url = url_de_prueba(POSTGRES_TEST)
    motor = db.crear_motor(url)
    with motor.begin() as c:
        c.execute(text("drop schema public cascade"))
        c.execute(text("create schema public"))
    motor.dispose()
    return url


def postgres_recien_migrado() -> str:
    """Vacía el Postgres local de pruebas y aplica las migraciones reales. Devuelve su URL."""
    from app.perfil.persistencia import db, migrar

    url = postgres_vacio()
    motor = db.crear_motor(url)
    migrar.aplicar(motor)
    motor.dispose()
    return url


def configurar_almacen(nombre: str) -> None:
    if nombre == "memoria":
        store.configurar("memoria")
    elif nombre == "bd-sqlite":
        store.configurar("bd", "sqlite://")
    elif nombre == "bd-postgres":
        store.configurar("bd", postgres_recien_migrado())
    else:  # pragma: no cover
        raise ValueError(nombre)


def pytest_generate_tests(metafunc):
    if "almacen" in metafunc.fixturenames and metafunc.module.__name__.rsplit(".", 1)[-1] in MODULOS_CONTRATO:
        metafunc.parametrize("almacen", ALMACENES, indirect=True)


@pytest.fixture(autouse=True)
def almacen(request):
    """Almacén de cada test: los de contrato, uno por almacén; el resto, memoria limpia."""
    nombre = getattr(request, "param", "memoria")
    configurar_almacen(nombre)
    yield nombre
    store.configurar("memoria")


@pytest.fixture
def postgres_migrado():
    """Función que deja el Postgres local de pruebas vacío y migrado (para tests propios de la base)."""
    return postgres_recien_migrado


@pytest.fixture
def carmen():
    """Carmen (DATOS SIMULADOS) recién cargada y pendiente de validación."""
    store.reiniciar()
    return store.cargar_fixture("carmen-68")
