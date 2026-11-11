"""Modo asesor de demostración: permitido solo con su autorización, en local y para clientes ficticios.

Todo con material sintético. Ningún test llama a proveedores, a Supabase ni a los puertos de la demo.
Se repite con memoria y SQLite (MODULOS_CONTRATO).
"""

from __future__ import annotations

import asyncio
import json
import os

import pytest
from fastapi.testclient import TestClient

from app import acceso
from app.main import app
from app.mcp.servidor import mcp
from app.perfil import store
from app.perfil.modelos import Fuente, Parche

C = "carmen-68"
BASE = "/api/demo/asesor"
TOKEN = "asesor-demo-sintetico-solo-para-tests-0123456789"
LOCAL = ("127.0.0.1", 51000)


@pytest.fixture
def modo(monkeypatch):
    monkeypatch.setenv("DEMO_ADVISOR_MODE", "1")
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", TOKEN)
    monkeypatch.delenv("DEMO_ADVISOR_CLIENTS", raising=False)
    monkeypatch.delenv("DEMO_ADVISOR_ID", raising=False)
    store.reiniciar()
    store.cargar_fixture(C)


def local(**kw) -> TestClient:
    return TestClient(app, base_url="http://localhost", client=LOCAL, **kw)


def asesor() -> dict[str, str]:
    return {"X-Demo-Advisor-Token": TOKEN}


def rutas(cid: str = C) -> list[tuple[str, str]]:
    return [("GET", f"{BASE}/estado"), ("GET", f"{BASE}/clientes/{cid}"),
            ("POST", f"{BASE}/clientes/{cid}/validar"), ("POST", f"{BASE}/clientes/{cid}/reiniciar")]


def version() -> int:
    return store.perfil(C).version


def mcp_constraints() -> dict:
    res = asyncio.run(mcp.call_tool("get_investment_constraints", {"client_id": C}))
    bloques = res[0] if isinstance(res, tuple) else res
    return json.loads(bloques[0].text)


# ---------- apagado por defecto ----------

def test_apagado_por_defecto_las_rutas_no_existen(monkeypatch):
    monkeypatch.delenv("DEMO_ADVISOR_MODE", raising=False)
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", TOKEN)
    store.reiniciar()
    store.cargar_fixture(C)
    c = local()
    for metodo, ruta in rutas():
        assert c.request(metodo, ruta, headers=asesor()).status_code == 404
    assert store.perfil(C).status.value == "pending_validation" and version() == 1


@pytest.mark.parametrize("valor", ["0", "true", "yes", "", "1 # no"])
def test_solo_el_valor_exacto_1_lo_activa(monkeypatch, valor):
    monkeypatch.setenv("DEMO_ADVISOR_MODE", valor)
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", TOKEN)
    assert local().get(f"{BASE}/estado", headers=asesor()).status_code == 404


# ---------- recorrido permitido ----------

def test_recorrido_de_carmen_hasta_validado_y_disponible_por_mcp(modo, mcp_servicio):
    c = local()
    estado = c.get(f"{BASE}/estado", headers=asesor())
    assert estado.status_code == 200 and estado.headers["Cache-Control"] == "no-store"
    assert estado.json() == {"enabled": True, "simulated": True, "clients": [C, "carmen-corta"], "advisor_id": "asesor-demo"}
    assert TOKEN not in estado.text

    antes = c.get(f"{BASE}/clientes/{C}", headers=asesor()).json()
    assert antes["profile"]["status"] == "pending_validation" and antes["constraints"]["usable"] is False
    assert antes["profile"]["personal"] == {}
    assert mcp_constraints()["usable"] is False

    r = c.post(f"{BASE}/clientes/{C}/validar", headers=asesor())
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["status"] == "active" and p["version"] == 2 and p["review"]["validated_by"] == "asesor-demo"
    assert all(a["status"] == "resolved" and a["resolved_by"] == "advisor:asesor-demo" for a in p["alerts"])

    despues = c.get(f"{BASE}/clientes/{C}", headers=asesor()).json()
    assert despues["constraints"]["usable"] is True and despues["constraints"]["profile_version"] == 2
    assert [v["reason"] for v in despues["versions"]][-1] == "validated"
    # Lo mismo que ve el agente de la entidad por MCP y por REST con su credencial de servicio.
    assert mcp_constraints()["usable"] is True and mcp_constraints()["funds_query"]["max_risk"] == 3
    rest = TestClient(app).get(f"/api/clients/{C}/constraints",
                               headers={"X-Admin-Token": os.environ["ADMIN_TOKEN"]}).json()
    assert rest["usable"] is True and rest["profile_version"] == 2


def test_validar_reutiliza_la_validacion_atomica(modo):
    c = local()
    assert c.post(f"{BASE}/clientes/{C}/validar", headers=asesor()).status_code == 200
    # Segunda vez: el perfil ya está activo. 409 y ninguna versión nueva.
    r = c.post(f"{BASE}/clientes/{C}/validar", headers=asesor())
    assert r.status_code == 409 and version() == 2


def test_perfil_incompleto_no_se_valida_ni_crea_versiones(modo):
    store.aplicar(C, [Parche(path="objectives.o1.goal", value=None, source=Fuente.advisor)],
                  "dato retirado para el test", "advisor:test")
    v = version()
    r = local().post(f"{BASE}/clientes/{C}/validar", headers=asesor())
    assert r.status_code == 409 and "objectives.o1.goal" in r.json()["detail"]
    assert version() == v and store.perfil(C).status.value == "draft"


def test_reiniciar_abre_una_epoca_nueva_sin_borrar_historial(modo, mcp_servicio):
    c = local()
    c.post(f"{BASE}/clientes/{C}/validar", headers=asesor())
    r = c.post(f"{BASE}/clientes/{C}/reiniciar", headers=asesor())
    assert r.status_code == 200 and r.json()["status"] == "pending_validation" and r.json()["version"] == 3
    assert mcp_constraints()["usable"] is False
    assert [v["version"] for v in store.versiones(C)] == [1, 2, 3]
    assert c.post(f"{BASE}/clientes/{C}/validar", headers=asesor()).status_code == 200


# ---------- intentos no autorizados ----------

def test_sin_token_o_con_token_incorrecto_401_y_nada_cambia(modo):
    c = local()
    sid = store.crear_sesion(C, "text")["session_id"]
    bearer = acceso.emitir_credencial(C)
    intentos = [
        {},
        {"X-Demo-Advisor-Token": TOKEN[:-1] + "x"},
        {"X-Demo-Advisor-Token": bearer},                          # token personal del cliente
        {"X-Demo-Advisor-Token": C},                               # client_id
        {"X-Demo-Advisor-Token": sid},                             # session_id
        {"X-Demo-Advisor-Token": os.environ["ADMIN_TOKEN"]},       # credencial de servicio
        {"Authorization": f"Bearer {bearer}"},                     # Bearer en su cabecera normal
        {"Authorization": f"Bearer {TOKEN}"},                      # el token de asesor, pero en otra cabecera
        {"X-Admin-Token": os.environ["ADMIN_TOKEN"]},
    ]
    v = version()
    for cabeceras in intentos:
        for metodo, ruta in rutas():
            r = c.request(metodo, ruta, headers=cabeceras)
            assert r.status_code == 401, (cabeceras, ruta, r.status_code)
            assert TOKEN not in r.text
    assert version() == v and store.perfil(C).status.value == "pending_validation"


def test_el_token_de_asesor_no_sirve_en_las_rutas_del_cliente_ni_del_servicio(modo):
    c = local()
    assert c.get(f"/api/clients/{C}/profile", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 401
    assert c.post(f"/api/clients/{C}/validate", headers={"Authorization": f"Bearer {TOKEN}", "X-Admin-Token": TOKEN},
                  json={"advisor_id": "intruso", "changes": []}).status_code == 401
    assert c.post("/api/demo/reset", headers={"X-Admin-Token": TOKEN}).status_code == 401
    assert c.post("/mcp", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 401
    assert version() == 1


def test_solo_clientes_ficticios_de_la_lista(modo):
    real = store.crear_nuevo("cliente-0a1b2c3d4e5f")
    c = local()
    for metodo, ruta in rutas(real.client_id)[1:]:
        assert c.request(metodo, ruta, headers=asesor()).status_code == 404
    assert store.perfil(real.client_id).version == 1


@pytest.mark.parametrize("cliente,cabeceras", [
    (("192.168.1.20", 51000), {}),                                  # otra máquina de la red
    (("10.0.0.7", 51000), {"Host": "localhost"}),                   # Host falseado desde fuera
    (LOCAL, {"Host": "idoneo.example.com"}),                        # dominio público
    (LOCAL, {"X-Forwarded-For": "203.0.113.9"}),                    # detrás de un proxy
    (LOCAL, {"X-Forwarded-Host": "localhost"}),
    (LOCAL, {"Forwarded": "for=203.0.113.9"}),
    (LOCAL, {"X-Real-IP": "127.0.0.1"}),
])
def test_solo_local_sin_proxy(modo, cliente, cabeceras):
    c = TestClient(app, base_url="http://localhost", client=cliente)
    for metodo, ruta in rutas():
        r = c.request(metodo, ruta, headers={**asesor(), **cabeceras})
        assert r.status_code == 403, (cliente, cabeceras, ruta)
    assert version() == 1


def test_loopback_ipv6_y_mapeado_se_aceptan(modo):
    for ip in ("::1", "::ffff:127.0.0.1"):
        c = TestClient(app, base_url="http://127.0.0.1:8000", client=(ip, 51000))
        assert c.get(f"{BASE}/estado", headers=asesor()).status_code == 200


# ---------- configuración insegura ----------

@pytest.mark.parametrize("variable", ["ADMIN_TOKEN", "CLIENT_ACCESS_SECRET", "VOICE_USER_ID_SECRET"])
def test_token_igual_a_otro_secreto_no_se_acepta(modo, monkeypatch, variable):
    monkeypatch.setenv(variable, TOKEN)
    r = local().get(f"{BASE}/estado", headers=asesor())
    assert r.status_code == 503 and TOKEN not in r.text


def test_token_corto_no_se_acepta(modo, monkeypatch):
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", "corto")
    assert local().get(f"{BASE}/estado", headers={"X-Demo-Advisor-Token": "corto"}).status_code == 503


@pytest.mark.parametrize("lista", ["cliente-real", "carmen-68,cliente-real", "../carmen-68", " , "])
def test_lista_con_clientes_no_ficticios_no_se_acepta(modo, monkeypatch, lista):
    monkeypatch.setenv("DEMO_ADVISOR_CLIENTS", lista)
    assert local().get(f"{BASE}/estado", headers=asesor()).status_code == 503


def test_un_fixture_sin_marca_de_datos_simulados_no_cuenta(modo, monkeypatch, tmp_path):
    (tmp_path / "cliente-x.json").write_text(json.dumps({"client_id": "cliente-x", "reason": "expediente real"}))
    monkeypatch.setattr(store, "FIXTURES_DIR", tmp_path)
    monkeypatch.setenv("DEMO_ADVISOR_CLIENTS", "cliente-x")
    assert local().get(f"{BASE}/estado", headers=asesor()).status_code == 503


def test_asesor_id_invalido_no_se_acepta(modo, monkeypatch):
    monkeypatch.setenv("DEMO_ADVISOR_ID", "no válido")
    assert local().get(f"{BASE}/estado", headers=asesor()).status_code == 503
