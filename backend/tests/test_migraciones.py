"""La migración SQL de Postgres y las tablas de SQLAlchemy no deben separarse; el aplicador es seguro."""

from __future__ import annotations

import os
import re

import pytest
from sqlalchemy import inspect, text

from app.perfil.persistencia import db, migrar
from app.perfil.persistencia.tablas import metadata
from tests.soporte_bd import postgres_vacio as postgres_vacio_url

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
    for tabla in ("profile_versions", "turns", "session_audio"):
        assert f"before update or delete on {tabla}" in SQL
    assert "before update on personal_versions" in SQL
    for tabla in ("profile_versions", "turns", "personal_versions", "session_audio"):
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
    assert migrar.main(["--destino", "127.0.0.1:5432/perfil_test"]) == 2
    assert "Postgres" in capsys.readouterr().out


def test_sin_destino_explicito_no_arranca(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u@127.0.0.1:5432/perfil_test")
    with pytest.raises(SystemExit) as salida:
        migrar.main([])
    assert salida.value.code == 2 and "--destino" in capsys.readouterr().err


def _sin_conexiones(monkeypatch, *modulos):
    def prohibido(*_a, **_k):
        raise AssertionError("no debía conectarse")
    for modulo in modulos:
        monkeypatch.setattr(modulo, "crear_motor", prohibido)


@pytest.mark.parametrize("url", [
    "postgresql://u:clave-sintetica@db.ejemplo.supabase.co:5432/postgres",
    "postgresql://u:clave-sintetica@127.0.0.1:5433/perfil_test",
    "postgresql://u:clave-sintetica@127.0.0.1:5432/otra_base",
])
def test_destino_distinto_no_se_conecta_ni_muestra_credenciales(monkeypatch, capsys, url):
    from app.perfil.persistencia import verificar

    _sin_conexiones(monkeypatch, migrar, verificar)
    monkeypatch.setenv("DATABASE_URL", url)
    assert migrar.main(["--destino", "127.0.0.1:5432/perfil_test", "--aplicar"]) == 2
    assert verificar.main(["ensayo", "--destino", "127.0.0.1:5432/perfil_test"]) == 2
    salida = capsys.readouterr().out
    assert "no me conecto" in salida and "clave-sintetica" not in salida and "u@" not in salida


def test_no_lee_el_env_del_repositorio_por_su_cuenta(monkeypatch, capsys, tmp_path):
    """Sin la variable en el entorno no hay destino, aunque un .env la tenga; solo --env-file la lee."""
    from app.perfil.persistencia import verificar

    _sin_conexiones(monkeypatch, migrar, verificar)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=postgresql://u:clave-sintetica@db.ejemplo.supabase.co:5432/postgres\n"
                   "ANTHROPIC_API_KEY=clave-sintetica-de-pago\n", "utf-8")
    monkeypatch.chdir(tmp_path)
    assert migrar.main(["--destino", "127.0.0.1:5432/perfil_test"]) == 2
    assert "No hay URL" in capsys.readouterr().out
    assert migrar.main(["--destino", "127.0.0.1:5432/perfil_test", "--env-file", str(env)]) == 2
    assert "db.ejemplo.supabase.co:5432/postgres" in capsys.readouterr().out
    assert os.environ.get("ANTHROPIC_API_KEY") == "" and "DATABASE_URL" not in os.environ
    for modulo in (migrar, verificar):
        assert "load_dotenv" not in open(modulo.__file__, encoding="utf-8").read()


def test_cli_postgres_con_destino_explicito(monkeypatch, capsys):
    if not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local de pruebas)")
    from app.perfil.persistencia import seguridad

    url = postgres_vacio_url()
    monkeypatch.setenv("URL_ENSAYO", url)
    destino = seguridad.describir(url)
    argumentos = ["--destino", destino, "--variable", "URL_ENSAYO"]
    assert migrar.main(argumentos) == 0
    assert "Pendientes: 0001_esquema_inicial.sql, 0002_audio_de_sesion.sql" in capsys.readouterr().out
    assert migrar.main([*argumentos, "--aplicar"]) == 0
    assert migrar.main(argumentos) == 0
    assert "No hay migraciones pendientes" in capsys.readouterr().out


@pytest.fixture
def postgres_vacio():
    if not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local de pruebas)")
    motor = db.crear_motor(postgres_vacio_url())
    yield motor
    motor.dispose()


TODAS = ["0001_esquema_inicial.sql", "0002_audio_de_sesion.sql"]


def test_postgres_plan_aplicar_y_repetir(postgres_vacio):
    assert [m.nombre for m in migrar.pendientes(postgres_vacio)] == TODAS
    assert "schema_migrations" not in inspect(postgres_vacio).get_table_names()  # el plan no escribe
    assert migrar.aplicar(postgres_vacio) == TODAS
    assert migrar.pendientes(postgres_vacio) == [] and migrar.aplicar(postgres_vacio) == []


def test_postgres_con_solo_0001_arranca_sin_audio_y_luego_se_actualiza(postgres_vacio, tmp_path):
    """El caso de Supabase ya desplegado: el backend nuevo arranca antes de aplicar 0002, sin audio."""
    from app.perfil.almacenes.bd import AlmacenBD

    primera = migrar.listar()[0]
    (tmp_path / primera.nombre).write_text(primera.sql, encoding="utf-8")
    assert migrar.aplicar(postgres_vacio, tmp_path) == ["0001_esquema_inicial.sql"]
    almacen = AlmacenBD(postgres_vacio)
    db.preparar(postgres_vacio)  # no falla: session_audio es opcional
    assert almacen.audio_disponible() is False
    assert [m.nombre for m in migrar.pendientes(postgres_vacio)] == ["0002_audio_de_sesion.sql"]
    assert migrar.aplicar(postgres_vacio) == ["0002_audio_de_sesion.sql"]
    inspect(postgres_vacio).clear_cache()
    assert AlmacenBD(postgres_vacio).audio_disponible() is True


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
