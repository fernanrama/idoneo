"""Protecciones de la base: destino explícito de las herramientas y borrado solo en bases desechables."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from app.perfil.almacenes.bd import AlmacenBD
from app.perfil.persistencia import db, migrar, seguridad
from tests.soporte_bd import POSTGRES_TEST, postgres_recien_migrado


@pytest.mark.parametrize("url", [
    "postgresql://u@db.abc.supabase.co:5432/perfil_test",
    "postgresql://u@aws-0-eu-west-1.pooler.supabase.com:5432/postgres",
    "postgresql://u@127.0.0.1:5432/produccion",
    "postgresql://u@10.0.0.5:5432/perfil_test",
    "postgresql://u@ejemplo.org:5432/perfil_test",
])
def test_url_no_autorizada_para_borrar(url):
    with pytest.raises(seguridad.BaseNoAutorizada):
        seguridad.comprobar_url_de_pruebas(url)


@pytest.mark.parametrize("url", [
    "postgresql://u@db.abc.supabase.co:5432/perfil_test",
    "postgresql://u@10.0.0.5:5432/perfil_test",
])
def test_reiniciar_se_niega_sin_conectarse(url, monkeypatch):
    almacen = AlmacenBD(db.crear_motor(url))  # create_engine no conecta todavía

    def conectar(*_a, **_k):
        raise AssertionError("no debía conectarse")

    monkeypatch.setattr(almacen.motor, "connect", conectar)
    with pytest.raises(seguridad.BaseNoAutorizada):
        almacen.reiniciar()


def test_vaciar_solo_en_postgres():
    with pytest.raises(seguridad.BaseNoAutorizada):
        seguridad.vaciar_esquema_publico(db.crear_motor("sqlite://"))


@pytest.mark.parametrize("destino,url,valida", [
    ("127.0.0.1:54418/perfil_test", "postgresql://u@127.0.0.1:54418/perfil_test", True),
    ("127.0.0.1:5432/perfil_test", "postgresql://u@127.0.0.1/perfil_test", True),  # puerto por defecto
    ("[::1]:5432/perfil_test", "postgresql://u@[::1]:5432/perfil_test", True),
    ("127.0.0.1:5433/perfil_test", "postgresql://u@127.0.0.1:5432/perfil_test", False),
    ("127.0.0.1:5432/otra", "postgresql://u@127.0.0.1:5432/perfil_test", False),
    ("db.abc.supabase.co:5432/postgres", "postgresql://u@127.0.0.1:5432/postgres", False),
    ("sin-formato", "postgresql://u@127.0.0.1:5432/perfil_test", False),
])
def test_destino_explicito(monkeypatch, destino, url, valida):
    monkeypatch.setenv("URL_DESTINO_TEST", url)
    if valida:
        assert seguridad.destino_explicito(destino, "URL_DESTINO_TEST") == url
    else:
        with pytest.raises(seguridad.DestinoNoValido):
            seguridad.destino_explicito(destino, "URL_DESTINO_TEST")


def test_env_file_solo_lee_la_variable_pedida(tmp_path, monkeypatch):
    import os

    monkeypatch.delenv("DATABASE_URL", raising=False)
    env = tmp_path / "destino.env"
    env.write_text("DATABASE_URL=postgresql://u:clave-sintetica@127.0.0.1:5432/perfil_test\n"
                   "OTRA_VARIABLE_SINTETICA=1\n", "utf-8")
    url = seguridad.destino_explicito("127.0.0.1:5432/perfil_test", env_file=str(env))
    assert url.endswith("@127.0.0.1:5432/perfil_test")
    assert "DATABASE_URL" not in os.environ and "OTRA_VARIABLE_SINTETICA" not in os.environ
    with pytest.raises(seguridad.DestinoNoValido, match="No existe"):
        seguridad.destino_explicito("127.0.0.1:5432/perfil_test", env_file=str(tmp_path / "no-esta.env"))


def test_postgres_sin_marca_de_desechable_no_se_borra(monkeypatch):
    """La marca del servidor es la autorización: si no coincide, no se borra nada."""
    if not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL (Postgres local de pruebas)")
    url = postgres_recien_migrado()
    motor = db.crear_motor(url)
    try:
        monkeypatch.setattr(seguridad, "MARCA_DESECHABLE", "otra-marca-sintetica")
        with pytest.raises(seguridad.BaseNoAutorizada, match="no está marcada"):
            seguridad.vaciar_esquema_publico(motor)
        with pytest.raises(seguridad.BaseNoAutorizada):
            AlmacenBD(motor).reiniciar()
        inspect(motor).clear_cache()
        assert "profile_versions" in inspect(motor).get_table_names()  # nada se ha borrado
        with motor.connect() as c:
            assert c.execute(text("select count(*) from schema_migrations")).scalar() == len(migrar.listar())
    finally:
        motor.dispose()
