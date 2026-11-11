"""Configuración común de los tests.

- Sin credenciales reales ni red externa (tests/aislamiento/sitecustomize.py): las claves de Anthropic y
  ElevenLabs quedan definidas y vacías ANTES de importar la app (load_dotenv no sobrescribe variables que
  ya existen), y solo se permiten conexiones a esta máquina, también en los subprocesos de los tests.
- Ningún test puede llegar a Supabase: se vacía DATABASE_URL antes de importar la app y todo almacén de
  base de datos se crea con una URL explícita.
- Los tests de contrato (los de la PR #7 y test_store_contrato.py) se repiten con cada almacén:
  memoria, SQLite y, si existe TEST_POSTGRES_URL, un Postgres LOCAL de pruebas con las migraciones
  reales. Esa base se vacía en cada test: local, con 'test' en el nombre y marcada como desechable.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_AISLAMIENTO = Path(__file__).resolve().parent / "aislamiento"
_spec = importlib.util.spec_from_file_location("aislamiento_tests", _AISLAMIENTO / "sitecustomize.py")
aislamiento = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(aislamiento)  # activa el aislamiento en este proceso
# ...y en cada subproceso Python que lancen los tests (Python ejecuta sitecustomize al arrancar).
os.environ["PYTHONPATH"] = os.pathsep.join([str(_AISLAMIENTO), *filter(None, [os.environ.get("PYTHONPATH")])])

os.environ["DATABASE_URL"] = ""
os.environ["PERFIL_ALMACEN"] = "memoria"
os.environ["DATA_PERSIST"] = "0"
os.environ.pop("ADMIN_TOKEN", None)
os.environ.pop("VERIFICADOR_CLAUDE", None)

import pytest  # noqa: E402

from app.perfil import store  # noqa: E402
from tests.soporte_bd import POSTGRES_TEST, postgres_recien_migrado, postgres_vacio  # noqa: E402,F401

ALMACENES = ["memoria", "bd-sqlite"] + (["bd-postgres"] if POSTGRES_TEST else [])
MODULOS_CONTRATO = {"test_api", "test_mcp", "test_store_contrato", "test_procesamiento_turnos", "test_asesor_demo",
                    "test_pending_review", "test_confirmaciones"}


@pytest.fixture(autouse=True)
def credenciales_sinteticas(monkeypatch):
    """Solo material ficticio y una credencial de servicio explícita en tests autorizados.

    Cada test empieza sin claves de proveedores (aunque el .env se cargara al importar la app) y con
    VERIFICADOR_CLAUDE en su valor por defecto: los tests que simulan a Claude ponen una clave ficticia.
    """
    for clave in aislamiento.CLAVES_DE_PAGO:
        monkeypatch.setenv(clave, "")
    monkeypatch.delenv("VERIFICADOR_CLAUDE", raising=False)
    monkeypatch.setenv("CLIENT_ACCESS_SECRET", "secreto-sintetico-local-de-pruebas-32-bytes-minimo")
    monkeypatch.setenv("ADMIN_TOKEN", "servicio-sintetico-de-pruebas")
    monkeypatch.setenv("CLIENT_ACCESS_TTL_S", "28800")


@pytest.fixture
def mcp_servicio(monkeypatch):
    """Invocación interna de herramientas con Request de servicio ficticia explícita."""
    from types import SimpleNamespace

    from starlette.requests import Request

    from app.mcp.servidor import mcp

    request = Request({"type": "http", "headers": [(b"x-admin-token", os.environ["ADMIN_TOKEN"].encode())]})
    monkeypatch.setattr(mcp, "get_context", lambda: SimpleNamespace(
        request_context=SimpleNamespace(request=request)))


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
