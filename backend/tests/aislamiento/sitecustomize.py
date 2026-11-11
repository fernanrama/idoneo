"""Aislamiento de los tests: sin credenciales reales y sin red fuera de esta máquina.

conftest.py lo carga en el proceso de pytest y añade este directorio a PYTHONPATH, así que Python lo
ejecuta también al arrancar cada subproceso de los tests (servidores uvicorn, multiprocessing...).

- Claves de proveedores de pago: definidas y VACÍAS. `load_dotenv` no sobrescribe variables que ya existen,
  así que el `.env` del repositorio no puede rellenarlas. Un test que necesite una clave pone una ficticia.
- Red: solo sockets UNIX y loopback (127.0.0.0/8, ::1). Cualquier otro destino falla sin abrir conexión.
- uvloop desactivado en este proceso: su bucle conecta sin pasar por `socket`, y el estándar sí pasa.
"""

from __future__ import annotations

import ipaddress
import os
import socket
import sys

CLAVES_DE_PAGO = ("ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_AGENT_ID", "ELEVENLABS_WEBHOOK_SECRET")
MENSAJE = "aislamiento de tests: conexión externa bloqueada"


def _permitido(sock: socket.socket, direccion) -> bool:
    if sock.family == getattr(socket, "AF_UNIX", object()):
        return True
    host = direccion[0] if isinstance(direccion, tuple) else direccion
    try:
        ip = ipaddress.ip_address(str(host).split("%")[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_loopback


def _activar_red() -> None:
    if getattr(socket.socket.connect, "_aislamiento", False):
        return
    original, original_ex = socket.socket.connect, socket.socket.connect_ex

    def connect(self, direccion):
        if not _permitido(self, direccion):
            raise ConnectionRefusedError(f"{MENSAJE} ({direccion!r})")
        return original(self, direccion)

    def connect_ex(self, direccion):
        if not _permitido(self, direccion):
            return 111  # ECONNREFUSED
        return original_ex(self, direccion)

    connect._aislamiento = True  # type: ignore[attr-defined]
    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex


class _SinUvloop:
    def find_spec(self, nombre, path=None, target=None):
        if nombre == "uvloop" or nombre.startswith("uvloop."):
            raise ImportError("aislamiento de tests: uvloop desactivado")
        return None


def activar() -> None:
    for clave in CLAVES_DE_PAGO:
        os.environ[clave] = ""
    _activar_red()
    if not any(isinstance(f, _SinUvloop) for f in sys.meta_path):
        sys.meta_path.insert(0, _SinUvloop())


activar()
