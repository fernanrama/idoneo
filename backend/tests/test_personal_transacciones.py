"""Contrato personal CAS, borrado durable y transacciones sin red ni migraciones."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier, Event

import pytest
from sqlalchemy import event

from app.perfil import store
from app.perfil.almacenes.bd import AlmacenBD
from app.perfil.almacenes.base import ConflictoVersion
from app.perfil.modelos import Turno, ahora

C = "cliente-personal-test"
A = "agent:memory"


@pytest.mark.parametrize("operacion", ["sesion", "turnos", "historial", "autor", "insertar_turno"])
def test_sqlite_en_memoria_no_comparte_conexion_durante_transaccion_personal(operacion):
    almacen = store.configurar("bd", "sqlite://")
    store.crear(C)
    s = store.crear_sesion(C)
    actualizar(0, concerns=["original"])
    iniciada, terminada = Event(), Event()

    def acceder():
        iniciada.set()
        if operacion == "sesion":
            resultado = almacen.sesion(s["session_id"])
        elif operacion == "turnos":
            resultado = almacen.turnos(s["session_id"])
        elif operacion == "historial":
            resultado = almacen.historial(C)
        elif operacion == "autor":
            resultado = almacen.ultima_de_autor(C, "system")
        else:
            resultado = almacen.insertar_turno(s["session_id"], Turno(
                speaker="agent", text="turno ficticio", t_start=0, t_end=1), ahora())
        terminada.set()
        return resultado

    with ThreadPoolExecutor(max_workers=1) as hilos:
        with almacen.transaccion_personal(C) as t:
            previa = t.ultima()
            t.borrar()
            t.insertar(previa.model_copy(update={"version": 2, "consent_given": False,
                                               "consent_at": None, "data": {}}))
            lectura = hilos.submit(acceder)
            assert iniciada.wait(2)
            # StaticPool comparte la conexión física: cerrar otra lectura puede
            # hacer rollback del DELETE; otra escritura podría confirmarlo antes.
            assert not terminada.wait(0.1), "Otra operación usó la conexión de la transacción personal"
        lectura.result(timeout=2)
    assert store.personal(C).version == 2
    assert not store.personal(C).consent_given


@pytest.fixture(params=["memoria", "sqlite"])
def personal_bd(request, tmp_path):
    url = f"sqlite:///{tmp_path / 'personal_test.db'}"
    almacen = store.configurar("memoria" if request.param == "memoria" else "bd",
                              None if request.param == "memoria" else url)
    store.crear(C)
    yield almacen, url
    store.configurar("memoria")


def actualizar(revision, **cambios):
    return store.actualizar_personal(C, cambios, [], A,
                                    version_esperada=revision, consentimiento=True)


def test_precondicion_y_consentimiento_no_tienen_fallback(personal_bd):
    with pytest.raises(store.PrecondicionRequerida):
        store.actualizar_personal(C, {}, [], A, consentimiento=True)
    with pytest.raises(store.PrecondicionRequerida):
        store.borrar_personal(C)
    for consentimiento in (None, False, 1, "true"):
        with pytest.raises(store.DatoInvalido):
            store.actualizar_personal(C, {"concerns": ["nuevo"]}, [], A,
                                      version_esperada=0, consentimiento=consentimiento)
    assert store.personal(C) is None


def test_tombstone_conserva_revision_y_rechaza_put_o_delete_antiguo(personal_bd):
    primera = actualizar(0, communication={"pace": "slow"})
    assert store.borrar_personal(C, version_esperada=primera.version, autor=A) == 1
    tumba = store.personal(C)
    assert tumba.version == 2 and tumba.data == {} and not tumba.consent_given
    assert tumba.consent_at is None and tumba.author == A
    for operacion in (lambda: actualizar(1, concerns=["retrasado"]),
                      lambda: store.borrar_personal(C, version_esperada=1)):
        with pytest.raises(store.RevisionObsoleta):
            operacion()
    assert store.borrar_personal(C, version_esperada=2) == 0
    assert store.personal(C).version == 2
    nueva = actualizar(2, concerns=["consentimiento nuevo"])
    assert nueva.version == 3 and nueva.consent_at is not None
    assert "communication" not in nueva.data


def test_snapshot_de_borrado_no_cambia_por_reconsentimiento_posterior(personal_bd):
    actualizar(0, concerns=["anterior"])
    borradas, snapshot = store.revocar_personal(C, version_esperada=1)
    actualizar(snapshot.version, concerns=["nuevo consentimiento"])
    assert borradas == 1 and snapshot.version == 2 and not snapshot.consent_given
    assert snapshot.data == {} and store.personal(C).version == 3


def test_revision_invalida_o_extra_desconocido_no_escribe(personal_bd):
    for revision in (-1, True, "0"):
        with pytest.raises(store.DatoInvalido):
            actualizar(revision, concerns=["hola"])
    for datos in ({"communication": {"pace": "slow", "instrucciones": "x"}},
                  {"concerns": "texto"}, {"exclusions": ["x" * 301]},
                  {"concerns": ["x"] * 21}, {"tax": "x" * 5000}):
        with pytest.raises(store.DatoInvalido):
            actualizar(0, **datos)
    assert store.personal(C) is None


def test_revocacion_legacy_con_historia_no_se_confunde_con_tombstone(personal_bd):
    actualizar(0, concerns=["historia que debe borrarse"])
    store.guardar_personal(C, {}, False, "system")
    assert store.borrar_personal(C, version_esperada=2) == 2
    capa = store.personal(C)
    assert capa.version == 3 and capa.data == {} and not capa.consent_given
    with store._a().transaccion_personal(C) as t:
        assert t.cantidad() == 1


def test_dos_put_sobre_misma_revision_solo_confirman_uno(personal_bd):
    barrera = Barrier(2)

    def escribir(ritmo):
        barrera.wait(timeout=5)
        try:
            return actualizar(0, communication={"pace": ritmo}).version
        except store.RevisionObsoleta:
            return "obsoleta"

    with ThreadPoolExecutor(max_workers=2) as hilos:
        resultados = list(hilos.map(escribir, ["slow", "fast"]))
    assert sorted(map(str, resultados)) == ["1", "obsoleta"]
    assert store.personal(C).version == 1


def test_reintento_transitorio_no_rebasa_revision_del_llamante(personal_bd, monkeypatch):
    almacen, _url = personal_bd
    actualizar(0, concerns=["original"])
    original = almacen.transaccion_personal
    llamadas = 0

    @contextmanager
    def interferir(cid):
        nonlocal llamadas
        llamadas += 1
        if llamadas == 1:
            # Otro escritor ha confirmado mientras nuestra transacción falló.
            with original(cid) as t:
                previa = t.ultima()
                t.insertar(previa.model_copy(update={"version": 2, "data": {"concerns": ["competidor"]}}))
            raise ConflictoVersion("bloqueo transitorio simulado")
        with original(cid) as t:
            yield t

    monkeypatch.setattr(almacen, "transaccion_personal", interferir)
    with pytest.raises(store.RevisionObsoleta):
        actualizar(1, communication={"pace": "fast"})
    assert llamadas == 2
    assert store.personal(C).data == {"concerns": ["competidor"]}


def test_crear_nuevo_no_devuelve_un_cliente_preexistente(personal_bd):
    with pytest.raises(store.Conflicto):
        store.crear_nuevo(C)
    assert store.crear_nuevo("otro-cliente-test").version == 1


def test_sqlite_otra_conexion_serializa_y_borrado_revertido_es_completo(personal_bd):
    almacen, url = personal_bd
    if almacen.tipo != "bd":
        pytest.skip("transacciones SQL")
    primera = actualizar(0, concerns=["se conserva si falla"])
    otro = AlmacenBD.desde_url(url)
    try:
        assert otro.ultima_personal(C).version == 1

        def fallar(_conexion, _cursor, sentencia, _parametros, _contexto, _muchos):
            if sentencia.lower().startswith("insert into personal_versions"):
                raise RuntimeError("fallo de tombstone simulado")

        event.listen(almacen.motor, "before_cursor_execute", fallar)
        try:
            with pytest.raises(RuntimeError, match="tombstone"):
                store.borrar_personal(C, version_esperada=1)
        finally:
            event.remove(almacen.motor, "before_cursor_execute", fallar)
        assert otro.ultima_personal(C).model_dump() == primera.model_dump()
        store.borrar_personal(C, version_esperada=1)
        assert otro.ultima_personal(C).version == 2
    finally:
        otro.cerrar()


def test_sqlite_dos_almacenes_concurrentes_comparten_revision(personal_bd):
    almacen, url = personal_bd
    if almacen.tipo != "bd":
        pytest.skip("dos conexiones SQL independientes")
    actualizar(0, concerns=["inicial"])
    otro = AlmacenBD.desde_url(url)
    barrera = Barrier(2)

    def escribir(a):
        barrera.wait(timeout=5)
        with a.transaccion_personal(C) as transaccion:
            previa = transaccion.ultima()
            if previa.version != 1:
                return "obsoleta"
            transaccion.insertar(previa.model_copy(update={"version": 2, "data": {"concerns": ["nuevo"]}}))
            return "confirmada"

    try:
        with ThreadPoolExecutor(max_workers=2) as hilos:
            assert sorted(hilos.map(escribir, [almacen, otro])) == ["confirmada", "obsoleta"]
        assert otro.ultima_personal(C).version == 2
    finally:
        otro.cerrar()


@pytest.mark.parametrize("tipo", ["json", "sqlite"])
def test_tombstone_sobrevive_reinicio_sin_texto_antiguo(tipo, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1" if tipo == "json" else "0")
    url = f"sqlite:///{tmp_path / 'tombstone_test.db'}"
    argumentos = ("memoria",) if tipo == "json" else ("bd", url)
    store.configurar(*argumentos)
    store.crear(C)
    actualizar(0, concerns=["secreto sintético eliminado"])
    actualizar(1, communication={"pace": "slow"})
    assert store.borrar_personal(C, version_esperada=2) == 2
    store.configurar(*argumentos)
    capa = store.personal(C)
    assert capa.version == 3 and not capa.consent_given and capa.data == {}
    if tipo == "json":
        assert "secreto" not in (tmp_path / f"personal_{C}.json").read_text()
    else:
        with store._a().motor.connect() as conexion:
            from sqlalchemy import select
            from app.perfil.persistencia.tablas import personal_versions

            filas = conexion.execute(select(personal_versions.c.version, personal_versions.c.data)).all()
        assert filas == [(3, {})]
    with pytest.raises(store.RevisionObsoleta):
        actualizar(2, concerns=["viejo"])


@pytest.mark.parametrize("operacion", ["actualizar", "borrar"])
def test_fallo_json_rechaza_publicacion_y_no_toca_mifid(operacion, tmp_path, monkeypatch):
    import os

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1")
    store.configurar("memoria")
    store.crear(C)
    primera = actualizar(0, concerns=["anterior"])
    perfil_antes = (tmp_path / f"perfil_{C}.json").read_bytes()
    personal_antes = (tmp_path / f"personal_{C}.json").read_bytes()
    original = os.replace

    def fallar(origen, destino):
        if destino.name == f"personal_{C}.json":
            raise OSError("rename fallido")
        return original(origen, destino)

    monkeypatch.setattr(os, "replace", fallar)
    with pytest.raises(OSError, match="rename fallido"):
        if operacion == "actualizar":
            actualizar(1, concerns=["posterior"])
        else:
            store.borrar_personal(C, version_esperada=1)
    assert store.personal(C).model_dump() == primera.model_dump()
    assert (tmp_path / f"personal_{C}.json").read_bytes() == personal_antes
    assert (tmp_path / f"perfil_{C}.json").read_bytes() == perfil_antes
    assert not list(tmp_path.glob("*.tmp"))


def test_escritura_mifid_no_reescribe_json_personal(tmp_path, monkeypatch):
    import os
    from app.perfil.modelos import Parche

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1")
    store.configurar("memoria")
    store.crear(C)
    actualizar(0, concerns=["se conserva"])
    ruta = tmp_path / f"personal_{C}.json"
    antes = ruta.read_bytes()
    original = os.replace

    def comprobar(origen, destino):
        assert destino != ruta, "Una escritura MiFID intentó reescribir memoria personal"
        return original(origen, destino)

    monkeypatch.setattr(os, "replace", comprobar)
    store.aplicar(C, [Parche(path="financial.debts_eur", value=0, source="advisor")],
                  "corrección sintética", "advisor:prueba")
    assert ruta.read_bytes() == antes
