"""Fixtures comunes. Cada test recibe una base de datos nueva y vacía.

- Siempre se prueba con SQLite en memoria.
- Si existe TEST_POSTGRES_URL (un Postgres LOCAL y desechable), los mismos tests se repiten en
  Postgres aplicando las migraciones reales. Se niega a usar Supabase u otro host remoto:
  esa base se borra entera en cada test.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.perfil.persistencia import db, migrar
from app.perfil.servicios import Servicios, construir_servicios

POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()


def _postgres_local(url: str) -> str:
    u = make_url(url)
    host = u.host or u.query.get("host") or ""
    if "supabase" in url or host not in ("", "localhost", "127.0.0.1") and not str(host).startswith("/"):
        raise RuntimeError("TEST_POSTGRES_URL debe ser un Postgres local y desechable, nunca Supabase")
    if "test" not in (u.database or ""):
        raise RuntimeError("Por seguridad, la base de TEST_POSTGRES_URL debe llevar 'test' en el nombre")
    return url


MOTORES = ["sqlite"] + (["postgres"] if POSTGRES_TEST else [])


def _base_vacia_postgres() -> str:
    url = _postgres_local(POSTGRES_TEST)
    motor = db.crear_motor(url)
    with motor.begin() as c:
        c.execute(text("drop schema public cascade"))
        c.execute(text("create schema public"))
    migrar.aplicar(motor)
    motor.dispose()
    return url


@pytest.fixture(params=MOTORES)
def motor_bd(request) -> str:
    return request.param


@pytest.fixture
def servicios(motor_bd) -> Servicios:
    url = "sqlite://" if motor_bd == "sqlite" else _base_vacia_postgres()
    s = construir_servicios(url)
    yield s
    s.motor.dispose()


@pytest.fixture
def carmen(servicios):
    """Carmen (DATOS SIMULADOS) cargada y pendiente de validación."""
    return servicios.perfiles.cargar_fixture("carmen-68")
