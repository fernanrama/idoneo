"""Operador de la demostración: autoriza clientes ficticios nuevos (DATOS SIMULADOS).

Lo usa una persona de confianza desde el ordenador del backend con `scripts/demo_operador.py`:

- Solo con el modo de demostración activo (`DEMO_ADVISOR_MODE=1`); si no, 404 como si no existiera.
- Solo local: loopback, `Host` local y sin cabeceras de proxy (403).
- Solo con `X-Admin-Token` (credencial de servicio, que nunca llega al navegador ni a Next). No acepta el
  Bearer de un cliente, el token del asesor ni los tokens MCP: un cliente no puede autorizarse a sí mismo.
- El operador confirma explícitamente que el cliente es ficticio (`"ficticio": true`).

Autorizar no cambia el perfil MiFID: el asesor sigue teniendo que validarlo con las reglas de siempre.
"""

from __future__ import annotations

import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from . import asesor_demo, demo_autorizaciones as autorizaciones
from .perfil import store

log = logging.getLogger("perfil.demo_operador")

router = APIRouter(prefix="/api/demo/operador", tags=["demo operador"])


def exigir_operador(request: Request, x_admin_token: str | None = Header(default=None)) -> None:
    """Orden: modo apagado (404) → no local (403) → servicio sin configurar (503) → sin credencial (401)."""
    if not asesor_demo.activado():
        raise HTTPException(404, "Not Found")
    if not asesor_demo.es_peticion_local(request):
        raise HTTPException(403, "El operador de la demostración solo funciona en local y sin proxy")
    admin = os.getenv("ADMIN_TOKEN", "").strip()
    if len(admin.encode()) < 32:
        raise HTTPException(503, "Operador no configurado: ADMIN_TOKEN necesita al menos 32 bytes")
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), admin.encode()):
        raise HTTPException(401, "Credencial de operador ausente o no válida", headers={"Cache-Control": "no-store"})


class NuevaAutorizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    ficticio: Literal[True] = Field(description="El operador confirma que el cliente es ficticio (DATOS SIMULADOS)")
    ttl_s: int = Field(default=autorizaciones.TTL_POR_DEFECTO_S, ge=autorizaciones.TTL_MIN_S, le=autorizaciones.TTL_MAX_S)


def _iso(segundos: int) -> str:
    return datetime.fromtimestamp(segundos, tz=timezone.utc).isoformat()


@router.post("/autorizaciones", status_code=201, dependencies=[Depends(exigir_operador)])
def autorizar(body: NuevaAutorizacion) -> dict:
    try:
        perfil = store.perfil(body.client_id)
    except store.NoEncontrado as e:
        raise HTTPException(404, "Cliente no encontrado") from e
    try:
        a, token = autorizaciones.autorizar(body.client_id, body.ttl_s)
    except autorizaciones.LimiteAlcanzado as e:
        raise HTTPException(409, str(e)) from e
    log.warning("Operador: %s autorizado para la demo hasta %s (DATOS SIMULADOS)", body.client_id, _iso(int(a.expira)))
    vista = a.vista()
    return {**vista, "expires_at_iso": _iso(vista["expires_at"]), "mcp_token": token,
            "profile_status": perfil.status.value, "profile_version": perfil.version,
            "aviso": "El token MCP solo se muestra ahora. Solo lee este cliente, desde esta máquina, hasta que caduque, "
                     "se revoque o se reinicie el backend."}


@router.get("/autorizaciones", dependencies=[Depends(exigir_operador)])
def listar() -> dict:
    return {"boot": autorizaciones.ARRANQUE, "autorizaciones": autorizaciones.listar()}


@router.delete("/autorizaciones/{client_id}", dependencies=[Depends(exigir_operador)])
def revocar(client_id: str) -> dict:
    revocada = autorizaciones.revocar(client_id)
    if revocada:
        log.warning("Operador: autorización de %s revocada", client_id)
    return {"client_id": client_id, "revocada": revocada}


@router.delete("/autorizaciones", dependencies=[Depends(exigir_operador)])
def revocar_todo() -> dict:
    n = autorizaciones.revocar_todo()
    log.warning("Operador: %d autorizaciones revocadas", n)
    return {"revocadas": n}
