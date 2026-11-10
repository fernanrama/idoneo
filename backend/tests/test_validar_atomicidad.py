"""Atomicidad de la validación del asesor, por la API y sin servidores externos.

Cada caso usa memoria nueva o SQLite en un fichero temporal. Los rechazos deben
conservar el perfil y su historial; los éxitos mantienen las versiones actuales.
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest
from tests.soporte_acceso import cliente_autorizado
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.main import app
from app.perfil import store
from app.perfil.almacenes.base import ConflictoVersion
from app.perfil.almacenes.bd import AlmacenBD
from app.perfil.almacenes.memoria import AlmacenMemoria
from app.perfil.modelos import Fact, Fuente, Parche


CLIENTE = "carmen-68"  # fixture ficticio, solo en el proceso aislado de pytest
RUTA = f"/api/clients/{CLIENTE}"
ASESOR = "asesor-atomicidad"


@pytest.fixture(params=["memoria", "sqlite"])
def api_perfil(almacen, request, tmp_path):
    # Depender de `almacen` asegura que conftest haya limpiado el store antes.
    if request.param == "sqlite":
        store.configurar("bd", f"sqlite:///{tmp_path / 'validacion_test.db'}")
    store.cargar_fixture(CLIENTE)
    cliente = cliente_autorizado()
    yield cliente
    cliente.close()


@pytest.fixture
def eventos(api_perfil):
    cola = store.bus.suscribir(CLIENTE)
    yield cola
    store.bus.cancelar(CLIENTE, cola)


def instantanea(api):
    resultado = {}
    for recurso in ("profile", "versions", "constraints"):
        respuesta = api.get(f"{RUTA}/{recurso}")
        assert respuesta.status_code == 200
        resultado[recurso] = respuesta.json()
    return resultado


def comprobar_sin_cambios(api, antes):
    despues = instantanea(api)
    assert despues["versions"] == antes["versions"], "Un rechazo no debe crear versiones"
    assert despues["profile"] == antes["profile"], "Un rechazo no debe alterar el perfil"
    assert despues["constraints"] == antes["constraints"]


def correccion(ruta, valor):
    return {"path": ruta, "value": valor, "source": "advisor"}


@pytest.mark.parametrize("cambiar_ingresos", [False, True], ids=["retirar-obligatorio", "lote"])
def test_409_por_perfil_incompleto_no_persiste_correcciones(api_perfil, eventos, cambiar_ingresos):
    antes = instantanea(api_perfil)
    cambios = [correccion("financial.net_monthly_income_eur", 1800)] if cambiar_ingresos else []
    cambios.append(correccion("financial.debts_eur", None))

    respuesta = api_perfil.post(f"{RUTA}/validate", json={"advisor_id": ASESOR, "changes": cambios})

    assert respuesta.status_code == 409
    assert "financial.debts_eur" in respuesta.json()["detail"]
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()


@pytest.mark.parametrize("invalida", [
    correccion("financial.debts_eur", "no es un importe"),
    correccion("ruta.inexistente", 1000),
], ids=["valor-invalido", "ruta-invalida"])
def test_422_en_lote_no_persiste_la_correccion_valida(api_perfil, eventos, invalida):
    antes = instantanea(api_perfil)

    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR,
        "changes": [correccion("financial.net_monthly_income_eur", 1800), invalida],
    })

    assert respuesta.status_code == 422
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()


def comprobar_validado(api, respuesta):
    assert respuesta.status_code == 200
    perfil = respuesta.json()
    assert perfil["status"] == "active"
    assert perfil["assessments"]["suitability"]["complete"] is True
    assert perfil["review"]["validated_by"] == ASESOR
    assert perfil["review"]["validated_at"] is not None
    assert perfil["review"]["next_review"] is not None
    assert perfil["review"]["open_flags"] == 0
    assert all(a["status"] == "resolved" for a in perfil["alerts"])
    assert all(a["resolved_by"] == f"advisor:{ASESOR}" for a in perfil["alerts"])
    restricciones = api.get(f"{RUTA}/constraints").json()
    assert restricciones["usable"] is True
    assert restricciones["profile_version"] == perfil["version"]
    return perfil


def test_validacion_normal_conserva_el_perfil_previo(api_perfil):
    antes = instantanea(api_perfil)

    respuesta = api_perfil.post(f"{RUTA}/validate", json={"advisor_id": ASESOR, "changes": []})

    perfil = comprobar_validado(api_perfil, respuesta)
    assert perfil["version"] == antes["profile"]["version"] + 1
    historial = api_perfil.get(f"{RUTA}/versions").json()
    assert historial[:-1] == antes["versions"]
    assert historial[-1]["reason"] == "validated"
    anterior = api_perfil.get(f"{RUTA}/profile", params={"version": antes["profile"]["version"]})
    assert anterior.json() == antes["profile"]


def test_correccion_sin_cambios_solo_crea_validated(api_perfil):
    store.aplicar(CLIENTE, [Parche(path="financial.debts_eur", value=1000, source="advisor")],
                  "corrección previa", f"advisor:{ASESOR}")
    antes = instantanea(api_perfil)
    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
    })
    perfil = comprobar_validado(api_perfil, respuesta)
    assert perfil["version"] == antes["profile"]["version"] + 1
    historial = api_perfil.get(f"{RUTA}/versions").json()
    assert historial[:-1] == antes["versions"]
    assert historial[-1]["reason"] == "validated"


@pytest.mark.parametrize("incompleto", [False, True], ids=["completo", "completar-borrador"])
def test_correcciones_validas_se_validan_y_conservan_trazabilidad(api_perfil, incompleto):
    if incompleto:
        store.aplicar(CLIENTE, [Parche(path="financial.debts_eur", value=None, source="advisor")],
                      "preparar borrador incompleto", f"advisor:{ASESOR}")
    antes = instantanea(api_perfil)

    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR,
        "changes": [correccion("financial.net_monthly_income_eur", 1800),
                    correccion("financial.debts_eur", 1000)],
    })

    perfil = comprobar_validado(api_perfil, respuesta)
    for ruta, valor in (("financial.net_monthly_income_eur", 1800), ("financial.debts_eur", 1000)):
        dato = perfil["mifid"][ruta]
        assert dato["value"] == valor
        assert dato["source"] == "advisor"
        assert dato["updated_by"] == f"advisor:{ASESOR}"
    assert perfil["mifid"]["financial.loss_capacity_eur"]["value"] == 73600

    historial = api_perfil.get(f"{RUTA}/versions").json()
    assert historial[:len(antes["versions"])] == antes["versions"]
    nuevas = historial[len(antes["versions"]):]
    # Mantener el comportamiento público actual al diseñar la corrección atómica.
    assert [v["reason"] for v in nuevas] == ["advisor_correction", "validated"]
    assert [v["version"] for v in nuevas] == [antes["profile"]["version"] + 1,
                                             antes["profile"]["version"] + 2]
    assert all(v["author"] == f"advisor:{ASESOR}" for v in nuevas)
    assert nuevas[-1]["status"] == "active"
    anterior = api_perfil.get(f"{RUTA}/profile", params={"version": antes["profile"]["version"]})
    assert anterior.json() == antes["profile"]


def test_eventos_se_publican_con_el_lote_ya_confirmado(api_perfil, monkeypatch):
    observados = []
    publicar = store.bus.publicar

    def observar(evento):
        # Un lector que reaccione al primer evento debe ver ya la validación final.
        observados.append((evento.version, store.perfil(CLIENTE).status.value,
                           [v["reason"] for v in store.versiones(CLIENTE)][-2:]))
        publicar(evento)

    monkeypatch.setattr(store.bus, "publicar", observar)
    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
    })
    comprobar_validado(api_perfil, respuesta)
    assert observados
    assert {v for v, _, _ in observados} == {2, 3}
    assert all(estado == "active" and motivos == ["advisor_correction", "validated"]
               for _, estado, motivos in observados)


def test_conflicto_rehace_el_lote_sobre_la_ultima_version(api_perfil, monkeypatch):
    almacen = store._a()
    otro = AlmacenBD.desde_url(str(almacen.motor.url)) if isinstance(almacen, AlmacenBD) else almacen
    insertar = almacen.insertar_lote
    intentos = []

    def competir(perfiles):
        intentos.append([p.version for p in perfiles])
        if len(intentos) == 1:
            rival = otro.ultima(CLIENTE)
            rival.version += 1
            rival.reason, rival.author, rival.personal = "competidor", "system", {}
            rival.mifid["financial.other_assets_eur"] = Fact(
                value=123, source=Fuente.declared, updated_by="system")
            otro.insertar(rival)
        insertar(perfiles)

    monkeypatch.setattr(almacen, "insertar_lote", competir)
    try:
        respuesta = api_perfil.post(f"{RUTA}/validate", json={
            "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
        })
        perfil = comprobar_validado(api_perfil, respuesta)
        assert intentos == [[2, 3], [3, 4]]
        assert perfil["version"] == 4
        assert perfil["mifid"]["financial.other_assets_eur"]["value"] == 123
        assert [v["reason"] for v in api_perfil.get(f"{RUTA}/versions").json()][1:] == [
            "competidor", "advisor_correction", "validated"]
    finally:
        if otro is not almacen:
            otro.cerrar()


def test_conflicto_no_corrige_un_perfil_que_otro_ya_valido(api_perfil, monkeypatch):
    almacen = store._a()
    insertar = almacen.insertar_lote
    compitio = False

    def competir(perfiles):
        nonlocal compitio
        if not compitio:
            compitio = True
            store.validar(CLIENTE, "asesor-competidor")
        insertar(perfiles)

    monkeypatch.setattr(almacen, "insertar_lote", competir)
    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
    })
    assert respuesta.status_code == 409
    perfil = api_perfil.get(f"{RUTA}/profile").json()
    assert perfil["version"] == 2
    assert perfil["review"]["validated_by"] == "asesor-competidor"
    assert perfil["mifid"]["financial.debts_eur"]["value"] == 0
    assert [v["reason"] for v in api_perfil.get(f"{RUTA}/versions").json()][1:] == ["validated"]


def test_agotar_reintentos_da_409_sin_cambios_ni_eventos(api_perfil, eventos, monkeypatch):
    antes = instantanea(api_perfil)
    intentos = []

    def competir(perfiles):
        intentos.append(1)
        raise ConflictoVersion("competidor")

    monkeypatch.setattr(store._a(), "insertar_lote", competir)
    respuesta = api_perfil.post(f"{RUTA}/validate", json={
        "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
    })
    assert respuesta.status_code == 409
    assert len(intentos) == store.MAX_REINTENTOS
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()


def test_dos_asesores_simultaneos_solo_validan_una_vez(api_perfil):
    barrera = threading.Barrier(2)

    def validar(importe):
        barrera.wait(timeout=5)
        try:
            p = store.validar(CLIENTE, f"asesor-{importe}", [
                Parche(path="financial.debts_eur", value=importe, source="advisor")])
        except store.Conflicto:
            return None
        return p.mifid["financial.debts_eur"].value

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(validar, [1000, 2000]))
    assert resultados.count(None) == 1
    ganador = next(r for r in resultados if r is not None)
    perfil = api_perfil.get(f"{RUTA}/profile").json()
    assert perfil["version"] == 3 and perfil["status"] == "active"
    assert perfil["mifid"]["financial.debts_eur"]["value"] == ganador
    assert [v["reason"] for v in api_perfil.get(f"{RUTA}/versions").json()][1:] == [
        "advisor_correction", "validated"]


def test_sqlite_deshace_el_primer_insert_si_falla_el_segundo(eventos, api_perfil):
    almacen = store._a()
    if not isinstance(almacen, AlmacenBD):
        pytest.skip("fallo transaccional propio de SQLite")
    antes = instantanea(api_perfil)
    with almacen.motor.begin() as c:
        c.execute(text("CREATE TRIGGER fallo_validated BEFORE INSERT ON profile_versions "
                       "WHEN NEW.reason = 'validated' BEGIN SELECT RAISE(ABORT, 'fallo de prueba'); END"))
    with pytest.raises(IntegrityError, match="fallo de prueba"):
        api_perfil.post(f"{RUTA}/validate", json={
            "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
        })
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()
    # Comprobar también el archivo desde otro motor, fuera de la transacción fallida.
    otro = AlmacenBD.desde_url(str(almacen.motor.url))
    try:
        assert len(otro.historial(CLIENTE)) == len(antes["versions"])
    finally:
        otro.cerrar()


def test_sqlite_ocupado_da_409_sin_modificar_el_perfil(api_perfil, eventos):
    almacen = store._a()
    if not isinstance(almacen, AlmacenBD):
        pytest.skip("bloqueo de escritura propio de SQLite")
    antes = instantanea(api_perfil)

    def sin_espera(conexion, _registro, _proxy):
        conexion.execute("PRAGMA busy_timeout=0")

    event.listen(almacen.motor, "checkout", sin_espera)
    with almacen.motor.connect() as rival:
        rival.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            respuesta = api_perfil.post(f"{RUTA}/validate", json={
                "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
            })
            assert respuesta.status_code == 409
        finally:
            rival.rollback()
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()


@pytest.mark.parametrize("caso", ["guardar", "fallo-al-sustituir", "409", "422"])
def test_memoria_con_json_guarda_el_lote_entero_o_nada(almacen, tmp_path, monkeypatch, caso):
    from app.perfil.almacenes import memoria

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1")
    store.configurar("memoria")
    store.cargar_fixture(CLIENTE)
    with closing(cliente_autorizado()) as api:
        antes = instantanea(api)
        ruta = tmp_path / f"perfil_{CLIENTE}.json"
        original = ruta.read_bytes()
        cola = store.bus.suscribir(CLIENTE)
        try:
            if caso in ("409", "422"):
                respuesta = api.post(f"{RUTA}/validate", json={
                    "advisor_id": ASESOR, "changes": [
                        correccion("financial.net_monthly_income_eur", 1800),
                        correccion("financial.debts_eur", None if caso == "409" else "inválido")],
                })
                assert respuesta.status_code == int(caso)
                comprobar_sin_cambios(api, antes)
                assert ruta.read_bytes() == original
                assert cola.empty()
            elif caso == "fallo-al-sustituir":
                def fallo(_origen, _destino):
                    raise OSError("fallo de disco simulado")

                monkeypatch.setattr(memoria.os, "replace", fallo)
                with pytest.raises(OSError, match="fallo de disco simulado"):
                    api.post(f"{RUTA}/validate", json={
                        "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
                    })
                comprobar_sin_cambios(api, antes)
                assert ruta.read_bytes() == original
                assert cola.empty()
            else:
                respuesta = api.post(f"{RUTA}/validate", json={
                    "advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)],
                })
                comprobar_validado(api, respuesta)
                guardadas = json.loads(ruta.read_text())
                assert [v["reason"] for v in guardadas][-2:] == ["advisor_correction", "validated"]
            assert not list(tmp_path.glob(".perfil-*.tmp"))
            # Un almacén nuevo ve exactamente la misma versión que el proceso actual.
            recargado = AlmacenMemoria(tmp_path)
            assert recargado.ultima(CLIENTE).version == store.perfil(CLIENTE).version
        finally:
            store.bus.cancelar(CLIENTE, cola)


@pytest.mark.parametrize("codigo", ["40001", "40P01", "08006"])
def test_sqlstate_transitorio_reintenta_pero_otro_error_se_propaga(api_perfil, eventos, codigo):
    """Inyección de SQLSTATE: comprueba el tratamiento, no una conexión a PostgreSQL."""
    almacen = store._a()
    if not isinstance(almacen, AlmacenBD):
        pytest.skip("clasificación de fallos del almacén SQL")
    antes = instantanea(api_perfil)
    intentos = []

    class FalloPostgresSimulado(Exception):
        sqlstate = codigo

    def fallar(_conexion, _cursor, sentencia, _parametros, _contexto, _muchos):
        if sentencia.startswith("INSERT INTO profile_versions"):
            intentos.append(1)
            raise OperationalError(sentencia, None, FalloPostgresSimulado("fallo simulado"))

    event.listen(almacen.motor, "before_cursor_execute", fallar)
    cuerpo = {"advisor_id": ASESOR, "changes": [correccion("financial.debts_eur", 1000)]}
    if codigo == "08006":
        with pytest.raises(OperationalError):
            api_perfil.post(f"{RUTA}/validate", json=cuerpo)
        assert len(intentos) == 1
    else:
        respuesta = api_perfil.post(f"{RUTA}/validate", json=cuerpo)
        assert respuesta.status_code == 409
        assert len(intentos) == store.MAX_REINTENTOS
    comprobar_sin_cambios(api_perfil, antes)
    assert eventos.empty()
