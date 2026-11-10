"""Regresiones de los defectos reproducidos primero sobre #21.

Las peticiones ahora llevan revisión esperada y consentimiento explícito.
Solo datos sintéticos, memoria y SQLite temporal; no se llama a agentes ni a la demo.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert, select

from app.main import app
from app.perfil import store
from app.perfil.modelos import ahora
from app.perfil.persistencia.tablas import personal_versions

C = "memoria-personal-prueba"
AUTOR = "agent:memory"


@pytest.fixture(params=["memoria", "sqlite"])
def personal_almacen(request, tmp_path):
    if request.param == "sqlite":
        store.configurar("bd", f"sqlite:///{tmp_path / 'personal_test.db'}")
    else:
        store.configurar("memoria")
    store.crear(C)
    yield request.param
    store.configurar("memoria")


@pytest.fixture(params=["json", "sqlite"])
def personal_legado(request, tmp_path, monkeypatch):
    """Representa un registro que el modelo anterior a #21 admitía sin conversión."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1" if request.param == "json" else "0")
    url = f"sqlite:///{tmp_path / 'legado_test.db'}"
    store.configurar("memoria" if request.param == "json" else "bd", None if request.param == "json" else url)
    store.crear(C)

    def insertar(datos):
        momento = ahora()
        fila = {"client_id": C, "version": 1, "consent_given": True,
                "consent_at": momento, "data": datos, "author": "system", "created_at": momento}
        if request.param == "sqlite":
            with store._a().motor.begin() as conexion:
                conexion.execute(insert(personal_versions).values(**fila))
        else:
            fila_json = {**fila, "consent_at": momento.isoformat(), "created_at": momento.isoformat()}
            (tmp_path / f"personal_{C}.json").write_text(json.dumps([fila_json]), encoding="utf-8")
            store.configurar("memoria")  # obliga a leer el archivo con el modelo de #21

    yield insertar
    store.configurar("memoria")


def _historial_personal() -> list[dict]:
    almacen = store._a()
    if almacen.tipo == "memoria":
        return [c.model_dump() for c in almacen._personal.get(C, [])]
    with almacen.motor.connect() as conexion:
        return [dict(f._mapping) for f in conexion.execute(
            select(personal_versions).where(personal_versions.c.client_id == C)
            .order_by(personal_versions.c.version))]


def test_put_retrasado_no_reactiva_memoria_borrada(personal_almacen):
    primera = store.actualizar_personal(C, {"communication": {"pace": "slow"}}, [], AUTOR,
                                        version_esperada=0, consentimiento=True)
    store.borrar_personal(C, version_esperada=primera.version)
    with pytest.raises(store.RevisionObsoleta):
        store.actualizar_personal(C, {"communication": {"pace": "slow"}}, [], AUTOR,
                                  version_esperada=primera.version, consentimiento=True)
    assert not store.personal(C).consent_given


def test_actualizacion_y_borrado_no_restauran_la_copia_anterior(personal_almacen, monkeypatch):
    store.guardar_personal(C, {"concerns": ["Dato sintético que se quiere borrar"]}, True, AUTOR)
    copia_leida, continuar, borrado_iniciado, borrado_terminado = Event(), Event(), Event(), Event()
    original = store._guardar_capa

    def guardar_pausado(*args, **kwargs):
        copia_leida.set()  # actualizar_personal ya ha copiado previa.data
        if not continuar.wait(5):
            raise TimeoutError("No se liberó la actualización de prueba")
        return original(*args, **kwargs)

    def borrar():
        borrado_iniciado.set()
        try:
            # Revocación interna trusted; comprueba la exclusión mutua del almacén.
            return store.borrar_personal_interno(C)
        finally:
            borrado_terminado.set()

    monkeypatch.setattr(store, "_guardar_capa", guardar_pausado)
    with ThreadPoolExecutor(max_workers=2) as hilos:
        actualizacion = hilos.submit(store.actualizar_personal, C,
                                     {"communication": {"pace": "slow"}}, [], AUTOR,
                                     version_esperada=1, consentimiento=True)
        try:
            assert copia_leida.wait(5), "La actualización no alcanzó el punto de intercalado"
            eliminacion = hilos.submit(borrar)
            assert borrado_iniciado.wait(5)
            # Un borrado que pudiera adelantarse se detecta al comprobar el estado
            # final. No se exige que el planificador ejecute el hilo en cierto plazo.
            borrado_terminado.wait(0.05)
        finally:
            continuar.set()
        actualizacion.result(timeout=5)
        eliminacion.result(timeout=5)

    capa = store.personal(C)
    assert capa is None or not capa.consent_given, "La copia anterior al borrado reaparece consentida"


def test_el_borrado_no_reinicia_la_revision_personal(personal_almacen):
    store.guardar_personal(C, {"communication": {"pace": "slow"}}, True, AUTOR)
    anterior = store.actualizar_personal(C, {"communication": {"pace": "fast"}}, [], AUTOR,
                                         version_esperada=1, consentimiento=True)
    store.borrar_personal(C, version_esperada=anterior.version)
    nueva = store.guardar_personal(C, {"communication": {"pace": "normal"}}, True, AUTOR)
    assert nueva.version > anterior.version, "Se reutiliza una revisión anterior al borrado"


@pytest.mark.parametrize("datos", [
    {"concerns": "Prefiero respuestas breves"},
    {"communication": "email"},
    {"communication": {"channel": "email", "preferencia_antigua": "Conservar sin interpretar"}},
    {"exclusions": ["x" * 301]},
])
def test_registros_del_contrato_anterior_siguen_legibles(personal_legado, datos):
    personal_legado(datos)
    assert store.personal(C).data == datos
    assert store.perfil(C).personal["consent"]["given"] is True


def test_editar_otro_bloque_no_rechaza_ni_pierde_datos_antiguos(personal_legado):
    datos = {"communication": {"channel": "email", "preferencia_antigua": "Conservar sin interpretar"}}
    personal_legado(datos)
    capa = store.actualizar_personal(C, {"concerns": ["Preferencia nueva sintética"]}, [], AUTOR,
                                     version_esperada=1, consentimiento=True)
    assert capa.data["communication"] == datos["communication"], "Se descarta una clave antigua al editar otro bloque"


@pytest.mark.parametrize("consentimiento", [None, False])
def test_api_exige_consentimiento_explicito_sin_escribir(personal_almacen, consentimiento):
    api = TestClient(app)
    sesion = api.post("/api/sessions", json={}).json()
    cuerpo = {"updates": {"communication": {"pace": "slow"}}, "forget": []}
    if consentimiento is not None:
        cuerpo["consent_given"] = consentimiento
    r = api.put(f"/api/sessions/{sesion['session_id']}/memory", json=cuerpo,
                headers={"Authorization": f"Bearer {sesion['access_token']}", "If-Match": '"personal-0"'})
    assert r.status_code == 422
    assert store.personal(sesion["client_id"]) is None


def test_edicion_conserva_consentimiento_e_historial_personal(personal_almacen):
    primera = store.guardar_personal(C, {"communication": {"pace": "slow"}}, True, AUTOR)
    segunda = store.actualizar_personal(C, {"communication": {"pace": "fast"}}, [], AUTOR,
                                        version_esperada=1, consentimiento=True)
    repetida = store.actualizar_personal(C, {"communication": {"pace": "fast"}}, [], AUTOR,
                                         version_esperada=segunda.version, consentimiento=True)
    assert segunda.consent_at == primera.consent_at
    assert repetida.version == segunda.version == primera.version + 1
    historia = _historial_personal()
    assert [h["version"] for h in historia] == [1, 2]
    assert historia[0]["data"] == primera.data and historia[1]["data"] == segunda.data
    assert all(h["consent_given"] for h in historia)


def test_memoria_no_altera_mifid_evidencias_ni_historial(personal_almacen):
    store.cargar_fixture("carmen-68")
    antes = store.perfil("carmen-68").model_dump(exclude={"personal"})
    historia = store.versiones("carmen-68")
    store.guardar_personal("carmen-68", {"communication": {"pace": "slow"}}, True, AUTOR)
    store.actualizar_personal("carmen-68", {"concerns": ["Preferencia sintética"]}, [], AUTOR,
                              version_esperada=1, consentimiento=True)
    store.borrar_personal("carmen-68", version_esperada=2)
    assert store.perfil("carmen-68").model_dump(exclude={"personal"}) == antes
    assert store.perfil("carmen-68", 1).model_dump(exclude={"personal"}) == antes
    assert store.versiones("carmen-68") == historia


def test_fallo_de_json_personal_no_deja_cambios_en_memoria(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_PERSIST", "1")
    store.configurar("memoria")
    store.crear(C)
    primera = store.guardar_personal(C, {"communication": {"pace": "slow"}}, True, AUTOR)
    ruta = tmp_path / f"personal_{C}.json"
    disco_antes = ruta.read_bytes()
    original = os.replace

    def fallar(origen, destino, *args, **kwargs):
        if Path(destino) == ruta:
            raise OSError("fallo de escritura simulado")
        return original(origen, destino, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fallar)
    with pytest.raises(OSError, match="simulado"):
        store.actualizar_personal(C, {"communication": {"pace": "fast"}}, [], AUTOR,
                                  version_esperada=1, consentimiento=True)
    assert ruta.read_bytes() == disco_antes
    assert store.personal(C).model_dump() == primera.model_dump(), "La operación fallida alteró la memoria"
