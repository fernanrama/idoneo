"""Garantías propias del almacén en base de datos (SQLite y, si está configurado, Postgres local)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.perfil import calculos, store
from app.perfil.almacenes.bd import AlmacenBD, url_de_prueba
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche, Turno

C = "carmen-68"
EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="q")]
POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()
MOTORES = ["sqlite"] + (["postgres"] if POSTGRES_TEST else [])


@pytest.fixture(params=MOTORES)
def bd(request, tmp_path, postgres_migrado):
    """Store en base de datos, vacío. SQLite en fichero (para poder 'reiniciar el proceso')."""
    url = f"sqlite:///{tmp_path / 'perfil_test.db'}" if request.param == "sqlite" else postgres_migrado()
    store.configurar("bd", url)
    yield url
    store.configurar("memoria")


def _motor():
    return store._a().motor  # noqa: SLF001 - acceso deliberado para probar la base por debajo


def test_los_datos_sobreviven_a_un_reinicio_del_proceso(bd):
    store.cargar_fixture(C)
    store.validar(C, "asesor-07", [])
    s = store.crear_sesion(C)
    store.anadir_turno(s["session_id"], Turno(speaker="client", text="hola", t_start=0, t_end=1))
    store.guardar_personal(C, {"exclusions": ["armas"]}, True, "system")

    store.configurar("bd", bd)  # nuevo proceso: nuevo motor, misma base
    p = store.perfil_para_consumidor(C)
    assert p.status == EstadoPerfil.active and p.personal["exclusions"] == ["armas"]
    assert [t.text for t in store.sesion(s["session_id"])["turns"]] == ["hola"]
    assert calculos.restricciones(p).usable
    assert store.asegurar_fixture(C).status == EstadoPerfil.active  # el arranque no pisa los datos


@pytest.mark.parametrize("sql", [
    "update profile_versions set reason = 'manipulado'",
    "delete from profile_versions",
    "update turns set text = 'otra cosa'",
    "delete from turns",
    "update personal_versions set consent_given = false",
])
def test_la_base_bloquea_modificar_el_registro(bd, sql):
    store.cargar_fixture(C)
    s = store.crear_sesion(C)
    store.anadir_turno(s["session_id"], Turno(speaker="client", text="hola", t_start=0, t_end=1))
    store.guardar_personal(C, {"exclusions": ["armas"]}, True, "system")
    with pytest.raises(DBAPIError):
        with _motor().begin() as c:
            c.execute(text(sql))
    assert store.perfil(C).version == 1


@pytest.mark.parametrize("tabla", ["profile_versions", "turns", "personal_versions"])
def test_postgres_bloquea_truncate(bd, tabla):
    if not bd.startswith("postgres"):
        pytest.skip("TRUNCATE solo existe en Postgres")
    store.cargar_fixture(C)
    with pytest.raises(DBAPIError, match="solo añadir"):
        with _motor().begin() as c:
            c.execute(text(f"truncate {tabla}"))
    with pytest.raises(DBAPIError, match="solo añadir"):  # tampoco en cascada desde clients
        with _motor().begin() as c:
            c.execute(text("truncate clients cascade"))
    assert store.perfil(C).version == 1


def test_borrar_la_capa_personal_si_esta_permitido(bd):
    store.cargar_fixture(C)
    store.guardar_personal(C, {"exclusions": ["armas"]}, True, "system")
    assert store.borrar_personal_interno(C) == 1


def test_claves_ajenas(bd):
    with pytest.raises(IntegrityError):
        with _motor().begin() as c:
            c.execute(text("insert into sessions (session_id, client_id, channel, started_at) "
                           "values ('s-x', 'no-existe', 'voice', CURRENT_TIMESTAMP)"))


def test_conflicto_con_otro_proceso_se_reintenta(bd):
    store.cargar_fixture(C)
    otro = AlmacenBD.desde_url(bd)  # otro proceso escribiendo en la misma base
    original = store._a().insertar  # noqa: SLF001
    llamadas = {"n": 0}

    def insertar_con_carrera(perfil):
        if llamadas["n"] == 0:
            llamadas["n"] += 1
            competidor = otro.ultima(C)
            competidor.version += 1
            competidor.reason, competidor.author = "otro proceso", "agent:extractor"
            otro.insertar(competidor)
        return original(perfil)

    store._a().insertar = insertar_con_carrera  # noqa: SLF001
    p = store.aplicar(C, [Parche(path="financial.debts_eur", value=9, source="declared", evidence=EV)],
                      "este", "agent:extractor")
    assert p.version == 3 and [v["reason"] for v in store.versiones(C)][1:] == ["otro proceso", "este"]
    otro.cerrar()


def test_otra_violacion_no_se_confunde_con_conflicto(bd):
    from app.perfil.almacenes.base import ConflictoVersion
    from app.perfil.modelos import Perfil

    with pytest.raises(IntegrityError) as info:
        store._a().insertar(Perfil(client_id="no-existe", version=2))  # noqa: SLF001 - viola la clave ajena
    assert not isinstance(info.value, ConflictoVersion)


def test_reiniciar_se_niega_fuera_de_bases_de_prueba(tmp_path):
    for url in (f"sqlite:///{tmp_path / 'produccion.db'}",):
        a = AlmacenBD.desde_url(url)
        with pytest.raises(RuntimeError):
            a.reiniciar()
        a.cerrar()
    for url in ("postgresql://u@db.abc.supabase.co:5432/postgres",
                "postgresql://u@127.0.0.1:5432/produccion",
                "postgresql://u@10.0.0.5:5432/perfil_test"):
        with pytest.raises(RuntimeError):
            url_de_prueba(url)


def test_postgres_sin_migraciones_falla_con_un_mensaje_claro():
    if not POSTGRES_TEST:
        pytest.skip("requiere TEST_POSTGRES_URL")
    from app.perfil.persistencia import db
    motor = db.crear_motor(url_de_prueba(POSTGRES_TEST))
    with motor.begin() as c:
        c.execute(text("drop schema public cascade"))
        c.execute(text("create schema public"))
    with pytest.raises(RuntimeError, match="migraciones"):
        db.preparar(motor)
    motor.dispose()
