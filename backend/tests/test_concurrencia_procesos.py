"""Concurrencia entre PROCESOS sobre la misma base: SQLite en fichero y, si hay TEST_POSTGRES_URL, Postgres.

Dos procesos hijos (`spawn`), cada uno con su propio almacén, hacen a la vez lo mismo que dos backends:
validar, guardar memoria personal sobre la misma revisión, añadir turnos y escribir versiones. Después
otro almacén nuevo («reinicio») comprueba que solo queda lo confirmado. Datos simulados; sin red.
"""

from __future__ import annotations

import multiprocessing

import pytest

from app.perfil import store
from tests import soporte_procesos as trabajo
from tests.soporte_bd import ALMACENES_SQL, url_sql

ESPERA_S = 120


@pytest.fixture(scope="module", params=ALMACENES_SQL)
def ensayo(request, tmp_path_factory):
    url = url_sql(request.param, tmp_path_factory.mktemp("procesos"), "procesos_test.db")
    store.configurar("bd", url)
    store.cargar_fixture(trabajo.CLIENTE_FIXTURE)
    store.crear(trabajo.CLIENTE)
    sesion = store.crear_sesion(trabajo.CLIENTE, "text")["session_id"]
    version_inicial = store.perfil(trabajo.CLIENTE).version

    contexto = multiprocessing.get_context("spawn")
    barrera, cola = contexto.Barrier(2), contexto.Queue()
    procesos = [contexto.Process(target=trabajo.ejecutar, args=(url, quien, sesion, barrera, cola))
                for quien in (0, 1)]
    for p in procesos:
        p.start()
    resultados = dict(cola.get(timeout=ESPERA_S) for _ in procesos)
    for p in procesos:
        p.join(ESPERA_S)
        if p.is_alive():  # pragma: no cover - bloqueo: el test debe fallar, no quedarse colgado
            p.terminate()
    assert all(p.exitcode == 0 for p in procesos), [p.exitcode for p in procesos]
    assert not [r["fallo"] for r in resultados.values() if "fallo" in r], resultados

    store.configurar("bd", url)  # «reinicio»: motor y pool nuevos, solo ve lo confirmado
    final = {
        "historial_fixture": store.versiones(trabajo.CLIENTE_FIXTURE),
        "consumidor": store.perfil_para_consumidor(trabajo.CLIENTE_FIXTURE),
        "personal": store.personal(trabajo.CLIENTE),
        "turnos": store.sesion(sesion)["turns"],
        "versiones": [h["version"] for h in store.versiones(trabajo.CLIENTE)],
    }
    store.configurar("memoria")
    return {"motor": request.param, "resultados": resultados, "final": final, "inicial": version_inicial}


def _de(ensayo, clave):
    return [ensayo["resultados"][q][clave] for q in (0, 1)]


def test_dos_asesores_a_la_vez_solo_validan_una_vez(ensayo):
    estados = sorted(r[0] for r in _de(ensayo, "validar"))
    assert estados == ["conflicto", "validado"], _de(ensayo, "validar")
    historial = ensayo["final"]["historial_fixture"]
    assert [h["reason"] for h in historial].count("validated") == 1
    assert ensayo["final"]["consumidor"].status.value == "active"


def test_dos_procesos_sobre_la_misma_revision_de_memoria_solo_confirman_uno(ensayo):
    assert sorted(r[0] for r in _de(ensayo, "memoria")) == ["confirmada", "obsoleta"]
    assert ensayo["final"]["personal"].version == 1


def test_turnos_simultaneos_en_la_misma_sesion_no_se_pierden_ni_se_duplican(ensayo):
    assert _de(ensayo, "turnos") == [[], []]
    turnos = ensayo["final"]["turnos"]
    assert len(turnos) == 2 * trabajo.TURNOS_POR_PROCESO
    assert len({t.turn_id for t in turnos}) == len(turnos)
    for quien in (0, 1):  # cada proceso conserva su orden
        propios = [t.text for t in turnos if t.text.startswith(f"p{quien}-")]
        assert propios == [f"p{quien}-{i}" for i in range(trabajo.TURNOS_POR_PROCESO)]


def test_versiones_simultaneas_sin_huecos_ni_duplicados(ensayo):
    confirmadas = sum(r[0] for r in _de(ensayo, "versiones"))
    assert [r[2] for r in _de(ensayo, "versiones")] == [[], []]  # solo éxitos o 409 limpios
    versiones = ensayo["final"]["versiones"]
    assert versiones == list(range(1, len(versiones) + 1))
    assert versiones[-1] == ensayo["inicial"] + confirmadas
    assert confirmadas >= 1
