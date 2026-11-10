"""Autorizaciones de demostración para clientes ficticios nuevos (DATOS SIMULADOS).

Un operador de confianza (scripts/demo_operador.py, en el ordenador del backend) autoriza un cliente concreto
que acaba de hacer la entrevista. La autorización:

- vale solo para ese `client_id`: permite que el asesor de demo lo valide y emite un token MCP de lectura
  que solo sirve para ese cliente;
- caduca (por defecto 2 h, máximo 8 h) y se puede revocar en cualquier momento;
- vive solo en la memoria de este proceso: un reinicio del backend las anula todas, también los tokens;
- guarda únicamente la huella SHA-256 del token, nunca el token.

No toca el perfil MiFID: no cambia estados, no valida nada y no omite ninguna regla.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass

TTL_POR_DEFECTO_S = 2 * 3600
TTL_MIN_S, TTL_MAX_S = 60, 8 * 3600
MAX_ACTIVAS = 10
PREFIJO_TOKEN = "idoneo-demo-"

_ahora = time.time  # sustituible en tests
_candado = threading.Lock()
# Identifica este proceso: lo ve el operador para saber que un reinicio anuló lo anterior.
ARRANQUE = secrets.token_hex(4)


@dataclass(frozen=True)
class Autorizacion:
    client_id: str
    creada: float
    expira: float
    huella_token: str  # sha256 hex del token MCP

    def vista(self) -> dict:
        return {"client_id": self.client_id, "created_at": int(self.creada), "expires_at": int(self.expira),
                "expires_in_s": max(0, int(self.expira - _ahora())), "boot": ARRANQUE}


_por_cliente: dict[str, Autorizacion] = {}


class LimiteAlcanzado(RuntimeError):
    pass


def _huella(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _purgar() -> None:
    ahora = _ahora()
    for cid in [c for c, a in _por_cliente.items() if a.expira <= ahora]:
        del _por_cliente[cid]


def autorizar(client_id: str, ttl_s: int = TTL_POR_DEFECTO_S) -> tuple[Autorizacion, str]:
    """Crea (o renueva) la autorización del cliente y devuelve un token MCP nuevo. El anterior deja de valer."""
    if not TTL_MIN_S <= ttl_s <= TTL_MAX_S:
        raise ValueError(f"ttl_s debe estar entre {TTL_MIN_S} y {TTL_MAX_S}")
    token = PREFIJO_TOKEN + secrets.token_urlsafe(32)
    with _candado:
        _purgar()
        if client_id not in _por_cliente and len(_por_cliente) >= MAX_ACTIVAS:
            raise LimiteAlcanzado(f"Como mucho {MAX_ACTIVAS} clientes autorizados a la vez")
        ahora = _ahora()
        a = Autorizacion(client_id=client_id, creada=ahora, expira=ahora + ttl_s, huella_token=_huella(token))
        _por_cliente[client_id] = a
    return a, token


def activa(client_id: str) -> Autorizacion | None:
    with _candado:
        _purgar()
        return _por_cliente.get(client_id)


def cliente_del_token(token: str | None) -> str | None:
    """El cliente al que da acceso un token MCP vigente, o None."""
    if not token or not token.startswith(PREFIJO_TOKEN) or len(token) > 256:
        return None
    huella = _huella(token)
    with _candado:
        _purgar()
        for a in _por_cliente.values():
            if hmac.compare_digest(a.huella_token, huella):
                return a.client_id
    return None


def revocar(client_id: str) -> bool:
    with _candado:
        return _por_cliente.pop(client_id, None) is not None


def revocar_todo() -> int:
    with _candado:
        n = len(_por_cliente)
        _por_cliente.clear()
        return n


def listar() -> list[dict]:
    with _candado:
        _purgar()
        return [a.vista() for a in sorted(_por_cliente.values(), key=lambda a: a.creada)]
