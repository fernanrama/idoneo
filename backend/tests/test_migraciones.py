"""La migración SQL de Postgres y las tablas de SQLAlchemy no deben separarse."""

from __future__ import annotations

import re

import pytest

from app.perfil.persistencia import db, migrar
from app.perfil.persistencia.tablas import metadata

SQL = "\n".join(m.sql for m in migrar.listar())


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
        assert re.search(rf"before update or delete on {tabla}", SQL)
    assert "before update on personal_versions" in SQL
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
    from sqlalchemy import inspect
    assert "schema_migrations" not in inspect(motor).get_table_names()


def test_el_script_se_niega_con_sqlite(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert migrar.main([]) == 1
    assert "Postgres" in capsys.readouterr().out


def test_postgres_aplicada_y_sin_pendientes(servicios, motor_bd):
    """Solo con TEST_POSTGRES_URL: el conftest ya aplicó la migración real; no queda nada pendiente."""
    if motor_bd != "postgres":
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local)")
    assert migrar.pendientes(servicios.motor) == []
    assert set(migrar.aplicadas(servicios.motor)) == {m.version for m in migrar.listar()}


def test_postgres_detecta_migracion_editada(servicios, motor_bd, tmp_path):
    if motor_bd != "postgres":
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local)")
    for m in migrar.listar():
        (tmp_path / m.nombre).write_text(m.sql + "\n-- editada después de aplicarse\n")
    with pytest.raises(RuntimeError, match="ha cambiado"):
        migrar.pendientes(servicios.motor, tmp_path)
