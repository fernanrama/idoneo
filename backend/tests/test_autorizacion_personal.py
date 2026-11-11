"""Contrato de posesión y revisiones, con clientes ficticios y sin permisos implícitos del test."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import acceso, main, voz
from app.agentes import memoria
from app.main import app
from app.mcp import servidor
from app.perfil import store
from app.perfil.modelos import Parche
from tests.soporte_bd import ALMACENES_SQL, url_sql


@pytest.fixture(scope="session")
def contexto_api():
    # El SDK MCP permite iniciar su session manager una vez por instancia.
    with TestClient(app, base_url="http://localhost") as cliente:
        yield cliente


@pytest.fixture(params=["memoria", *ALMACENES_SQL])
def api(request, tmp_path, contexto_api):
    store.configurar("memoria" if request.param == "memoria" else "bd",
                     None if request.param == "memoria" else url_sql(request.param, tmp_path, "acceso_test.db"))
    yield contexto_api
    store.configurar("memoria")


def nueva(api):
    r = api.post("/api/sessions", json={"channel": "text"})
    assert r.status_code == 200
    s = r.json()
    return s, {"Authorization": f"Bearer {s['access_token']}"}


def ruta(s):
    return f"/api/sessions/{s['session_id']}/memory"


def guardar(api, s, headers, *, revision=0, datos=None):
    return api.put(ruta(s), headers={**headers, "If-Match": f'"personal-{revision}"'}, json={
        "consent_given": True, "updates": datos or {"communication": {"pace": "slow"}}, "forget": []})


def test_credencial_solo_se_emite_en_alta_exclusiva(api):
    a, ha = nueva(api)
    b, hb = nueva(api)
    assert a["client_id"] != b["client_id"]
    assert api.post("/api/sessions", json={"client_id": a["client_id"]}).status_code == 401
    assert api.post("/api/sessions", json={"client_id": a["client_id"]}, headers=hb).status_code == 404
    r = api.post("/api/sessions", json={"client_id": a["client_id"], "channel": "voice"}, headers=ha)
    assert r.status_code == 200 and "access_token" not in r.json()
    servicio = {"X-Admin-Token": "servicio-sintetico-de-pruebas"}
    r = api.post("/api/sessions", json={"client_id": a["client_id"]}, headers=servicio)
    assert r.status_code == 200 and "access_token" not in r.json()
    assert "access_token" not in api.get(f"/api/sessions/{a['session_id']}", headers=ha).json()
    assert a["access_token"] not in json.dumps(store.perfil(a["client_id"]).model_dump(mode="json"))


def test_sin_secreto_no_crea_clientes_ni_emite_credenciales(api, monkeypatch):
    llamadas = []
    original = store.crear_nuevo

    def observar(cid):
        llamadas.append(cid)
        return original(cid)

    monkeypatch.setattr(store, "crear_nuevo", observar)
    monkeypatch.delenv("CLIENT_ACCESS_SECRET")
    assert api.post("/api/sessions", json={}).status_code == 503
    assert llamadas == []


@pytest.mark.parametrize("duracion", ["0", "-1", "86401", "invalido"])
def test_configuracion_invalida_no_emite_acceso(api, monkeypatch, duracion):
    monkeypatch.setenv("CLIENT_ACCESS_TTL_S", duracion)
    assert api.post("/api/sessions", json={}).status_code == 503


@pytest.mark.parametrize("salida", ["profile", "versions", "constraints", "context", "evidence/financial.debts_eur"])
def test_lecturas_cliente_no_permiten_otro_propietario(api, salida):
    a, ha = nueva(api)
    b, hb = nueva(api)
    path = f"/api/clients/{b['client_id']}/{salida}"
    assert api.get(path).status_code == 401
    assert api.get(path, headers=ha).status_code == 404
    if salida.startswith("evidence"):
        assert api.get(path, headers=hb).status_code == 404  # cliente nuevo sin ese dato
    else:
        assert api.get(path, headers=hb).status_code == 200


@pytest.mark.parametrize("salida", ["", "/pending", "/memory"])
def test_conocer_session_id_no_da_acceso(api, salida):
    a, ha = nueva(api)
    b, hb = nueva(api)
    path = f"/api/sessions/{b['session_id']}{salida}"
    assert api.get(path).status_code == 401
    assert api.get(path, headers=ha).status_code == 404
    assert api.get(path, headers=hb).status_code == 200
    assert api.delete(ruta(b), headers={**ha, "If-Match": '"personal-0"'}).status_code == 404
    assert guardar(api, b, ha).status_code == 404


def test_contexto_y_llamadas_agentes_exigen_propietario_antes_de_usar_servicios(api, monkeypatch):
    a, ha = nueva(api)
    b, hb = nueva(api)

    async def no_llamar():
        raise AssertionError("Un acceso denegado no debe contactar ElevenLabs")

    monkeypatch.setattr(voz, "_url_firmada", no_llamar)
    assert api.get(f"/api/voice/context/{b['session_id']}").status_code == 401
    assert api.get(f"/api/voice/context/{b['session_id']}", headers=ha).status_code == 404
    assert api.get(f"/api/voice/context/{b['session_id']}", headers=hb).status_code == 200
    assert api.post("/api/voice/bootstrap", json={"session_id": b["session_id"]}, headers=ha).status_code == 404
    assert api.post(f"/api/sessions/{b['session_id']}/chat", json={}, headers=ha).status_code == 404
    assert api.post(f"/api/sessions/{b['session_id']}/turns", json={
        "speaker": "client", "text": "Ficticio", "t_start": 0, "t_end": 1}, headers=ha).status_code == 404


def test_credencial_alterada_y_caducada_no_se_aceptan_ni_se_registran(api, monkeypatch, caplog):
    s, headers = nueva(api)
    token = s["access_token"]
    alterada = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert api.get(ruta(s), headers={"Authorization": f"Bearer {alterada}"}).status_code == 401
    momento = acceso.time.time()
    monkeypatch.setattr(acceso.time, "time", lambda: momento + 28801)
    assert api.get(ruta(s), headers=headers).status_code == 401
    assert token not in caplog.text and alterada not in caplog.text


@pytest.mark.parametrize("cabecera", ["*", 'W/"personal-0"', '"personal-0", "personal-1"', "personal-0", '"personal--1"'])
def test_if_match_ambiguo_o_invalido_no_modifica(api, cabecera):
    s, headers = nueva(api)
    assert api.put(ruta(s), headers={**headers, "If-Match": cabecera}, json={
        "consent_given": True, "updates": {}, "forget": []}).status_code == 412
    assert store.personal(s["client_id"]) is None


def test_revision_obligatoria_consentimiento_y_borrado_sin_resurreccion(api):
    s, headers = nueva(api)
    path = ruta(s)
    vista = api.get(path, headers=headers)
    assert vista.json() == {"enabled": False, "version": 0, "data": {}}
    assert vista.headers["ETag"] == '"personal-0"'
    cuerpo = {"consent_given": True, "updates": {"concerns": ["Preferencia ficticia anterior"]}, "forget": []}
    assert api.put(path, headers=headers, json=cuerpo).status_code == 428
    assert api.delete(path, headers=headers).status_code == 428
    primera = guardar(api, s, headers, datos=cuerpo["updates"])
    assert primera.status_code == 200 and primera.headers["ETag"] == '"personal-1"'
    assert guardar(api, s, headers, revision=0).status_code == 412
    assert api.delete(path, headers={**headers, "If-Match": '"personal-0"'}).status_code == 412
    borrado = api.delete(path, headers={**headers, "If-Match": '"personal-1"'})
    assert borrado.status_code == 200
    assert borrado.json() == {"enabled": False, "version": 2, "data": {}, "deleted_versions": 1}
    assert borrado.headers["ETag"] == '"personal-2"'
    assert api.put(path, headers={**headers, "If-Match": '"personal-1"'}, json=cuerpo).status_code == 412
    repetido = api.delete(path, headers={**headers, "If-Match": '"personal-2"'})
    assert repetido.json()["version"] == 2 and repetido.json()["deleted_versions"] == 0
    for consentimiento in [False, 1, "true"]:
        assert api.put(path, headers={**headers, "If-Match": '"personal-2"'}, json={
            "consent_given": consentimiento, "updates": {}, "forget": []}).status_code == 422
    nueva_vista = guardar(api, s, headers, revision=2)
    assert nueva_vista.status_code == 200 and nueva_vista.json()["version"] == 3
    assert "concerns" not in nueva_vista.json()["data"]


def test_delete_devuelve_el_snapshot_confirmado_aunque_haya_otro_put(api, monkeypatch):
    s, headers = nueva(api)
    assert guardar(api, s, headers).status_code == 200
    original = store.revocar_personal

    def borrar_y_otra_aceptacion(cid, **kwargs):
        borradas, capa = original(cid, **kwargs)
        store.actualizar_personal(cid, {"concerns": ["Aceptación posterior ficticia"]}, [], "agent:memory",
                                 version_esperada=capa.version, consentimiento=True)
        return borradas, capa

    monkeypatch.setattr(store, "revocar_personal", borrar_y_otra_aceptacion)
    r = api.delete(ruta(s), headers={**headers, "If-Match": '"personal-1"'})
    assert r.status_code == 200 and r.json()["enabled"] is False
    assert r.json()["version"] == 2 and r.headers["ETag"] == '"personal-2"'
    assert store.personal(s["client_id"]).version == 3  # la respuesta no mezcla otra operación


def test_cache_etag_cors_y_autor_no_controlado_por_cliente(api):
    s, headers = nueva(api)
    r = api.get(ruta(s), headers={**headers, "Origin": "http://localhost:3000"})
    assert r.headers["Cache-Control"] == "no-store"
    assert "etag" in r.headers["Access-Control-Expose-Headers"].lower()
    assert api.put(ruta(s), headers={**headers, "If-Match": r.headers["ETag"]}, json={
        "consent_given": True, "updates": {}, "forget": [], "author": "advisor:falso"}).status_code == 422


def test_demo_fija_no_lee_memoria_ni_modifica_cliente_persistido(api, monkeypatch):
    store.cargar_fixture("carmen-68")
    store.guardar_personal("carmen-68", {"concerns": ["DATO-PERSONAL-FICTICIO-NO-PUBLICO"]}, True, "system")
    store.aplicar("carmen-68", [Parche(path="financial.liquid_savings_eur", value=123, source="advisor")],
                  "Corrección ficticia", "advisor:prueba")
    antes = store.perfil("carmen-68").model_dump(mode="json")
    historia = store.versiones("carmen-68")
    r = api.get("/api/demo/profile")
    assert r.status_code == 200 and r.json()["personal"] == {}
    assert r.json()["mifid"]["financial.liquid_savings_eur"]["value"] == 80000
    assert "DATO-PERSONAL-FICTICIO-NO-PUBLICO" not in r.text
    assert api.get("/api/demo/constraints").json()["usable"] is False
    assert store.perfil("carmen-68").model_dump(mode="json") == antes
    assert store.versiones("carmen-68") == historia
    monkeypatch.setenv("DEMO_ENDPOINTS", "0")
    assert api.get("/api/demo/profile").status_code == 404
    assert api.get("/api/demo/constraints").status_code == 404


def test_validar_requiere_propietario_y_servicio_separadamente(api):
    store.cargar_fixture("carmen-68")
    owner = {"Authorization": f"Bearer {acceso.emitir_credencial('carmen-68')}"}
    service = {"X-Admin-Token": "servicio-sintetico-de-pruebas"}
    path = "/api/clients/carmen-68/validate"
    assert api.post(path, headers=owner, json={"advisor_id": "demo"}).status_code == 401
    assert api.post(path, headers=service, json={"advisor_id": "demo"}).status_code == 401
    otro, headers_otro = nueva(api)
    assert api.post(path, headers={**headers_otro, **service}, json={"advisor_id": "demo"}).status_code == 404
    assert api.post(path, headers={**owner, **service}, json={"advisor_id": "demo"}).status_code == 200


@pytest.mark.parametrize("herramienta", ["get_client_profile", "get_investment_constraints", "get_evidence", "get_client_context"])
def test_mcp_protege_transporte_y_cliente_de_cada_herramienta(api, herramienta):
    a, ha = nueva(api)
    b, hb = nueva(api)
    assert guardar(api, b, hb, datos={"concerns": ["NO-EXPOSICION-FICTICIA"]}).status_code == 200
    argumentos = {"client_id": b["client_id"]}
    if herramienta == "get_evidence":
        argumentos["field"] = "financial.debts_eur"
    mensaje = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": herramienta, "arguments": argumentos}}
    accept = {"Accept": "application/json, text/event-stream"}
    assert api.post("/mcp", headers=accept, json=mensaje).status_code == 401
    prohibido = api.post("/mcp", headers={**ha, **accept}, json=mensaje)
    assert prohibido.status_code == 200 and prohibido.json()["result"]["isError"] is True
    assert "NO-EXPOSICION-FICTICIA" not in prohibido.text
    permitido = api.post("/mcp", headers={**hb, **accept}, json=mensaje)
    assert permitido.status_code == 200 and not permitido.json()["result"].get("isError")
    if herramienta == "get_client_profile":
        assert "NO-EXPOSICION-FICTICIA" in permitido.text
    servicio = api.post("/mcp", headers={**accept, "X-Admin-Token": "servicio-sintetico-de-pruebas"}, json=mensaje)
    assert servicio.status_code == 200 and not servicio.json()["result"].get("isError")


def test_mcp_invocado_sin_request_no_omite_autorizacion(api):
    s, headers = nueva(api)
    with pytest.raises(HTTPException) as error:
        servidor.get_client_profile(s["client_id"])
    assert error.value.status_code == 401


def test_legacy_legible_no_se_proyecta_sin_tipo_y_limites_validos():
    datos = {"consent": {"given": True}, "communication": {"pace": "infinito", "channel": "email",
             "campo_antiguo": "NO-ENVIAR"}, "concerns": ["x" * 301], "tax": "NO-ENVIAR"}
    texto = memoria.contexto(datos)
    assert "email" in texto
    assert "infinito" not in texto and "NO-ENVIAR" not in texto and "x" * 301 not in texto
