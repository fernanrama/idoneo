"""Contrato del MCP para el pitch con la credencial fija de demostración (mcp/demo.py). Nunca en la URL.

Sin servicios externos: el protocolo completo se prueba contra un uvicorn local en un puerto efímero,
con las claves de proveedores vacías y datos simulados. Nunca usa los puertos 3000/8000.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app import acceso, demo_autorizaciones
from app.main import app
from app.mcp import demo
from app.mcp.servidor import mcp
from app.perfil import store

C = "carmen-68"
TOKEN = "mcp-demo-sintetico-solo-para-tests-0123456789abc"
ASESOR = "asesor-demo-sintetico-del-test-mcp-0123456789"
BACKEND = Path(__file__).resolve().parents[1]
ACEPTA = {"Accept": "application/json, text/event-stream"}
HERRAMIENTAS = {"get_client_profile", "get_investment_constraints", "get_evidence", "get_client_context"}


@pytest.fixture
def activa(monkeypatch):
    monkeypatch.setenv("MCP_DEMO_TOKEN", TOKEN)
    monkeypatch.delenv("MCP_DEMO_CLIENTS", raising=False)
    demo_autorizaciones.revocar_todo()
    store.reiniciar()
    store.cargar_fixture(C)


# ---------- configuración ----------

def test_desactivada_por_defecto(monkeypatch):
    monkeypatch.delenv("MCP_DEMO_TOKEN", raising=False)
    assert demo.configuracion() is None and not demo.es_token(TOKEN) and not demo.permite(C)


@pytest.mark.parametrize("variable", ["ADMIN_TOKEN", "CLIENT_ACCESS_SECRET", "VOICE_USER_ID_SECRET", "DEMO_ADVISOR_TOKEN"])
def test_no_puede_coincidir_con_otro_secreto(activa, monkeypatch, variable):
    monkeypatch.setenv(variable, TOKEN)
    assert demo.configuracion() is None and not demo.es_token(TOKEN)


@pytest.mark.parametrize("token", ["corto", "x" * 31, "con espacios " + "x" * 40, "con/barra/" + "x" * 40])
def test_token_inseguro_la_desactiva(monkeypatch, token):
    monkeypatch.setenv("MCP_DEMO_TOKEN", token)
    assert demo.configuracion() is None and not demo.es_token(token)


@pytest.mark.parametrize("lista", ["cliente-real", "carmen-68,cliente-real", "../carmen-68", " , "])
def test_solo_clientes_ficticios(activa, monkeypatch, lista):
    monkeypatch.setenv("MCP_DEMO_CLIENTS", lista)
    assert demo.configuracion() is None


def test_configuracion_valida(activa):
    conf = demo.configuracion()
    assert conf and conf.clientes == {C, "carmen-corta"} and demo.es_token(TOKEN) and not demo.es_token(TOKEN + "x")


# ---------- la credencial no sirve fuera de /mcp ----------

def test_no_abre_ninguna_ruta_rest(activa):
    c = TestClient(app)
    b = {"Authorization": f"Bearer {TOKEN}"}
    assert c.get(f"/api/clients/{C}/profile", headers=b).status_code == 401
    assert c.get(f"/api/clients/{C}/constraints", headers=b).status_code == 401
    assert c.post(f"/api/clients/{C}/validate", headers=b, json={"advisor_id": "x", "changes": []}).status_code == 401
    assert c.post("/api/demo/reset", headers={"X-Admin-Token": TOKEN}).status_code == 401
    assert c.post("/api/sessions", headers=b, json={"client_id": C}).status_code == 401
    assert store.perfil(C).version == 1


def test_transporte_sin_credencial_o_incorrecta(activa):
    c = TestClient(app)
    for cab in [{}, {"Authorization": "Bearer otra-cosa"}, {"Authorization": f"Bearer {TOKEN}x"}, {"X-Admin-Token": TOKEN}]:
        assert c.post("/mcp", headers={**ACEPTA, **cab}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).status_code == 401


def test_desactivada_el_token_no_abre_el_transporte(monkeypatch):
    monkeypatch.delenv("MCP_DEMO_TOKEN", raising=False)
    r = TestClient(app).post("/mcp", headers={**ACEPTA, "Authorization": f"Bearer {TOKEN}"},
                             json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code == 401


def test_un_token_en_la_url_nunca_autentica(activa, monkeypatch):
    c = TestClient(app, base_url="http://localhost", client=("127.0.0.1", 50000))
    cuerpo = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    monkeypatch.setenv("MCP_DEMO_URL_TOKEN", "1")  # la variable antigua ya no existe: se ignora
    for ruta in (f"/mcp/{TOKEN}", f"/mcp/{TOKEN}/", f"/mcp?token={TOKEN}", f"/mcp/{os.environ['ADMIN_TOKEN']}"):
        assert c.post(ruta, headers=ACEPTA, json=cuerpo).status_code in (401, 404), ruta


def test_credencial_de_demo_solo_desde_local(activa):
    cuerpo = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    b = {**ACEPTA, "Authorization": f"Bearer {TOKEN}"}
    for cliente, extra in [(("192.168.1.20", 50000), {}), (("127.0.0.1", 50000), {"X-Forwarded-For": "203.0.113.9"}),
                           (("127.0.0.1", 50000), {"Host": "idoneo.example.com"}), (("10.0.0.7", 50000), {"Host": "localhost"})]:
        r = TestClient(app, base_url="http://localhost", client=cliente).post("/mcp", headers={**b, **extra}, json=cuerpo)
        assert r.status_code == 403, (cliente, extra)


# ---------- herramientas (en proceso) ----------

def _con_bearer(monkeypatch, valor: str):
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {valor}".encode())]})
    monkeypatch.setattr(mcp, "get_context", lambda: SimpleNamespace(request_context=SimpleNamespace(request=request)))


def _llamar(nombre: str, **args):
    res = asyncio.run(mcp.call_tool(nombre, args))
    bloques = res[0] if isinstance(res, tuple) else res
    return json.loads(bloques[0].text)


def test_herramientas_con_la_credencial_solo_para_carmen(activa, monkeypatch):
    real = store.crear_nuevo("cliente-0a1b2c3d4e5f")
    _con_bearer(monkeypatch, TOKEN)
    assert _llamar("get_investment_constraints", client_id=C)["usable"] is False
    for nombre, args in [("get_client_profile", {}), ("get_investment_constraints", {}),
                         ("get_evidence", {"field": "financial.liquid_savings_eur"}), ("get_client_context", {})]:
        with pytest.raises(Exception, match="404"):
            _llamar(nombre, client_id=real.client_id, **args)


def test_las_cuatro_herramientas_se_declaran_de_solo_lectura():
    herramientas = asyncio.run(mcp.list_tools())
    assert {t.name for t in herramientas} == HERRAMIENTAS
    for t in herramientas:
        a = t.annotations
        assert a.readOnlyHint is True and a.destructiveHint is False and a.openWorldHint is False, t.name


# ---------- protocolo completo contra uvicorn local ----------

def _puerto() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    puerto = _puerto()
    assert puerto not in (3000, 8000)
    entorno = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC", "ELEVENLABS", "TEST_POSTGRES", "MCP_DEMO"))}
    entorno.update(ANTHROPIC_API_KEY="", ELEVENLABS_API_KEY="", ELEVENLABS_AGENT_ID="", DATABASE_URL="",
                   PERFIL_ALMACEN="memoria", DATA_PERSIST="0", LOAD_DEMO_FIXTURE="1",
                   CLIENT_ACCESS_SECRET="material-sintetico-del-test-mcp-0123456789", ADMIN_TOKEN="servicio-del-test-mcp",
                   MCP_DEMO_TOKEN=TOKEN, DEMO_ADVISOR_MODE="1", DEMO_ADVISOR_TOKEN=ASESOR)
    registro = tmp_path_factory.mktemp("mcp") / "uvicorn.log"
    with open(registro, "w") as salida:
        proceso = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                                    "--port", str(puerto), "--log-level", "warning"],
                                   cwd=BACKEND, env=entorno, stdout=salida, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{puerto}"
    try:
        for _ in range(150):
            assert proceso.poll() is None, registro.read_text()[-2000:]
            try:
                if httpx.get(f"{base}/api/health", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        yield SimpleNamespace(base=base, registro=registro)
    finally:
        proceso.terminate()
        proceso.wait(timeout=10)


def _rpc(base: str, metodo: str, params: dict | None = None, ruta: str = "/mcp", cab: dict | None = None):
    cabeceras = {**ACEPTA, **({"Authorization": f"Bearer {TOKEN}"} if cab is None else cab)}
    return httpx.post(f"{base}{ruta}", headers=cabeceras, timeout=10,
                      json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params or {}})


def _herramienta(base: str, nombre: str, ruta: str = "/mcp", **args) -> tuple[bool, object]:
    r = _rpc(base, "tools/call", {"name": nombre, "arguments": args}, ruta)
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    texto = res["content"][0]["text"]
    return bool(res.get("isError")), (texto if res.get("isError") else json.loads(texto))


def test_contrato_http_recorrido_del_pitch(servidor):
    b = servidor.base
    init = _rpc(b, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "test-contrato", "version": "0"}})
    assert init.status_code == 200 and init.json()["result"]["instructions"]
    herramientas = _rpc(b, "tools/list").json()["result"]["tools"]
    assert {t["name"] for t in herramientas} == HERRAMIENTAS
    assert all(t["annotations"]["readOnlyHint"] for t in herramientas)

    # Sin validar: el agente no debe recomendar.
    error, r = _herramienta(b, "get_investment_constraints", client_id=C)
    assert not error and r["status"] == "pending_validation" and r["usable"] is False

    # El asesor valida (modo asesor de demostración) y el MCP pasa a servir restricciones utilizables.
    v = httpx.post(f"{b}/api/demo/asesor/clientes/{C}/validar", headers={"X-Demo-Advisor-Token": ASESOR}, timeout=10)
    assert v.status_code == 200 and v.json()["status"] == "active"
    error, r = _herramienta(b, "get_investment_constraints", client_id=C)
    assert not error and r["usable"] is True
    assert r["funds_query"] == {"currency": "EUR", "max_risk": 3, "asset_type": ["Monetario", "Renta Fija"]}
    assert r["portfolios_query"] == {"profile": "CONSERVADOR", "risk_max": 1}
    assert r["appropriateness"]["equity_funds"] == "not_appropriate"

    error, e = _herramienta(b, "get_evidence", client_id=C, field="knowledge.equity_funds")
    assert not error and e["source"] == "demonstrated" and e["declared"] == "high" and e["value"] == "none"
    assert "el fondo es del banco" in e["evidence"][0]["quote"]
    error, ctx = _herramienta(b, "get_client_context", client_id=C)
    assert not error and ctx["usable"] is True
    error, p = _herramienta(b, "get_client_profile", client_id=C)
    assert not error and p["status"] == "active" and p["review"]["validated_by"] == "asesor-demo"

    # Nunca por la URL: el token solo vale en la cabecera.
    assert _rpc(b, "tools/list", ruta=f"/mcp/{TOKEN}", cab={}).status_code == 404

    # Otro cliente: invisible para la credencial de demostración.
    otro = httpx.post(f"{b}/api/sessions", json={"channel": "text"}, timeout=10).json()
    error, texto = _herramienta(b, "get_client_profile", client_id=otro["client_id"])
    assert error and "404" in texto
    # Y la credencial del otro cliente no lee a Carmen.
    r = _rpc(b, "tools/call", {"name": "get_investment_constraints", "arguments": {"client_id": C}},
             cab={"Authorization": f"Bearer {otro['access_token']}"})
    assert r.json()["result"]["isError"] is True

    # Sin credencial, incorrecta, o la de demo fuera de /mcp.
    assert _rpc(b, "tools/list", cab={}).status_code == 401
    assert _rpc(b, "tools/list", cab={"Authorization": "Bearer inventada"}).status_code == 401
    assert httpx.get(f"{b}/api/clients/{C}/profile", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 401
    assert httpx.post(f"{b}/api/demo/reset", headers={"X-Admin-Token": TOKEN}).status_code == 401
    assert "CREDENCIAL MCP DE DEMO ACTIVA" in servidor.registro.read_text()
    assert TOKEN not in servidor.registro.read_text()


def test_cliente_mcp_oficial_con_cabecera_y_nunca_por_url(servidor):
    """El SDK cliente de MCP (como haría Claude Code o un puente local) negocia, lista y llama."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def recorrido(url: str, cabeceras: dict[str, str] | None) -> tuple[set[str], dict]:
        async with httpx.AsyncClient(headers=cabeceras or {}, timeout=10) as http, \
                streamable_http_client(url, http_client=http) as (lectura, escritura, _), \
                ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            nombres = {t.name for t in (await sesion.list_tools()).tools}
            r = await sesion.call_tool("get_investment_constraints", {"client_id": C})
            assert not r.isError
            return nombres, json.loads(r.content[0].text)

    nombres, r = asyncio.run(recorrido(f"{servidor.base}/mcp", {"Authorization": f"Bearer {TOKEN}"}))
    assert nombres == HERRAMIENTAS and r["client_id"] == C and "usable" in r
    with pytest.raises(BaseException):  # el SDK no logra ni negociar: la URL con token no existe
        asyncio.run(recorrido(f"{servidor.base}/mcp/{TOKEN}", None))
