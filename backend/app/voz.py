"""Voz (ElevenLabs). La clave nunca llega al navegador: el backend pide una URL firmada de un solo uso.

Endpoint de ElevenLabs usado: GET /v1/convai/conversation/get-signed-url?agent_id=...
(con cabecera xi-api-key). PENDIENTE de verificar con la cuenta real del equipo.
Si no hay clave configurada responde 503 y el front intenta con un agente público (agentId).
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/voice", tags=["voz"])

URL_ELEVENLABS = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


@router.get("/signed-url")
async def url_firmada():
    clave, agente = os.getenv("ELEVENLABS_API_KEY"), os.getenv("ELEVENLABS_AGENT_ID")
    if not clave or not agente:
        raise HTTPException(503, "Voz no configurada en el backend (ELEVENLABS_API_KEY / ELEVENLABS_AGENT_ID)")
    async with httpx.AsyncClient(timeout=10) as cliente:
        r = await cliente.get(URL_ELEVENLABS, params={"agent_id": agente}, headers={"xi-api-key": clave})
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs respondió {r.status_code}")
    return {"signed_url": r.json()["signed_url"]}
