"""Credenciales de posesión del prototipo; no verifican la identidad de una persona.

Se emiten solo al crear un cliente nuevo. Nunca se recuperan presentando un identificador.
El secreto debe configurarse fuera del código y conservarse para poder reabrir clientes locales.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Header, HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

from .asesor_demo import es_peticion_local
from .mcp import demo as mcp_demo
from .perfil import store, validacion


@dataclass(frozen=True)
class Permiso:
    client_id: str | None = None
    servicio: bool = False


def _denegar() -> HTTPException:
    return HTTPException(401, "Credencial ausente, inválida o caducada",
                         headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"})


def _configuracion() -> tuple[bytes, int]:
    secreto = os.getenv("CLIENT_ACCESS_SECRET", "").encode()
    if len(secreto) < 32:
        raise HTTPException(503, "Falta configurar CLIENT_ACCESS_SECRET (mínimo 32 bytes)")
    try:
        duracion = int(os.getenv("CLIENT_ACCESS_TTL_S", "28800"))
    except ValueError as e:
        raise HTTPException(503, "CLIENT_ACCESS_TTL_S no es válido") from e
    if not 60 <= duracion <= 86400:
        raise HTTPException(503, "CLIENT_ACCESS_TTL_S debe estar entre 60 y 86400")
    return secreto, duracion


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def preparar_emision() -> Callable[[str], str]:
    """Valida configuración ANTES de crear un cliente; no deja altas huérfanas por falta de secreto."""
    secreto, duracion = _configuracion()

    def emitir(client_id: str) -> str:
        validacion.comprobar_client_id(client_id)
        momento = int(time.time())
        datos = {"cid": client_id, "iat": momento, "exp": momento + duracion,
                 "nonce": secrets.token_urlsafe(24)}
        payload = _b64(json.dumps(datos, sort_keys=True, separators=(",", ":")).encode())
        mensaje = f"v1.{payload}"
        firma = _b64(hmac.new(secreto, mensaje.encode(), hashlib.sha256).digest())
        return f"{mensaje}.{firma}"

    return emitir


def emitir_credencial(client_id: str) -> str:
    """Solo para llamadores internos de confianza después de un alta exclusiva."""
    return preparar_emision()(client_id)


def verificar_credencial(token: str) -> Permiso:
    if not isinstance(token, str) or not 1 <= len(token) <= 2048:
        raise _denegar()
    secreto, _ = _configuracion()
    try:
        version, payload, firma = token.split(".")
        if version != "v1":
            raise ValueError("versión")
        esperada = _b64(hmac.new(secreto, f"v1.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(firma, esperada):
            raise ValueError("firma")
        datos = json.loads(base64.b64decode(payload + "=" * (-len(payload) % 4), altchars=b"-_", validate=True))
        if not isinstance(datos, dict) or set(datos) != {"cid", "iat", "exp", "nonce"}:
            raise ValueError("campos")
        if type(datos["iat"]) is not int or type(datos["exp"]) is not int:
            raise ValueError("tiempo")
        ahora = int(time.time())
        if datos["exp"] <= ahora or datos["iat"] > ahora + 60 or datos["exp"] <= datos["iat"]:
            raise ValueError("caducidad")
        if not isinstance(datos["nonce"], str) or not 16 <= len(datos["nonce"]) <= 128:
            raise ValueError("nonce")
        cid = validacion.comprobar_client_id(datos["cid"])
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as e:
        raise _denegar() from e
    return Permiso(client_id=cid)


def _bearer(authorization: str | None) -> str:
    partes = (authorization or "").split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise _denegar()
    return partes[1]


def principal(authorization: str | None, x_admin_token: str | None = None) -> Permiso:
    """ADMIN_TOKEN es una credencial de servicio privilegiada explícita, no la identidad del asesor."""
    admin = os.getenv("ADMIN_TOKEN", "")
    if x_admin_token is not None:
        if not admin or not hmac.compare_digest(x_admin_token.encode(), admin.encode()):
            raise _denegar()
        return Permiso(servicio=True)
    token = _bearer(authorization)
    if admin and hmac.compare_digest(token.encode(), admin.encode()):
        return Permiso(servicio=True)
    return verificar_credencial(token)


def exigir_cliente(client_id: str, authorization: str | None = Header(default=None),
                   x_admin_token: str | None = Header(default=None)) -> Permiso:
    permiso = principal(authorization, x_admin_token)
    if not permiso.servicio and permiso.client_id != client_id:
        raise HTTPException(404, "Recurso no encontrado")
    return permiso


def exigir_propietario(client_id: str, authorization: str | None = Header(default=None)) -> Permiso:
    """La acción de revisión exige posesión del cliente además del permiso de servicio separado."""
    permiso = verificar_credencial(_bearer(authorization))
    if permiso.client_id != client_id:
        raise HTTPException(404, "Recurso no encontrado")
    return permiso


def exigir_sesion(session_id: str, authorization: str | None = Header(default=None),
                  x_admin_token: str | None = Header(default=None)) -> dict:
    permiso = principal(authorization, x_admin_token)
    try:
        sesion = store.sesion(session_id)
    except store.NoEncontrado as e:
        raise HTTPException(404, "Recurso no encontrado") from e
    if not permiso.servicio and permiso.client_id != sesion["client_id"]:
        raise HTTPException(404, "Recurso no encontrado")
    return sesion


def exigir_servicio(x_admin_token: str | None = Header(default=None)) -> None:
    admin = os.getenv("ADMIN_TOKEN", "")
    if not admin:
        raise HTTPException(503, "Servicio de revisión no configurado")
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), admin.encode()):
        raise _denegar()


def alcance_demo_mcp(authorization: str | None, x_admin_token: str | None) -> frozenset[str] | None:
    """Clientes que abre una credencial MCP de demostración (mcp/demo.py), o None si no es una.
    Solo para /mcp: la API REST nunca las reconoce."""
    if x_admin_token is not None:
        return None
    return mcp_demo.alcance(mcp_demo.bearer(authorization))


class TransporteMCPAutorizado:
    """Protege el transporte; cada herramienta comprueba además el cliente de sus argumentos.
    Las credenciales de demostración solo se aceptan desde esta máquina (loopback, Host local, sin proxy)."""

    def __init__(self, app):
        self.app = app

    @staticmethod
    async def _rechazar(scope, receive, send, status: int, detalle: str, headers=None):
        respuesta = JSONResponse({"detail": detalle}, status_code=status,
                                 headers={**(headers or {}), "Cache-Control": "no-store"})
        return await respuesta(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").rstrip("/") == "/mcp":
            cabeceras = Headers(scope=scope)
            autorizacion, admin = cabeceras.get("authorization"), cabeceras.get("x-admin-token")
            if alcance_demo_mcp(autorizacion, admin) is not None:
                if not es_peticion_local(Request(scope)):
                    return await self._rechazar(scope, receive, send, 403,
                                                "Las credenciales MCP de demostración solo funcionan en local")
            else:
                try:
                    principal(autorizacion, admin)
                except HTTPException as e:
                    return await self._rechazar(scope, receive, send, e.status_code, e.detail, e.headers)
        return await self.app(scope, receive, send)
