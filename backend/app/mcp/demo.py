"""Credenciales MCP de demostración: solo lectura, solo clientes ficticios, solo en local.

Para conectar Claude Code al MCP durante el pitch sin entregarle `ADMIN_TOKEN`, que da acceso de servicio
a todos los clientes y a rutas REST de escritura. Dos credenciales, ambas por `Authorization: Bearer`
(nunca en la URL) y solo desde esta máquina:

1. `MCP_DEMO_TOKEN` (fija, en el `.env`): lee los fixtures ficticios de `MCP_DEMO_CLIENTS`
   (por defecto `carmen-68,carmen-corta`). Vacía = desactivada. 32+ bytes, distinta de los demás secretos.
2. Token de operador (efímero): lo emite `scripts/demo_operador.py` al autorizar un cliente ficticio nuevo
   (demo_autorizaciones.py). Solo lee ese cliente, caduca, se revoca y no sobrevive a un reinicio.

Solo valen en el transporte `/mcp` y en sus cuatro herramientas de lectura; la API REST no las reconoce.
Una configuración insegura desactiva la credencial fija (falla cerrada) y se avisa en el log al arrancar.
"""

from __future__ import annotations

import hmac
import logging
import os
from dataclasses import dataclass

from .. import demo_autorizaciones
from ..asesor_demo import es_cliente_ficticio

log = logging.getLogger("perfil.mcp.demo")

MIN_BYTES = 32
SECRETOS_DISTINTOS = ("ADMIN_TOKEN", "CLIENT_ACCESS_SECRET", "VOICE_USER_ID_SECRET", "DEMO_ADVISOR_TOKEN")


@dataclass(frozen=True)
class Configuracion:
    token: bytes
    clientes: frozenset[str]


def _clientes() -> list[str]:
    return [c.strip() for c in os.getenv("MCP_DEMO_CLIENTS", "carmen-68,carmen-corta").split(",") if c.strip()]


def _motivo_invalida() -> str | None:
    token = os.getenv("MCP_DEMO_TOKEN", "").strip()
    if not token:
        return "desactivada"
    if len(token.encode()) < MIN_BYTES:
        return f"MCP_DEMO_TOKEN necesita al menos {MIN_BYTES} bytes"
    if not token.replace("-", "").replace("_", "").isalnum():
        return "MCP_DEMO_TOKEN solo admite letras, números, '-' y '_'"
    if token.startswith(demo_autorizaciones.PREFIJO_TOKEN):
        return f"MCP_DEMO_TOKEN no puede empezar por {demo_autorizaciones.PREFIJO_TOKEN!r} (reservado)"
    for nombre in SECRETOS_DISTINTOS:
        otro = os.getenv(nombre, "").strip()
        if otro and hmac.compare_digest(otro.encode(), token.encode()):
            return f"MCP_DEMO_TOKEN debe ser distinto de {nombre}"
    clientes = _clientes()
    if not clientes:
        return "MCP_DEMO_CLIENTS está vacío"
    no_ficticios = [c for c in clientes if not es_cliente_ficticio(c)]
    if no_ficticios:
        return f"MCP_DEMO_CLIENTS solo admite clientes ficticios de backend/fixtures; no lo son: {no_ficticios}"
    return None


def configuracion() -> Configuracion | None:
    """La credencial fija vigente, o None si está desactivada o es insegura."""
    if _motivo_invalida() is not None:
        return None
    return Configuracion(token=os.getenv("MCP_DEMO_TOKEN", "").strip().encode(), clientes=frozenset(_clientes()))


def bearer(authorization: str | None) -> str | None:
    partes = (authorization or "").split()
    return partes[1] if len(partes) == 2 and partes[0].lower() == "bearer" else None


def es_token(valor: str | None) -> bool:
    """¿Es la credencial fija MCP_DEMO_TOKEN?"""
    conf = configuracion()
    return bool(conf and valor and hmac.compare_digest(valor.encode(), conf.token))


def permite(client_id: str) -> bool:
    """Clientes que puede leer la credencial fija."""
    conf = configuracion()
    return bool(conf and client_id in conf.clientes)


def alcance(valor: str | None) -> frozenset[str] | None:
    """Clientes a los que da acceso un Bearer de demostración (fijo o de operador), o None si no lo es."""
    if es_token(valor):
        return configuracion().clientes  # type: ignore[union-attr]
    cid = demo_autorizaciones.cliente_del_token(valor)
    return frozenset({cid}) if cid else None


def avisar_si_activa() -> None:
    motivo = _motivo_invalida()
    if motivo == "desactivada":
        return
    if motivo:
        log.error("MCP_DEMO_TOKEN definida pero desactivada: %s", motivo)
        return
    log.warning("CREDENCIAL MCP DE DEMO ACTIVA: solo lectura, solo en local y solo %s (DATOS SIMULADOS).",
                ", ".join(sorted(configuracion().clientes)))  # type: ignore[union-attr]
