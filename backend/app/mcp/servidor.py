"""Servidor MCP del perfil (rol D).

Expone 4 herramientas de solo lectura sobre el mismo perfil que la API REST
(especificación: docs/diseno/03-contrato-perfil.md, sección "Herramientas MCP y API REST"):

- get_client_profile(client_id, version?)
- get_investment_constraints(client_id)
- get_evidence(client_id, field)
- get_client_context(client_id)

Reglas del contrato:
- Leen el perfil `active` más reciente (`store.perfil_para_consumidor`). Si no hay ninguno activo,
  devuelven el último con `usable: false` en vez de un error.
- Nosotros no filtramos productos: `get_investment_constraints` da los parámetros para que el agente de
  la entidad los pase al MCP de MyInvestor (como conector en Claude, nunca desde este backend).
- Los números salen de `calculos.py`, nunca del modelo.

Se monta en la API (`app.main`) en `/mcp` con transporte HTTP "streamable", sin estado.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from .. import acceso
from ..agentes import contexto
from ..perfil import store
from ..perfil.modelos import EstadoPerfil

INSTRUCCIONES = """\
Este servidor da el perfil inversor verificado de un cliente (idoneidad y conveniencia MiFID II),
construido en una entrevista por voz. Cada dato lleva su fuente (declarado, demostrado, calculado o
corregido por el asesor), su confianza y la cita de la entrevista que lo justifica.

Cómo usarlo:
1. Antes de proponer cualquier producto, llama a get_investment_constraints. Si `usable` es false, el
   perfil aún no lo ha validado un asesor: no recomiendes nada y dilo. Si `pending_review` no es null,
   esos datos han cambiado y están pendientes de validar: no apoyes ninguna recomendación en ellos y
   dile al cliente que están en revisión.
2. Usa `funds_query` y `portfolios_query` como criterios de búsqueda en el catálogo de MyInvestor.
   Si un criterio trae una lista (p. ej. `asset_type: ["Monetario", "Renta Fija"]`) y el catálogo solo
   acepta un valor, haz una búsqueda por cada valor y une los resultados; no quites ninguno.
   Aplica después `post_filters` a cada ficha. En `min_initial` la ficha da texto ("1000.00 EUR" o
   "0.001 participaciones"): compara el importe en euros; si viene en participaciones, no hay mínimo.
   No busques ni propongas lo que aparece en `blocked_searches` ("funds" fondos, "portfolios" carteras,
   "etfs", "stocks" acciones); `rationale` dice por qué. Un `asset_type` vacío significa ningún tipo de
   fondo, nunca «cualquiera». Respeta `appropriateness`: no ofrezcas familias `not_appropriate`.
   Estas restricciones son límites, no una selección: qué productos proponer y en qué orden lo decide
   la entidad con su propio criterio.
3. Para justificar una decisión ante el cliente o el asesor, usa get_evidence con el campo concreto.
4. get_client_context da un resumen breve para orientar el tono de la conversación.

Los datos de la demo son simulados. Este servidor no recomienda productos: solo describe al cliente.
"""


def _seguridad() -> TransportSecuritySettings:
    """Protección DNS rebinding: localhost siempre; los hosts públicos (túnel, despliegue) por variable."""
    extra = [h.strip() for h in os.getenv("MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
    if "*" in extra:  # solo para pruebas rápidas con un túnel cuyo nombre cambia
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    hosts = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*", *extra]
    origins = ["http://localhost:*", "http://127.0.0.1:*", *(f"https://{h}" for h in extra)]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins
    )


# Las cuatro herramientas solo leen: así lo declaran a los clientes MCP (Claude puede tratarlas como seguras).
SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

mcp = FastMCP(
    name="perfil-inversor",
    instructions=INSTRUCCIONES,
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    transport_security=_seguridad(),
)


def _error(e: Exception, client_id: str) -> dict[str, Any]:
    return {"error": "not_found", "client_id": client_id, "detail": str(e)}


def _autorizar(client_id: str) -> None:
    """Credencial de cliente, de servicio o de demostración (fija o de operador: solo sus clientes ficticios)."""
    # FastMCP transmite la Request HTTP en request_context (SDK instalado).
    # Una invocación directa sin contexto tampoco puede saltarse esta comprobación.
    try:
        request = mcp.get_context().request_context.request
    except (ValueError, LookupError):
        request = None
    cabeceras = request.headers if request is not None else {}
    autorizacion, admin = cabeceras.get("authorization"), cabeceras.get("x-admin-token")
    clientes_demo = acceso.alcance_demo_mcp(autorizacion, admin)
    if clientes_demo is not None:  # credencial de demostración: solo sus clientes ficticios
        if client_id not in clientes_demo:
            raise HTTPException(404, "Recurso no encontrado")
        return
    acceso.exigir_cliente(client_id, autorizacion, admin)


def _perfil(client_id: str, version: int | None = None):
    _autorizar(client_id)
    return store.perfil(client_id, version) if version else store.perfil_para_consumidor(client_id)


@mcp.tool(annotations=SOLO_LECTURA)
def get_client_profile(client_id: str, version: int | None = None) -> dict[str, Any]:
    """Perfil inversor completo del cliente: cada dato con su fuente, confianza, evidencias y flags,
    los resultados de idoneidad y conveniencia y las alertas abiertas.

    Sin `version`, devuelve el perfil activo más reciente (o el último, con usable=false, si ninguno
    está activo) y `pending_review`: qué datos están en revisión en una versión posterior. Con `version`,
    esa versión concreta del historial.
    """
    try:
        p = _perfil(client_id, version)
    except store.NoEncontrado as e:
        return _error(e, client_id)
    datos = p.model_dump(mode="json")
    datos["usable"] = p.status == EstadoPerfil.active
    if not version:
        pendiente = store.revision_pendiente(client_id, p)
        datos["pending_review"] = pendiente.model_dump(mode="json") if pendiente else None
    return datos


@mcp.tool(annotations=SOLO_LECTURA)
def get_investment_constraints(client_id: str) -> dict[str, Any]:
    """Reglas que cualquier propuesta de inversión debe cumplir para este cliente, ya expresadas como
    criterios del catálogo de MyInvestor: `funds_query` (búsqueda de fondos), `portfolios_query`
    (carteras automatizadas), `post_filters` (comprobaciones sobre cada ficha), `appropriateness`
    (conveniencia por familia de producto), `blocked_searches` (qué no se busca: fondos, carteras, ETF o
    acciones) y `rationale` (por qué). Si `usable` es false, no recomendar.
    Si `pending_review` no es null, esas rutas están en revisión en una versión posterior aún sin validar:
    no apoyar ninguna recomendación en ellas hasta que la entidad valide.
    Una lista dentro de `funds_query` (como `asset_type`) significa "cualquiera de estos valores": si el
    buscador solo admite uno, se hace una búsqueda por valor.
    """
    _autorizar(client_id)
    try:
        return store.restricciones_para_consumidor(client_id).model_dump(mode="json")
    except store.NoEncontrado as e:
        return _error(e, client_id)


@mcp.tool(annotations=SOLO_LECTURA)
def get_evidence(client_id: str, field: str) -> dict[str, Any]:
    """Pruebas que justifican un dato del perfil: cita literal, segundos [inicio, fin] en la grabación y
    URL del clip de audio si existe. `field` es la ruta del dato, por ejemplo `knowledge.equity_funds`
    o `risk_tolerance.scenario_score`. Si el dato es calculado, devuelve los datos de los que sale.
    """
    _autorizar(client_id)
    try:
        p = store.perfil_para_consumidor(client_id)
    except store.NoEncontrado as e:
        return _error(e, client_id)
    f = p.mifid.get(field)
    if f is None:
        return {"error": "unknown_field", "field": field, "available_fields": sorted(p.mifid)}
    return {
        "client_id": client_id,
        "profile_version": p.version,
        "field": field,
        "value": f.value,
        "declared": f.declared,
        "source": f.source.value,
        "confidence": f.confidence,
        "flags": [x.value for x in f.flags],
        "inputs": f.inputs,
        "evidence": [e.model_dump(mode="json") for e in f.evidence],
    }


@mcp.tool(annotations=SOLO_LECTURA)
async def get_client_context(client_id: str) -> dict[str, Any]:
    """Resumen breve del cliente (150 palabras como máximo) escrito para otro agente: objetivo, perfil de
    riesgo, familias no convenientes y alertas abiertas. Úsalo para orientar la conversación, no como
    sustituto de get_investment_constraints.
    """
    _autorizar(client_id)
    try:
        p = store.perfil_para_consumidor(client_id)
    except store.NoEncontrado as e:
        return _error(e, client_id)
    pendiente = store.revision_pendiente(client_id, p)
    return {
        "client_id": client_id,
        "profile_version": p.version,
        "usable": p.status == EstadoPerfil.active,
        "pending_review": pendiente.model_dump(mode="json") if pendiente else None,
        "text": await contexto.resumen(p),
    }
