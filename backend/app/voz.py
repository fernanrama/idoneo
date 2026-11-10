"""Voz (ElevenLabs): bootstrap privado y webhook post-llamada verificado.

La clave nunca llega al navegador. El bootstrap devuelve una URL firmada de un solo uso y una
proyección mínima de la memoria consentida. El webhook solo correlaciona/cierra la sesión: no convierte
automáticamente una transcripción en memoria durable.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from .agentes import chat, memoria
from .perfil import store

router = APIRouter(prefix="/api/voice", tags=["voz"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

URL_ELEVENLABS = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"
MAX_WEBHOOK_BYTES = 1_000_000
MAX_WEBHOOK_AGE_S = 30 * 60
UBICACIONES = {"us", "global", "eu-residency", "in-residency"}


class BootstrapVoz(BaseModel):
    session_id: str


def _sesion(session_id: str) -> dict[str, Any]:
    try:
        return store.sesion(session_id)
    except store.NoEncontrado as e:
        raise HTTPException(404, f"Sesión no encontrada: {session_id}") from e


def _user_id(client_id: str) -> str:
    """Identificador seudónimo de correlación para ElevenLabs; nunca sustituye autenticación."""
    secreto = os.getenv("VOICE_USER_ID_SECRET") or os.getenv("ADMIN_TOKEN") or "idoneo-dev-correlation-only"
    digest = hmac.new(secreto.encode(), client_id.encode(), hashlib.sha256).hexdigest()[:32]
    return f"usr_{digest}"


def contexto_sesion(session_id: str) -> dict[str, Any]:
    sesion = _sesion(session_id)
    perfil = store.perfil(sesion["client_id"])
    variables = memoria.variables(store.personal(sesion["client_id"]), chat.pendientes(perfil))
    # El webhook usa session_id como correlación. No es autorización y no contiene el client_id.
    variables["session_id"] = session_id
    ubicacion = os.getenv("ELEVENLABS_SERVER_LOCATION", "").strip()
    if ubicacion and ubicacion not in UBICACIONES:
        raise HTTPException(500, "ELEVENLABS_SERVER_LOCATION no es válida")
    return {"user_id": _user_id(sesion["client_id"]), "dynamic_variables": variables,
            "server_location": ubicacion or None}


async def _url_firmada() -> str:
    clave = os.getenv("ELEVENLABS_API_KEY", "").strip()
    agente = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    if not clave or not agente:
        raise HTTPException(503, "Voz no configurada en el backend (ELEVENLABS_API_KEY / ELEVENLABS_AGENT_ID)")
    try:
        async with httpx.AsyncClient(timeout=10) as cliente:
            r = await cliente.get(URL_ELEVENLABS, params={"agent_id": agente}, headers={"xi-api-key": clave})
    except httpx.HTTPError as e:
        raise HTTPException(502, "No se pudo conectar con ElevenLabs") from e
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs respondió {r.status_code}")
    try:
        signed_url = r.json().get("signed_url")
    except ValueError as e:
        raise HTTPException(502, "ElevenLabs devolvió una respuesta no válida") from e
    if not isinstance(signed_url, str) or not signed_url:
        raise HTTPException(502, "ElevenLabs no devolvió signed_url")
    return signed_url


@router.get("/signed-url", deprecated=True)
async def url_firmada():
    """Compatibilidad local; desactivada por defecto porque no vincula la URL a una sesión."""
    if os.getenv("ALLOW_LEGACY_SIGNED_URL", "0") != "1":
        raise HTTPException(410, "Ruta obsoleta: usa POST /api/voice/bootstrap")
    return {"signed_url": await _url_firmada()}


@router.post("/bootstrap")
async def bootstrap(body: BootstrapVoz):
    contexto = contexto_sesion(body.session_id)
    return {"signed_url": await _url_firmada(), **contexto}


@router.get("/context/{session_id}")
def obtener_contexto(session_id: str):
    """Contexto sin credenciales para el fallback de agente público; nunca incluye el client_id."""
    return contexto_sesion(session_id)


def _firma_valida(raw: bytes, cabecera: str | None, secreto: str) -> bool:
    pares: dict[str, str] = {}
    for trozo in (cabecera or "").split(","):
        clave, separador, valor = trozo.strip().partition("=")
        if separador and clave in {"t", "v0"}:
            pares[clave] = valor
    try:
        timestamp = int(pares["t"])
    except (KeyError, ValueError):
        return False
    if abs(int(time.time()) - timestamp) > MAX_WEBHOOK_AGE_S:
        return False
    esperado = hmac.new(secreto.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(pares.get("v0", ""), esperado)


async def _cuerpo_acotado(request: Request) -> bytes:
    longitud = request.headers.get("content-length")
    if longitud:
        try:
            if int(longitud) > MAX_WEBHOOK_BYTES:
                raise HTTPException(413, "Webhook demasiado grande")
        except ValueError as e:
            raise HTTPException(400, "Content-Length no válido") from e
    cuerpo = bytearray()
    async for bloque in request.stream():
        cuerpo.extend(bloque)
        if len(cuerpo) > MAX_WEBHOOK_BYTES:
            raise HTTPException(413, "Webhook demasiado grande")
    return bytes(cuerpo)


@webhook_router.post("/elevenlabs")
async def webhook_elevenlabs(request: Request, elevenlabs_signature: str | None = Header(default=None)):
    secreto = os.getenv("ELEVENLABS_WEBHOOK_SECRET", "").strip()
    if not secreto:
        raise HTTPException(503, "Falta ELEVENLABS_WEBHOOK_SECRET")
    raw = await _cuerpo_acotado(request)
    if not _firma_valida(raw, elevenlabs_signature, secreto):
        raise HTTPException(401, "Firma de ElevenLabs no válida")
    try:
        evento = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(400, "JSON no válido") from e
    if evento.get("type") != "post_call_transcription":
        return {"processed": False, "reason": "event_ignored"}
    datos = evento.get("data") if isinstance(evento.get("data"), dict) else {}
    inicio = datos.get("conversation_initiation_client_data")
    inicio = inicio if isinstance(inicio, dict) else {}
    variables = inicio.get("dynamic_variables")
    variables = variables if isinstance(variables, dict) else {}
    session_id, conversation_id = variables.get("session_id"), datos.get("conversation_id")
    if not isinstance(session_id, str) or not isinstance(conversation_id, str):
        raise HTTPException(422, "El webhook no contiene session_id y conversation_id")
    try:
        procesado = store.finalizar_sesion(session_id, conversation_id)
    except store.NoEncontrado as e:
        raise HTTPException(404, "Sesión no encontrada") from e
    except store.DatoInvalido as e:
        raise HTTPException(422, str(e)) from e
    except store.Conflicto as e:
        raise HTTPException(409, str(e)) from e
    return {"processed": procesado, "session_id": session_id, "conversation_id": conversation_id}
