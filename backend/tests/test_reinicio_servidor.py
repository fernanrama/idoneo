"""Reinicio real de FastAPI (uvicorn en otro proceso) con PERFIL_ALMACEN=bd y lectura por MCP sobre HTTP.

Siempre con SQLite en fichero; también con Postgres si existe TEST_POSTGRES_URL (local de pruebas).
Comprueba que lo validado sobrevive al reinicio, que el arranque no pisa los datos y que el MCP sirve
el último perfil activo.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

BACKEND = Path(__file__).resolve().parents[1]
POSTGRES_TEST = os.getenv("TEST_POSTGRES_URL", "").strip()
MOTORES = ["sqlite"] + (["postgres"] if POSTGRES_TEST else [])
from tests.soporte_acceso import cabeceras_cliente

C = "carmen-68"


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Servidor:
    def __init__(self, url_bd: str, registro: Path):
        self.url_bd, self.registro = url_bd, registro
        self.proceso: subprocess.Popen | None = None
        self.base = ""
        self.headers = cabeceras_cliente(C)

    def arrancar(self) -> None:
        puerto = _puerto_libre()
        entorno = {k: v for k, v in os.environ.items() if k not in ("TEST_POSTGRES_URL",)}
        entorno.update(PERFIL_ALMACEN="bd", DATABASE_URL=self.url_bd, DATA_PERSIST="0",
                       LOAD_DEMO_FIXTURE="1", DEMO_ENDPOINTS="1")
        with open(self.registro, "a") as salida:
            self.proceso = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(puerto), "--log-level", "warning"],
                cwd=BACKEND, env=entorno, stdout=salida, stderr=subprocess.STDOUT)
        self.base = f"http://127.0.0.1:{puerto}"
        for _ in range(100):
            if self.proceso.poll() is not None:
                raise RuntimeError(f"uvicorn terminó al arrancar:\n{self.registro.read_text()[-2000:]}")
            try:
                if httpx.get(f"{self.base}/api/health", timeout=0.5).status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.1)
        raise RuntimeError("uvicorn no respondió a tiempo")

    def parar(self) -> None:
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            self.proceso.wait(timeout=10)

    def api(self, metodo: str, ruta: str, **kw) -> httpx.Response:
        cabeceras = {**self.headers, **kw.pop("headers", {})}
        return httpx.request(metodo, f"{self.base}{ruta}", headers=cabeceras, timeout=10, **kw)

    def mcp(self, herramienta: str, **argumentos) -> dict:
        r = httpx.post(f"{self.base}/mcp", timeout=10,
                       headers={**self.headers, "accept": "application/json, text/event-stream"},
                       json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": herramienta, "arguments": argumentos}})
        assert r.status_code == 200, r.text
        resultado = r.json()["result"]
        assert not resultado.get("isError"), resultado
        return json.loads(resultado["content"][0]["text"])


@pytest.fixture(params=MOTORES)
def servidor(request, tmp_path):
    if request.param == "sqlite":
        url = f"sqlite:///{tmp_path / 'perfil_test.db'}"
    else:
        from tests.conftest import postgres_recien_migrado
        url = postgres_recien_migrado()
    s = Servidor(url, tmp_path / "uvicorn.log")
    yield s
    s.parar()


def test_lo_validado_sobrevive_al_reinicio_y_el_mcp_lo_sirve(servidor):
    servidor.arrancar()
    p = servidor.api("GET", f"/api/clients/{C}/profile").json()
    assert (p["version"], p["status"]) == (1, "pending_validation")
    assert servidor.mcp("get_investment_constraints", client_id=C)["usable"] is False
    r = servidor.api("POST", f"/api/clients/{C}/validate", json={"advisor_id": "asesor-07"})
    assert r.status_code == 200 and r.json()["status"] == "active"
    s = servidor.api("POST", "/api/sessions", json={"client_id": C, "channel": "text"}).json()
    t = servidor.api("POST", f"/api/sessions/{s['session_id']}/turns",
                     json={"speaker": "client", "text": "Hola", "t_start": 0, "t_end": 1})
    assert t.status_code == 202
    # El turno del cliente dispara extractor y verificador en segundo plano; puede añadir una versión
    # (p. ej. una alerta). Se compara el historial completo antes y después del reinicio.
    time.sleep(0.5)
    antes = servidor.api("GET", f"/api/clients/{C}/versions").json()
    assert [v["reason"] for v in antes][:2] == [
        "DATOS SIMULADOS: perfil de ejemplo para desarrollo y demo de respaldo", "validated"]

    servidor.parar()
    servidor.arrancar()  # proceso nuevo, misma base

    despues = servidor.api("GET", f"/api/clients/{C}/versions").json()
    assert despues == antes  # nada perdido y el arranque no recargó el fixture encima
    p = servidor.api("GET", f"/api/clients/{C}/profile").json()
    assert p["version"] == antes[-1]["version"] and p["status"] == "active"
    restricciones = servidor.mcp("get_investment_constraints", client_id=C)
    assert restricciones["usable"] is True and restricciones["funds_query"]["max_risk"] == 3
    perfil_mcp = servidor.mcp("get_client_profile", client_id=C)
    assert perfil_mcp["version"] == antes[-1]["version"] and perfil_mcp["usable"] is True
    evidencia = servidor.mcp("get_evidence", client_id=C, field="knowledge.equity_funds")
    assert evidencia["source"] == "demonstrated" and evidencia["evidence"]
    sesion = servidor.api("GET", f"/api/sessions/{s['session_id']}").json()
    assert sesion["channel"] == "text" and [x["text"] for x in sesion["turns"]] == ["Hola"]

    reset = servidor.api("POST", "/api/demo/reset").json()
    assert reset["version"] == antes[-1]["version"] + 1 and reset["reason"].startswith("demo_reset")
    assert servidor.mcp("get_investment_constraints", client_id=C)["usable"] is False  # nueva época


def test_entrada_invalida_no_tumba_el_servidor(servidor):
    servidor.arrancar()
    r = servidor.api("POST", f"/api/clients/{C}/validate", json={"advisor_id": "a", "changes": [
        {"path": "financial.debts_eur", "value": "muchísimo", "source": "advisor"}]})
    assert r.status_code == 422
    assert servidor.api("GET", "/api/health").status_code == 200
    assert servidor.api("GET", f"/api/clients/{C}/profile").json()["version"] == 1
