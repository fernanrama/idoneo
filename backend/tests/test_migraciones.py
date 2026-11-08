"""La migración SQL de Postgres y las tablas de SQLAlchemy no deben separarse; el aplicador es seguro."""

from __future__ import annotations

import os
import re

import pytest
from sqlalchemy import inspect, text

from app.perfil.almacenes.bd import url_de_prueba
from app.perfil.persistencia import db, migrar
from app.perfil.persistencia.tablas import metadata

SQL = "\n".join(m.sql for m in migrar.listar())
POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()


def _bloque_tabla(nombre: str) -> str:
    m = re.search(rf"create table {nombre} \((.*?)\n\);", SQL, re.S)
    assert m, f"La migración no crea la tabla {nombre}"
    return m.group(1)


@pytest.mark.parametrize("tabla", sorted(metadata.tables))
def test_cada_tabla_y_columna_esta_en_la_migracion(tabla):
    bloque = _bloque_tabla(tabla)
    columnas_sql = {linea.split()[0] for linea in bloque.splitlines()
                    if linea.strip()
                    and not linea.strip().startswith(("primary", "constraint", "unique", "check", "--"))}
    assert columnas_sql == {c.name for c in metadata.tables[tabla].columns}


def test_la_migracion_protege_el_registro_y_activa_rls():
    for tabla in ("profile_versions", "turns"):
        assert f"before update or delete on {tabla}" in SQL
    assert "before update on personal_versions" in SQL
    for tabla in ("profile_versions", "turns", "personal_versions"):
        assert re.search(rf"before truncate on {tabla}\s+for each statement", SQL)
    for tabla in metadata.tables:
        assert f"alter table {tabla} enable row level security" in SQL


def test_nombres_de_migracion(tmp_path):
    (tmp_path / "0001_buena.sql").write_text("select 1;")
    assert [m.version for m in migrar.listar(tmp_path)] == ["0001"]
    (tmp_path / "mala.sql").write_text("select 1;")
    with pytest.raises(ValueError):
        migrar.listar(tmp_path)


def test_modo_plan_no_escribe_nada():
    motor = db.crear_motor("sqlite://")
    assert migrar.aplicadas(motor) == {}
    assert "schema_migrations" not in inspect(motor).get_table_names()


def test_el_script_se_niega_con_sqlite(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert migrar.main([]) == 1
    assert "Postgres" in capsys.readouterr().out


@pytest.fixture
def postgres_vacio():
    if not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local de pruebas)")
    motor = db.crear_motor(url_de_prueba(POSTGRES_TEST))
    with motor.begin() as c:
        c.execute(text("drop schema public cascade"))
        c.execute(text("create schema public"))
    yield motor
    motor.dispose()


def test_postgres_plan_aplicar_y_repetir(postgres_vacio):
    assert [m.nombre for m in migrar.pendientes(postgres_vacio)] == ["0001_esquema_inicial.sql"]
    assert "schema_migrations" not in inspect(postgres_vacio).get_table_names()  # el plan no escribe
    assert migrar.aplicar(postgres_vacio) == ["0001_esquema_inicial.sql"]
    assert migrar.pendientes(postgres_vacio) == [] and migrar.aplicar(postgres_vacio) == []


def test_postgres_detecta_migracion_editada(postgres_vacio, tmp_path):
    migrar.aplicar(postgres_vacio)
    for m in migrar.listar():
        (tmp_path / m.nombre).write_text(m.sql + "\n-- editada después de aplicarse\n")
    with pytest.raises(RuntimeError, match="ha cambiado"):
        migrar.pendientes(postgres_vacio, tmp_path)


def test_postgres_sin_permisos_para_la_data_api(postgres_vacio):
    with postgres_vacio.begin() as c:  # como en Supabase: permisos por defecto para anon/authenticated
        for rol in ("anon", "authenticated"):
            if not c.execute(text("select 1 from pg_roles where rolname = :r"), {"r": rol}).first():
                c.execute(text(f"create role {rol} nologin"))
        c.execute(text("alter default privileges in schema public grant all on tables to anon, authenticated"))
    migrar.aplicar(postgres_vacio)
    with postgres_vacio.connect() as c:
        permisos = c.execute(text("select count(*) from information_schema.role_table_grants "
                                  "where grantee in ('anon','authenticated') and table_schema='public'")).scalar()
        sin_rls = c.execute(text("select count(*) from pg_class where relnamespace='public'::regnamespace "
                                 "and relkind='r' and not relrowsecurity")).scalar()
    assert permisos == 0 and sin_rls == 0
