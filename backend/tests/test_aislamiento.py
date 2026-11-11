"""El aislamiento de los tests funciona: sin claves reales, sin red externa, también en subprocesos."""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys

import pytest
from dotenv import load_dotenv

from tests.conftest import aislamiento

EXTERNA = ("192.0.2.1", 443)  # TEST-NET-1 (RFC 5737): nunca es un servicio real


def test_cada_test_empieza_sin_claves_de_pago():
    for clave in aislamiento.CLAVES_DE_PAGO:
        assert os.environ.get(clave) == ""
    assert "VERIFICADOR_CLAUDE" not in os.environ


def test_un_env_con_claves_no_las_rellena(tmp_path):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=clave-sintetica-que-no-debe-cargarse\n"
                   "ELEVENLABS_API_KEY=otra-clave-sintetica\n", "utf-8")
    load_dotenv(env)  # como hace app/main.py con el .env de la raíz (override=False)
    assert os.environ["ANTHROPIC_API_KEY"] == "" and os.environ["ELEVENLABS_API_KEY"] == ""
    from app.agentes import claude
    assert not claude.disponible()


def test_conexion_externa_bloqueada():
    with socket.socket() as s, pytest.raises(ConnectionRefusedError, match="aislamiento"):
        s.connect(EXTERNA)
    try:
        s6 = socket.socket(socket.AF_INET6)
    except OSError:  # máquina sin IPv6 (algunos contenedores): no hay por dónde salir por IPv6
        return
    with s6, pytest.raises(ConnectionRefusedError, match="aislamiento"):
        s6.connect(("2001:db8::1", 443, 0, 0))


def test_conexion_externa_asincrona_bloqueada():
    async def abrir():
        await asyncio.open_connection(*EXTERNA)

    with pytest.raises(ConnectionRefusedError):
        asyncio.run(abrir())


def test_loopback_permitido():
    with socket.socket() as servidor:
        servidor.bind(("127.0.0.1", 0))
        servidor.listen(1)
        with socket.socket() as cliente:
            cliente.connect(servidor.getsockname())


def test_el_sdk_de_anthropic_no_sale_de_la_maquina():
    anthropic = pytest.importorskip("anthropic")
    cliente = anthropic.Anthropic(api_key="clave-sintetica", base_url="https://192.0.2.1", max_retries=0, timeout=5)
    with pytest.raises(anthropic.APIConnectionError):
        cliente.messages.create(model="modelo-sintetico", max_tokens=1, messages=[{"role": "user", "content": "x"}])


def test_los_subprocesos_heredan_el_aislamiento():
    codigo = (
        "import os, socket\n"
        "s = socket.socket()\n"
        "try:\n    s.connect(('192.0.2.1', 443)); print('CONECTADO')\n"
        "except ConnectionRefusedError:\n    print('bloqueado')\n"
        "print(repr(os.environ.get('ANTHROPIC_API_KEY')))\n"
        "try:\n    import uvloop; print('uvloop')\n"
        "except ImportError:\n    print('sin uvloop')\n"
    )
    entorno = {**os.environ, "ANTHROPIC_API_KEY": "clave-sintetica-del-padre"}
    salida = subprocess.run([sys.executable, "-c", codigo], env=entorno, capture_output=True, text=True,
                            timeout=60).stdout.split()
    assert salida == ["bloqueado", "''", "sin", "uvloop"]
