"""Vista de la entidad en la web publicada: expediente y validación de cualquier cliente.

La llama SOLO el servidor de Next (`/api/entidad/...`) cuando un administrador ha iniciado sesión con la
clave de administración del front (`ADMIN_LOGIN_CLAVE`, en Vercel). El navegador nunca ve `ADMIN_TOKEN`.

- Autorización: cabecera `X-Admin-Token` con `ADMIN_TOKEN` (credencial de servicio, la misma que ya
  permite leer cualquier perfil). Sin `ADMIN_TOKEN` configurado, 503.
- Validar firma `advisor:<ENTIDAD_ASESOR_ID>` (por defecto `asesor-web`) y admite `expected_version`:
  si el perfil ha cambiado desde lo que vio el administrador, 409 y no se escribe nada.
- A diferencia del modo asesor de demo, sirve para clientes reales de la web (los que crea cada
  entrevista), no solo fixtures. Es una decisión de demo de hackathon: la clave de administración es
  compartida por el equipo, no una identidad individual de asesor.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import acceso
from .asesor_demo import _llamar, _perfil_para_asesor, armar_expediente
from .perfil import store, validacion

log = logging.getLogger("perfil.entidad")

router = APIRouter(prefix="/api/entidad", tags=["entidad"], dependencies=[Depends(acceso.exigir_servicio)])


def _asesor() -> str:
    asesor = os.getenv("ENTIDAD_ASESOR_ID", "asesor-web").strip()
    try:
        validacion.comprobar_autor(f"advisor:{asesor}")
    except validacion.DatoInvalido as e:
        raise HTTPException(503, "ENTIDAD_ASESOR_ID no es válido") from e
    return asesor


@router.get("/clientes/{client_id}")
def expediente(client_id: str) -> dict[str, Any]:
    """Perfil (sin capa personal), restricciones tal como las sirve el MCP, historial, revisión y cambios."""
    return armar_expediente(client_id)


class Validacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int | None = Field(default=None, ge=1)


@router.post("/clientes/{client_id}/validar")
def validar(client_id: str, body: Validacion | None = None) -> dict[str, Any]:
    asesor = _asesor()
    _llamar(store.validar, client_id, asesor, [], body.expected_version if body else None)
    log.warning("Entidad web: %s validado por advisor:%s", client_id, asesor)
    return _perfil_para_asesor(client_id)
