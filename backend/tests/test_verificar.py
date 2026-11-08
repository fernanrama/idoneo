"""Herramienta de verificación de migraciones (persistencia/verificar.py) contra un Postgres LOCAL de pruebas.

Comprueba que detecta lo que debe detectar y que el ensayo y la prueba de escritura no dejan rastro.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import inspect, text

from app.perfil.persistencia import db, migrar, verificar

POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not POSTGRES_TEST, reason="requiere TEST_POSTGRES_URL (Postgres local de pruebas)")


@pytest.fixture
def motor_vacio():
    from tests.conftest import postgres_vacio

    motor = db.crear_motor(postgres_vacio())
    yield motor
    motor.dispose()


def _tablas(motor) -> set[str]:
    inspect(motor).clear_cache()
    return set(inspect(motor).get_table_names())


def _fallos(inf) -> list[str]:
    return [f"{c}: {d}" for n, c, d in inf.lineas if n == "FALLO"]


def test_previo_en_base_vacia(motor_vacio):
    inf = verificar.previo(motor_vacio)
    assert not _fallos(inf)
    assert any(c == "migraciones pendientes" and "0001" in d for _, c, d in inf.lineas)
    assert _tablas(motor_vacio) == set()  # solo lectura


def test_posterior_sin_migrar_falla(motor_vacio):
    assert verificar.posterior(motor_vacio).fallos > 0


def test_ensayo_comprueba_todo_y_no_deja_rastro(motor_vacio):
    inf = verificar.ensayo(motor_vacio)
    assert not _fallos(inf), _fallos(inf)
    nombres = [c for _, c, _ in inf.lineas]
    assert "ensayo: 0001_esquema_inicial.sql" in nombres and "bloquea TRUNCATE clients CASCADE" in nombres
    assert _tablas(motor_vacio) == set()  # ROLLBACK
    with motor_vacio.connect() as c:
        assert c.execute(text("select count(*) from pg_proc where proname = 'perfil_bloquear_cambio'")).scalar() == 0


def test_posterior_tras_aplicar_y_prueba_de_escritura(motor_vacio):
    migrar.aplicar(motor_vacio)
    inf = verificar.posterior(motor_vacio, con_prueba_escritura=True)
    assert not _fallos(inf), _fallos(inf)
    with motor_vacio.connect() as c:  # la prueba de escritura no deja filas
        assert c.execute(text("select count(*) from clients")).scalar() == 0


@pytest.mark.parametrize("sabotaje,esperado", [
    ("drop trigger turns_sin_truncate on turns", "trigger turns_sin_truncate"),
    ("alter table profile_versions disable trigger profile_versions_solo_anadir", "trigger profile_versions_solo_anadir"),
    ("alter table sessions disable row level security", "RLS activado"),
    ("create policy abierta on profile_versions for select using (true)", "sin políticas RLS"),
    ("alter function perfil_bloquear_cambio() reset search_path", "función perfil_bloquear_cambio"),
    ("alter table turns drop constraint turns_speaker_check", "restricciones y claves ajenas"),
])
def test_posterior_detecta_sabotajes(motor_vacio, sabotaje, esperado):
    migrar.aplicar(motor_vacio)
    with motor_vacio.begin() as c:
        c.execute(text(sabotaje))
    fallos = _fallos(verificar.posterior(motor_vacio))
    assert any(f.startswith(esperado) for f in fallos), fallos


def test_posterior_detecta_permisos_para_la_data_api(motor_vacio):
    migrar.aplicar(motor_vacio)
    with motor_vacio.begin() as c:
        if not c.execute(text("select 1 from pg_roles where rolname = 'anon'")).first():
            c.execute(text("create role anon nologin"))
        c.execute(text("grant select on profile_versions to anon"))
    fallos = _fallos(verificar.posterior(motor_vacio))
    assert any(f.startswith("sin permisos para") for f in fallos), fallos


def test_previo_detecta_choques_y_el_ensayo_no_se_ejecuta(motor_vacio):
    with motor_vacio.begin() as c:
        c.execute(text("create table clients (id int)"))
    inf = verificar.ensayo(motor_vacio)
    fallos = _fallos(inf)
    assert any(f.startswith("sin tablas que choquen con 0001") for f in fallos)
    assert any(f.startswith("ensayo: no se ejecuta") for f in fallos)
    assert _tablas(motor_vacio) == {"clients"}


def test_previo_detecta_migracion_editada(motor_vacio, tmp_path):
    migrar.aplicar(motor_vacio)
    for m in migrar.listar():
        (tmp_path / m.nombre).write_text(m.sql + "\n-- editada\n")
    inf = verificar.Informe()
    with motor_vacio.connect() as c:
        verificar.comprobar_previo(c, inf, tmp_path)
    assert any(f.startswith("migraciones aplicadas sin modificar") for f in _fallos(inf))


def test_linea_de_comandos(motor_vacio, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", POSTGRES_TEST)
    assert verificar.main(["previo"]) == 0
    assert verificar.main(["posterior"]) == 1
    salida = capsys.readouterr().out
    assert "SIN FALLOS" in salida and "FALLO(S)" in salida
    usuario = (motor_vacio.url.username or "").strip()
    assert not usuario or f"{usuario}@" not in salida  # nunca imprime credenciales
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    assert verificar.main(["previo"]) == 2
