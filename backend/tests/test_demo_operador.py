"""Cliente ficticio nuevo → entrevista → perfil pendiente → autorización del operador → validación del asesor
→ MCP → restricciones. Más caducidad, revocación y no reutilización tras reiniciar.

Sin servicios externos: el entrevistador y el extractor de Claude se sustituyen por dobles deterministas
(su lógica tiene tests propios); todo lo demás (API, store, validación, MCP) es el código real.
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

from app import demo_autorizaciones as aut
from app.agentes import chat, claude, extractor
from app.main import app
from app.mcp.servidor import mcp
from app.perfil import store
from app.perfil.modelos import Evidencia, Fuente, Parche

C = "carmen-68"
ASESOR = "asesor-demo-sintetico-operador-0123456789abc"
MCP_FIJO = "mcp-fijo-sintetico-del-test-operador-0123456789"
LOCAL = ("127.0.0.1", 51000)
BACKEND = Path(__file__).resolve().parents[1]

# Entrevista ficticia de «Lucía»: cada frase del cliente y lo que el extractor sacaría de ella (con su cita).
ENTREVISTA = [
    ("Sí, entiendo que hablo con una IA y para qué sirve.",
     [("disclosures.ai_notice_ack", True, "entiendo que hablo con una IA"), ("disclosures.purpose_ack", True, "para qué sirve")]),
    ("Ingreso unos 2.400 € netos al mes y mis gastos fijos son unos 1.300 €.",
     [("financial.net_monthly_income_eur", 2400.0, "Ingreso unos 2.400 € netos al mes"),
      ("financial.fixed_monthly_costs_eur", 1300.0, "mis gastos fijos son unos 1.300 €")]),
    ("Tengo 15.000 € ahorrados y no tengo deudas.",
     [("financial.liquid_savings_eur", 15000.0, "Tengo 15.000 € ahorrados"), ("financial.debts_eur", 0.0, "no tengo deudas")]),
    ("Quiero la entrada de un piso dentro de 5 años.",
     [("objectives.o1.goal", "entrada de un piso", "la entrada de un piso"), ("objectives.o1.horizon_years", 5.0, "dentro de 5 años")]),
    ("Conozco algo los fondos de renta fija, poco la renta variable; si bajara un 20 % esperaría; la sostenibilidad me da igual.",
     [("knowledge.fixed_income_funds", "medium", "Conozco algo los fondos de renta fija"),
      ("knowledge.equity_funds", "basic", "poco la renta variable"),
      ("risk_tolerance.scenario_score", 3, "si bajara un 20 % esperaría"),
      ("sustainability.preference", "none", "la sostenibilidad me da igual")]),
]


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("DEMO_ADVISOR_MODE", "1")
    monkeypatch.setenv("DEMO_ADVISOR_TOKEN", ASESOR)
    monkeypatch.setenv("MCP_DEMO_TOKEN", MCP_FIJO)
    monkeypatch.setenv("ADMIN_TOKEN", "servicio-sintetico-del-operador-0123456789abcdef")
    for v in ("DEMO_ADVISOR_CLIENTS", "MCP_DEMO_CLIENTS"):
        monkeypatch.delenv(v, raising=False)
    aut.revocar_todo()
    store.reiniciar()
    store.cargar_fixture(C)
    yield SimpleNamespace(admin={"X-Admin-Token": os.environ["ADMIN_TOKEN"]}, asesor={"X-Demo-Advisor-Token": ASESOR})
    aut.revocar_todo()


def local() -> TestClient:
    return TestClient(app, base_url="http://localhost", client=LOCAL)


def operador(c: TestClient, cab: dict, client_id: str, **extra) -> httpx.Response:
    return c.post("/api/demo/operador/autorizaciones", headers=cab, json={"client_id": client_id, "ficticio": True, **extra})


def mcp_con(monkeypatch, token: str, nombre: str, **args):
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    monkeypatch.setattr(mcp, "get_context", lambda: SimpleNamespace(request_context=SimpleNamespace(request=request)))
    res = asyncio.run(mcp.call_tool(nombre, args))
    bloques = res[0] if isinstance(res, tuple) else res
    return json.loads(bloques[0].text)


def entrevistar(monkeypatch, c: TestClient) -> dict:
    """Entrevista de texto por la API real; Claude sustituido por dobles sin red."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(claude, "_cliente_async", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sin red")))

    async def responder(turnos, perfil):
        return chat.Respuesta(texto="¿Seguimos?", terminada=False)

    async def extraer(turnos, perfil, session_id):
        ultimo = [t for t in turnos if t.speaker == "client"][-1]
        datos = dict(ENTREVISTA)[ultimo.text]
        # Conocimientos como si hubiera respondido bien a la comprobación: lo declarado no da conveniencia.
        return [Parche(path=r, value=v, source=Fuente.demonstrated if r.startswith("knowledge.") else Fuente.declared,
                       confidence=0.9, confidence_basis="doble:test",
                       evidence=[Evidencia(session_id=session_id, turn_id=ultimo.turn_id, t=(ultimo.t_start, ultimo.t_end), quote=q)])
                for r, v, q in datos]

    monkeypatch.setattr(chat, "responder", responder)
    monkeypatch.setattr(extractor, "extraer", extraer)
    alta = c.post("/api/sessions", json={"channel": "text"}).json()
    h = {"Authorization": f"Bearer {alta['access_token']}"}
    assert c.post(f"/api/sessions/{alta['session_id']}/chat", json={"text": None}, headers=h).status_code == 200
    for texto, _ in ENTREVISTA:
        assert c.post(f"/api/sessions/{alta['session_id']}/chat", json={"text": texto}, headers=h).status_code == 200
    return {**alta, "h": h}


# ---------- registro: caducidad, revocación, huellas ----------

def test_registro_caduca_se_revoca_y_no_guarda_el_token(monkeypatch):
    aut.revocar_todo()
    reloj = [1_000_000.0]
    monkeypatch.setattr(aut, "_ahora", lambda: reloj[0])
    a, token = aut.autorizar("cliente-x", ttl_s=60)
    assert token.startswith(aut.PREFIJO_TOKEN) and token not in repr(a) and aut.cliente_del_token(token) == "cliente-x"
    reloj[0] += 59
    assert aut.activa("cliente-x") is not None
    reloj[0] += 2  # caducado
    assert aut.activa("cliente-x") is None and aut.cliente_del_token(token) is None and aut.listar() == []
    _, t1 = aut.autorizar("cliente-x")
    _, t2 = aut.autorizar("cliente-x")  # renovar invalida el token anterior
    assert aut.cliente_del_token(t1) is None and aut.cliente_del_token(t2) == "cliente-x"
    assert aut.revocar("cliente-x") and aut.cliente_del_token(t2) is None and not aut.revocar("cliente-x")
    for i in range(aut.MAX_ACTIVAS):
        aut.autorizar(f"cliente-{i}")
    with pytest.raises(aut.LimiteAlcanzado):
        aut.autorizar("cliente-otro")
    assert aut.revocar_todo() == aut.MAX_ACTIVAS
    for ttl in (0, 59, aut.TTL_MAX_S + 1):
        with pytest.raises(ValueError):
            aut.autorizar("cliente-x", ttl_s=ttl)


# ---------- quién puede autorizar ----------

def test_operador_apagado_por_defecto(demo, monkeypatch):
    monkeypatch.delenv("DEMO_ADVISOR_MODE")
    assert operador(local(), demo.admin, C).status_code == 404


@pytest.mark.parametrize("cliente,extra", [(("192.168.1.20", 51000), {}), (LOCAL, {"X-Forwarded-For": "203.0.113.9"}),
                                           (LOCAL, {"Host": "idoneo.example.com"}), (("10.0.0.7", 51000), {"Host": "localhost"})])
def test_operador_solo_en_local(demo, cliente, extra):
    c = TestClient(app, base_url="http://localhost", client=cliente)
    assert c.post("/api/demo/operador/autorizaciones", headers={**demo.admin, **extra},
                  json={"client_id": C, "ficticio": True}).status_code == 403


def test_nadie_salvo_el_operador_puede_autorizar(demo, monkeypatch):
    c = local()
    alta = c.post("/api/sessions", json={"channel": "text"}).json()
    _, efimero = aut.autorizar(C)
    intentos = [{}, {"Authorization": f"Bearer {alta['access_token']}"},           # el propio cliente
                {"X-Admin-Token": alta["access_token"]}, {"X-Admin-Token": alta["client_id"]},
                {"X-Admin-Token": alta["session_id"]}, {"X-Admin-Token": ASESOR},  # asesor
                {"X-Admin-Token": MCP_FIJO}, {"X-Admin-Token": efimero},          # tokens MCP
                {"Authorization": f"Bearer {os.environ['ADMIN_TOKEN']}"}]         # ADMIN fuera de su cabecera
    for cab in intentos:
        assert operador(c, cab, alta["client_id"]).status_code == 401, cab
    assert aut.activa(alta["client_id"]) is None
    monkeypatch.setenv("ADMIN_TOKEN", "corto")
    assert operador(c, {"X-Admin-Token": "corto"}, alta["client_id"]).status_code == 503


def test_peticion_de_autorizacion_explicita(demo):
    c = local()
    url = "/api/demo/operador/autorizaciones"
    assert c.post(url, headers=demo.admin, json={"client_id": C}).status_code == 422                     # sin confirmar
    assert c.post(url, headers=demo.admin, json={"client_id": C, "ficticio": False}).status_code == 422
    assert c.post(url, headers=demo.admin, json={"client_id": C, "ficticio": True, "ttl_s": 10}).status_code == 422
    assert c.post(url, headers=demo.admin, json={"client_id": C, "ficticio": True, "todos": True}).status_code == 422
    assert c.post(url, headers=demo.admin, json={"client_id": "../x", "ficticio": True}).status_code == 422
    assert operador(c, demo.admin, "cliente-que-no-existe").status_code == 404


# ---------- recorrido completo ----------

def test_recorrido_cliente_nuevo_hasta_mcp(demo, monkeypatch):
    c = local()
    nuevo = entrevistar(monkeypatch, c)
    cid = nuevo["client_id"]
    p = c.get(f"/api/clients/{cid}/profile", headers=nuevo["h"]).json()
    assert p["status"] == "pending_validation" and p["assessments"]["suitability"]["complete"]
    cita = p["mifid"]["financial.liquid_savings_eur"]["evidence"][0]
    assert cita["session_id"] == nuevo["session_id"] and cita["quote"] in ENTREVISTA[2][0]
    versiones = len(store.versiones(cid))

    # Sin autorización del operador: ni el asesor ni el MCP de demo lo ven.
    assert cid not in c.get("/api/demo/asesor/estado", headers=demo.asesor).json()["clients"]
    assert c.post(f"/api/demo/asesor/clientes/{cid}/validar", headers=demo.asesor).status_code == 404
    with pytest.raises(Exception, match="404"):
        mcp_con(monkeypatch, MCP_FIJO, "get_investment_constraints", client_id=cid)

    # El operador lo autoriza: no cambia el perfil MiFID.
    r = operador(c, demo.admin, cid)
    assert r.status_code == 201 and r.headers["Cache-Control"] == "no-store"
    token = r.json()["mcp_token"]
    assert r.json()["profile_status"] == "pending_validation" and len(store.versiones(cid)) == versiones
    listado = c.get("/api/demo/operador/autorizaciones", headers=demo.admin).json()
    assert [a["client_id"] for a in listado["autorizaciones"]] == [cid] and token not in json.dumps(listado)
    assert mcp_con(monkeypatch, token, "get_investment_constraints", client_id=cid)["usable"] is False

    # El asesor valida con la validación de siempre.
    assert cid in c.get("/api/demo/asesor/estado", headers=demo.asesor).json()["clients"]
    v = c.post(f"/api/demo/asesor/clientes/{cid}/validar", headers=demo.asesor)
    assert v.status_code == 200 and v.json()["status"] == "active" and v.json()["review"]["validated_by"] == "asesor-demo"
    assert c.post(f"/api/demo/asesor/clientes/{cid}/reiniciar", headers=demo.asesor).status_code == 404  # sin fixture

    # MCP con el token del operador: solo este cliente, solo lectura, restricciones calculadas.
    r = mcp_con(monkeypatch, token, "get_investment_constraints", client_id=cid)
    assert r["usable"] is True and r["portfolios_query"]["profile"] == "DINAMICO" and r["funds_query"]["max_risk"] == 5
    assert r["appropriateness"]["equity_funds"] == "not_appropriate" and r["funds_query"]["asset_type"] == ["Renta Fija"]
    e = mcp_con(monkeypatch, token, "get_evidence", client_id=cid, field="financial.liquid_savings_eur")
    assert e["value"] == 15000.0 and e["evidence"][0]["quote"] == "Tengo 15.000 € ahorrados"
    for otro in (C, store.crear_nuevo("cliente-0a1b2c3d4e5f").client_id):
        with pytest.raises(Exception, match="404"):
            mcp_con(monkeypatch, token, "get_client_profile", client_id=otro)

    # Fin de la demo: revocar. El perfil sigue validado, pero el token y el permiso del asesor desaparecen.
    assert c.delete(f"/api/demo/operador/autorizaciones/{cid}", headers=demo.admin).json()["revocada"] is True
    with pytest.raises(Exception, match="401"):
        mcp_con(monkeypatch, token, "get_investment_constraints", client_id=cid)
    assert c.get(f"/api/demo/asesor/clientes/{cid}", headers=demo.asesor).status_code == 404
    assert store.perfil(cid).status.value == "active"


def test_autorizar_no_omite_la_validacion_mifid(demo):
    c = local()
    alta = c.post("/api/sessions", json={"channel": "text"}).json()  # sin entrevista: perfil incompleto
    assert operador(c, demo.admin, alta["client_id"]).status_code == 201
    r = c.post(f"/api/demo/asesor/clientes/{alta['client_id']}/validar", headers=demo.asesor)
    assert r.status_code == 409 and "Faltan datos obligatorios" in r.json()["detail"]
    assert store.perfil(alta["client_id"]).status.value == "draft" and len(store.versiones(alta["client_id"])) == 1


def test_tokens_del_operador_tampoco_abren_rest(demo):
    c = local()
    alta = c.post("/api/sessions", json={"channel": "text"}).json()
    token = operador(c, demo.admin, alta["client_id"]).json()["mcp_token"]
    b = {"Authorization": f"Bearer {token}"}
    assert c.get(f"/api/clients/{alta['client_id']}/profile", headers=b).status_code == 401
    assert c.post(f"/api/demo/asesor/clientes/{alta['client_id']}/validar", headers={"X-Demo-Advisor-Token": token}).status_code == 401
    assert c.post("/api/demo/reset", headers={"X-Admin-Token": token}).status_code == 401
    r = TestClient(app, base_url="http://localhost", client=("192.168.1.20", 1)).post(
        "/mcp", headers={"Accept": "application/json, text/event-stream", **b}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code == 403


def test_el_script_no_escribe_el_token_en_la_terminal(monkeypatch, capsys):
    """Con stdout en una terminal no autoriza nada (ni siquiera contacta con el backend) salvo --mostrar-token."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("demo_operador_cli", BACKEND / "scripts" / "demo_operador.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    llamadas = []
    monkeypatch.setattr(cli, "_pedir", lambda *a, **k: llamadas.append(a) or {
        "client_id": "cliente-x", "profile_version": 1, "profile_status": "draft", "expires_at_iso": "-", "boot": "b",
        "mcp_token": "idoneo-demo-SINTETICO"})
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    with pytest.raises(SystemExit) as e:
        cli.main(["autorizar", "cliente-x", "--confirmo-ficticio"])
    assert "export IDONEO_MCP_TOKEN" in str(e.value) and llamadas == []
    cli.main(["autorizar", "cliente-x", "--confirmo-ficticio", "--mostrar-token"])
    assert capsys.readouterr().out.strip() == "idoneo-demo-SINTETICO" and len(llamadas) == 1


# ---------- reinicio: nada se reutiliza ----------

def _puerto() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Backend:
    def __init__(self, tmp: Path):
        self.entorno = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC", "ELEVENLABS", "TEST_POSTGRES", "MCP_DEMO"))}
        self.entorno.update(ANTHROPIC_API_KEY="", ELEVENLABS_API_KEY="", ELEVENLABS_AGENT_ID="", PERFIL_ALMACEN="bd",
                            DATABASE_URL=f"sqlite:///{tmp / 'demo.db'}", DATA_PERSIST="0", LOAD_DEMO_FIXTURE="1",
                            CLIENT_ACCESS_SECRET="material-sintetico-reinicio-0123456789abcdef",
                            ADMIN_TOKEN="servicio-sintetico-reinicio-0123456789abcdef",
                            DEMO_ADVISOR_MODE="1", DEMO_ADVISOR_TOKEN=ASESOR)
        self.registro, self.proceso, self.base = tmp / "uvicorn.log", None, ""

    def arrancar(self):
        puerto = _puerto()
        assert puerto not in (3000, 8000)
        with open(self.registro, "a") as salida:
            self.proceso = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                                             "--port", str(puerto), "--log-level", "warning"],
                                            cwd=BACKEND, env=self.entorno, stdout=salida, stderr=subprocess.STDOUT)
        self.base = f"http://127.0.0.1:{puerto}"
        for _ in range(150):
            assert self.proceso.poll() is None, self.registro.read_text()[-2000:]
            try:
                if httpx.get(f"{self.base}/api/health", timeout=0.5).status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.1)
        raise RuntimeError("uvicorn no arrancó")

    def parar(self):
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            self.proceso.wait(timeout=10)

    def operador(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "scripts/demo_operador.py", *args], cwd=BACKEND, capture_output=True, text=True,
                              env={**self.entorno, "IDONEO_API_URL": self.base}, timeout=30)

    def mcp(self, token: str, metodo: str, params: dict | None = None) -> httpx.Response:
        return httpx.post(f"{self.base}/mcp", timeout=10, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params or {}},
                          headers={"Accept": "application/json, text/event-stream", "Authorization": f"Bearer {token}"})


def test_tras_reiniciar_no_se_reutiliza_nada(tmp_path):
    b = Backend(tmp_path)
    try:
        b.arrancar()
        alta = httpx.post(f"{b.base}/api/sessions", json={"channel": "text"}).json()
        cid = alta["client_id"]
        # El script del operador: stdout lleva solo el token; stderr, el resumen.
        hecho = b.operador("autorizar", cid, "--confirmo-ficticio", "--ttl", "600")
        assert hecho.returncode == 0, hecho.stderr
        token = hecho.stdout.strip()
        assert token.startswith(aut.PREFIJO_TOKEN) and "\n" not in token and cid in hecho.stderr and token not in hecho.stderr
        assert b.operador("autorizar", cid).returncode != 0  # sin --confirmo-ficticio no hace nada
        assert cid in b.operador("listar").stdout
        r = b.mcp(token, "tools/call", {"name": "get_investment_constraints", "arguments": {"client_id": cid}})
        assert r.status_code == 200 and json.loads(r.json()["result"]["content"][0]["text"])["usable"] is False
        b.parar()

        b.arrancar()  # misma base SQLite: el cliente sigue existiendo, las autorizaciones no
        assert httpx.get(f"{b.base}/api/clients/{cid}/profile", headers={"Authorization": f"Bearer {alta['access_token']}"}).status_code == 200
        assert b.mcp(token, "tools/list").status_code == 401
        assert httpx.post(f"{b.base}/api/demo/asesor/clientes/{cid}/validar", headers={"X-Demo-Advisor-Token": ASESOR}).status_code == 404
        assert "(ninguna)" in b.operador("listar").stdout
        nuevo = b.operador("autorizar", cid, "--confirmo-ficticio").stdout.strip()
        assert nuevo != token and b.mcp(nuevo, "tools/list").status_code == 200
        assert "revocada" in b.operador("revocar", cid).stdout and b.mcp(nuevo, "tools/list").status_code == 401
        assert "Revocadas: 0" in b.operador("revocar-todo").stdout
        assert token not in b.registro.read_text() and nuevo not in b.registro.read_text()
    finally:
        b.parar()
