"""El MCP en un despliegue: el agente de la entidad entra por el nombre público del servicio.

Reproduce lo que pasaba en Render: sin `MCP_ALLOWED_HOSTS`, la protección contra DNS rebinding del SDK
solo admitía localhost y toda llamada con credencial válida a `https://<servicio>.onrender.com/mcp` acababa
en `421 Invalid Host header`. Render publica su nombre en `RENDER_EXTERNAL_HOSTNAME`: ese host se admite solo.

Sin servicios externos: uvicorn local en un puerto efímero, datos simulados y claves de proveedores vacías.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.mcp.servidor import _seguridad

BACKEND = Path(__file__).resolve().parents[1]
PUBLICO = "idoneo-backend.onrender.com"
SERVICIO = "servicio-del-test-mcp-despliegue"
ACEPTA = {"Accept": "application/json, text/event-stream"}


def test_el_host_publico_de_render_se_admite_solo(monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", PUBLICO)
    s = _seguridad()
    assert s.enable_dns_rebinding_protection is True
    assert PUBLICO in s.allowed_hosts and "localhost:*" in s.allowed_hosts


def test_sin_despliegue_solo_localhost(monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_HOSTNAME", raising=False)
    assert _seguridad().allowed_hosts == ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*"]


def test_los_hosts_declarados_se_suman_al_de_render(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "abc.trycloudflare.com")
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", PUBLICO)
    s = _seguridad()
    assert {"abc.trycloudflare.com", PUBLICO} <= set(s.allowed_hosts)
    assert "https://abc.trycloudflare.com" in s.allowed_origins


def _puerto() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def como_en_render(tmp_path_factory):
    """El backend arrancado como en Render: sin MCP_ALLOWED_HOSTS y con el nombre público que pone la plataforma."""
    puerto = _puerto()
    assert puerto not in (3000, 8000)
    entorno = {k: v for k, v in os.environ.items()
               if not k.startswith(("ANTHROPIC", "ELEVENLABS", "TEST_POSTGRES", "MCP_"))}
    entorno.update(ANTHROPIC_API_KEY="", ELEVENLABS_API_KEY="", ELEVENLABS_AGENT_ID="", DATABASE_URL="",
                   PERFIL_ALMACEN="memoria", DATA_PERSIST="0", LOAD_DEMO_FIXTURE="1",
                   CLIENT_ACCESS_SECRET="material-sintetico-del-test-mcp-despliegue-0123", ADMIN_TOKEN=SERVICIO,
                   RENDER_EXTERNAL_HOSTNAME=PUBLICO)
    registro = tmp_path_factory.mktemp("mcp-despliegue") / "uvicorn.log"
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
        yield base
    finally:
        proceso.terminate()
        proceso.wait(timeout=10)


def _restricciones(base: str, host: str) -> httpx.Response:
    return httpx.post(f"{base}/mcp", timeout=10, headers={**ACEPTA, "Host": host, "X-Admin-Token": SERVICIO},
                      json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "get_investment_constraints", "arguments": {"client_id": "carmen-68"}}})


def test_el_agente_de_la_entidad_entra_por_el_nombre_publico(como_en_render):
    r = _restricciones(como_en_render, PUBLICO)
    assert r.status_code == 200, r.text  # antes: 421 Invalid Host header
    resultado = r.json()["result"]
    assert not resultado.get("isError"), resultado
    assert '"usable"' in resultado["content"][0]["text"]


def test_otro_host_sigue_rechazado(como_en_render):
    assert _restricciones(como_en_render, "atacante.example.com").status_code == 421
