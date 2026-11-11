"""Pruebas de audio: cada dato del perfil suena con el fragmento de la llamada que lo justifica.

Al acabar una entrevista por voz, el backend descarga de ElevenLabs el audio de la llamada y su
transcripción oficial, alinea esa transcripción con los turnos de la sesión y guarda, una sola vez,
el audio y los tiempos reales de cada turno (`store.guardar_audio`, de solo añadir).

No se recorta el archivo: se guarda el audio completo de la sesión y cada evidencia apunta a su
fragmento `[inicio, fin]`, que el navegador reproduce solo (así no hace falta ffmpeg en el servidor).

Cómo llega la orden de descargar:
- el navegador, al colgar, manda el `conversation_id` (`POST /api/sessions/{id}/audio`); es lo que
  funciona en local, donde el webhook de ElevenLabs no llega;
- el webhook firmado `post_call_transcription` (despliegue), que llama a `programar` tras cerrar la sesión.

Seguridad: el `conversation_id` que manda el navegador no se cree sin más. Se descarga la conversación y
solo se acepta si la creó nuestro agente (`ELEVENLABS_AGENT_ID`) para ESTA sesión (la variable dinámica
`session_id` que pone `voz.contexto_sesion`). Así nadie puede colgar en su perfil el audio de otra persona.
La clave de ElevenLabs nunca sale del backend; el audio solo se sirve con la credencial de la sesión.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from . import acceso
from .agentes.normalizacion import sin_tildes
from .perfil import store
from .perfil.almacenes.base import AudioSesion
from .perfil.modelos import Perfil, Turno

log = logging.getLogger("perfil.audio")

router = APIRouter(prefix="/api", tags=["audio"])

API = "https://api.elevenlabs.io/v1/convai/conversations"
MAX_AUDIO_BYTES = 30 * 1024 * 1024  # unos 30 min de MP3 a 128 kbps
TIPOS_AUDIO = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/ogg", "audio/webm"}
# Esperas entre intentos: ElevenLabs tarda unos segundos (a veces más de un minuto) en tener el audio.
ESPERAS_S = (3.0, 6.0, 12.0, 24.0, 45.0, 90.0)
SIMILITUD_MINIMA = 0.6
VENTANA_ALINEACION = 6   # mensajes oficiales que se miran por delante de la posición actual
MARGEN_S = 0.4           # margen alrededor de cada fragmento, para no cortar la primera sílaba

_estado: dict[str, dict[str, Any]] = {}  # session_id -> {"status": "pending"|"failed", "detail": str}
_en_curso: set[str] = set()


class SinAudioTodavia(Exception):
    """ElevenLabs aún está procesando la llamada: se reintenta más tarde."""


class ConversacionAjena(Exception):
    """La conversación no es de nuestro agente o no se creó para esta sesión: no se reintenta."""


# ---------- configuración ----------

def configurado() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY", "").strip() and os.getenv("ELEVENLABS_AGENT_ID", "").strip())


def _cabeceras() -> dict[str, str]:
    return {"xi-api-key": os.getenv("ELEVENLABS_API_KEY", "").strip()}


# ---------- alineación de la transcripción oficial con los turnos de la sesión ----------

def _normalizar(texto: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9ñ ]", " ", sin_tildes(texto or "").lower()).split())


def _similitud(a: str, b: str) -> float:
    a, b = _normalizar(a), _normalizar(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0 if min(len(a), len(b)) >= 8 else 0.7
    return SequenceMatcher(None, a, b).ratio()


def mensajes_oficiales(transcripcion: list[dict[str, Any]], duracion: float | None) -> list[dict[str, Any]]:
    """Mensajes con texto de la transcripción de ElevenLabs, con su inicio y su fin en segundos.

    ElevenLabs da el segundo en que empieza cada mensaje (`time_in_call_secs`); el fin es el inicio del
    siguiente, o el final de la llamada en el último."""
    utiles = []
    for m in transcripcion or []:
        if not isinstance(m, dict):
            continue
        texto, rol, t = m.get("message"), m.get("role"), m.get("time_in_call_secs")
        if not isinstance(texto, str) or not texto.strip() or rol not in ("user", "agent"):
            continue
        if not isinstance(t, (int, float)) or t < 0:
            continue
        utiles.append({"role": rol, "message": texto.strip(), "start": float(t)})
    for i, m in enumerate(utiles):
        siguiente = utiles[i + 1]["start"] if i + 1 < len(utiles) else None
        if siguiente is not None and siguiente > m["start"]:
            m["end"] = siguiente
        elif duracion and duracion > m["start"]:
            m["end"] = float(duracion)
        else:
            m["end"] = m["start"] + max(2.0, len(m["message"]) / 15)
    return utiles


def alinear(turnos: list[Turno], oficiales: list[dict[str, Any]]) -> dict[str, list[float]]:
    """turn_id -> [inicio, fin] reales. Recorre los turnos en orden y busca, por delante de la última
    coincidencia, el mensaje oficial del mismo hablante más parecido. Un turno sin pareja se queda sin
    tiempo real (su evidencia conserva los tiempos aproximados del navegador)."""
    tiempos: dict[str, list[float]] = {}
    j = 0
    for turno in turnos:
        if not turno.turn_id:
            continue
        rol = "user" if turno.speaker == "client" else "agent"
        mejor, mejor_k = 0.0, None
        for k in range(j, min(len(oficiales), j + VENTANA_ALINEACION)):
            if oficiales[k]["role"] != rol:
                continue
            s = _similitud(turno.text, oficiales[k]["message"])
            if s > mejor:
                mejor, mejor_k = s, k
        if mejor_k is not None and mejor >= SIMILITUD_MINIMA:
            m = oficiales[mejor_k]
            tiempos[turno.turn_id] = [round(m["start"], 2), round(m["end"], 2)]
            j = mejor_k + 1
    return tiempos


# ---------- descarga desde ElevenLabs ----------

def _comprobar_propiedad(datos: dict[str, Any], session_id: str) -> None:
    agente = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    if datos.get("agent_id") != agente:
        raise ConversacionAjena("La conversación no es del agente de este backend")
    inicio = datos.get("conversation_initiation_client_data")
    variables = inicio.get("dynamic_variables") if isinstance(inicio, dict) else None
    if not isinstance(variables, dict) or variables.get("session_id") != session_id:
        raise ConversacionAjena("La conversación no se creó para esta sesión")


async def _descargar_audio(cliente: httpx.AsyncClient, conversation_id: str) -> tuple[bytes, str]:
    async with cliente.stream("GET", f"{API}/{conversation_id}/audio", headers=_cabeceras()) as r:
        if r.status_code in (404, 425):
            raise SinAudioTodavia("ElevenLabs aún no tiene el audio")
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs respondió {r.status_code} al pedir el audio")
        tipo = (r.headers.get("content-type") or "audio/mpeg").split(";")[0].strip().lower()
        if tipo not in TIPOS_AUDIO:
            tipo = "audio/mpeg"
        trozos, total = [], 0
        async for trozo in r.aiter_bytes():
            total += len(trozo)
            if total > MAX_AUDIO_BYTES:
                raise RuntimeError("El audio supera el tamaño máximo admitido")
            trozos.append(trozo)
    datos = b"".join(trozos)
    if not datos:
        raise SinAudioTodavia("ElevenLabs devolvió un audio vacío")
    return datos, tipo


async def recuperar(session_id: str, conversation_id: str) -> bool:
    """Un intento: descarga conversación y audio, alinea y guarda. True si se guardó ahora."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10)) as cliente:
        r = await cliente.get(f"{API}/{conversation_id}", headers=_cabeceras())
        if r.status_code == 404:
            raise ConversacionAjena("ElevenLabs no conoce esa conversación")
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs respondió {r.status_code} al pedir la conversación")
        try:
            datos = r.json()
        except ValueError as e:
            raise RuntimeError("ElevenLabs devolvió una conversación no válida") from e
        if not isinstance(datos, dict):
            raise RuntimeError("ElevenLabs devolvió una conversación no válida")
        _comprobar_propiedad(datos, session_id)
        if datos.get("status") in ("initiated", "in-progress", "processing") or datos.get("has_audio") is False:
            raise SinAudioTodavia(f"Conversación en estado {datos.get('status')}")
        audio, tipo = await _descargar_audio(cliente, conversation_id)

    metadatos = datos.get("metadata") if isinstance(datos.get("metadata"), dict) else {}
    duracion = metadatos.get("call_duration_secs")
    duracion = float(duracion) if isinstance(duracion, (int, float)) and duracion > 0 else None
    oficiales = mensajes_oficiales(datos.get("transcript") or [], duracion)
    tiempos = alinear(store.sesion(session_id)["turns"], oficiales)
    # La conversación queda ligada a la sesión (si el webhook no lo hizo ya). Repetirlo es inocuo.
    store.finalizar_sesion(session_id, conversation_id)
    registro = AudioSesion(
        session_id=session_id, conversation_id=conversation_id, content_type=tipo, size_bytes=len(audio),
        duration_s=duracion, timings=tiempos,
        transcript=[{k: m[k] for k in ("role", "message", "start", "end")} for m in oficiales])
    guardado = store.guardar_audio(registro, audio)
    log.info("Audio de %s: %d bytes, %d de %d turnos con tiempo real", session_id, len(audio), len(tiempos),
             len(store.sesion(session_id)["turns"]))
    return guardado


async def recuperar_con_reintentos(session_id: str, conversation_id: str, esperas=ESPERAS_S) -> None:
    """Tarea en segundo plano: reintenta mientras ElevenLabs procesa la llamada. Nunca lanza."""
    if session_id in _en_curso:
        return
    _en_curso.add(session_id)
    _estado[session_id] = {"status": "pending", "detail": "Descargando el audio de la llamada"}
    try:
        for intento, espera in enumerate((0.0, *esperas)):
            if espera:
                await asyncio.sleep(espera)
            try:
                await recuperar(session_id, conversation_id)
                _estado.pop(session_id, None)
                return
            except SinAudioTodavia as e:
                log.info("Audio de %s aún no disponible (intento %d): %s", session_id, intento + 1, e)
            except (ConversacionAjena, store.Conflicto, store.NoEncontrado, store.DatoInvalido) as e:
                log.warning("Audio de %s rechazado: %s", session_id, e)
                _estado[session_id] = {"status": "failed", "detail": str(e)[:200]}
                return
            except Exception as e:  # red, límite de ElevenLabs…: se reintenta
                log.warning("Fallo al descargar el audio de %s (intento %d): %s", session_id, intento + 1,
                            type(e).__name__)
        _estado[session_id] = {"status": "failed", "detail": "ElevenLabs no entregó el audio a tiempo"}
    finally:
        _en_curso.discard(session_id)


def estado(session_id: str) -> dict[str, Any]:
    info = store.info_audio([session_id]).get(session_id)
    if info is not None:
        return {"status": "ready", "duration_s": info.duration_s, "aligned_turns": len(info.timings),
                "url": url_audio(session_id)}
    return {"status": "none", **_estado.get(session_id, {})}


def programar(tareas: BackgroundTasks, session_id: str, conversation_id: str) -> str:
    """Encola la descarga si hace falta. Devuelve el estado resultante."""
    if not configurado() or not store.audio_disponible():
        return "unavailable"
    if session_id in store.info_audio([session_id]):
        return "ready"
    if session_id not in _en_curso:
        tareas.add_task(recuperar_con_reintentos, session_id, conversation_id)
    return "pending"


# ---------- fragmentos de cada evidencia ----------

def url_audio(session_id: str) -> str:
    return f"/api/sessions/{session_id}/audio"


@dataclass(frozen=True)
class Fragmento:
    session_id: str
    turn_id: str | None
    start: float
    end: float
    exact: bool  # True: tiempos de ElevenLabs; False: los aproximados del navegador

    def vista(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "turn_id": self.turn_id, "start": self.start, "end": self.end,
                "exact": self.exact, "url": url_audio(self.session_id)}


def fragmento(evidencia, info: AudioSesion | None) -> Fragmento | None:
    """Dónde suena una evidencia dentro del audio de su sesión, o None si esa sesión no tiene audio."""
    if info is None:
        return None
    real = info.timings.get(evidencia.turn_id) if evidencia.turn_id else None
    inicio, fin = (real if real else evidencia.t)
    limite = info.duration_s or float("inf")
    inicio = max(0.0, float(inicio) - MARGEN_S)
    fin = min(limite, float(fin) + MARGEN_S)
    if fin <= inicio:
        return None
    return Fragmento(evidencia.session_id, evidencia.turn_id, round(inicio, 2), round(fin, 2), exact=bool(real))


def fragmentos_del_perfil(perfil: Perfil) -> dict[str, list[dict[str, Any] | None]]:
    """ruta -> un fragmento (o None) por cada evidencia del dato, en el mismo orden que `evidence`."""
    sesiones = {e.session_id for f in perfil.mifid.values() for e in f.evidence}
    infos = store.info_audio(sesiones) if sesiones else {}
    salida: dict[str, list[dict[str, Any] | None]] = {}
    for ruta, f in perfil.mifid.items():
        if not f.evidence:
            continue
        lista = [(fr.vista() if (fr := fragmento(e, infos.get(e.session_id))) else None) for e in f.evidence]
        if any(lista):
            salida[ruta] = lista
    return salida


# ---------- API ----------

class AvisoConversacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")


@router.post("/sessions/{session_id}/audio", status_code=202)
def registrar_conversacion(session_id: str, body: AvisoConversacion, tareas: BackgroundTasks,
                           sesion: dict = Depends(acceso.exigir_sesion)):
    """El navegador avisa al colgar: descarga en segundo plano el audio de esa conversación de ElevenLabs.
    Solo se acepta si la conversación se creó para esta sesión (se comprueba en ElevenLabs)."""
    if sesion.get("channel") != "voice":
        raise HTTPException(409, "Solo las sesiones de voz tienen audio")
    if not configurado():
        raise HTTPException(503, "Voz no configurada en el backend (ELEVENLABS_API_KEY / ELEVENLABS_AGENT_ID)")
    if not store.audio_disponible():
        raise HTTPException(503, "Falta aplicar la migración 0002 (audio de las sesiones)")
    if sesion.get("conversation_id") not in (None, body.conversation_id):
        raise HTTPException(409, "La sesión ya pertenece a otra conversación")
    resultado = programar(tareas, session_id, body.conversation_id)
    return estado(session_id) if resultado == "ready" else {"status": resultado}


@router.get("/sessions/{session_id}/audio/status", dependencies=[Depends(acceso.exigir_sesion)])
def ver_estado(session_id: str):
    return estado(session_id)


@router.get("/sessions/{session_id}/audio", dependencies=[Depends(acceso.exigir_sesion)])
def descargar(session_id: str):
    """El audio completo de la sesión. Cada evidencia dice qué fragmento escuchar."""
    try:
        info, datos = store.audio(session_id)
    except store.NoEncontrado as e:
        raise HTTPException(404, "Esta sesión no tiene audio") from e
    return Response(content=datos, media_type=info.content_type,
                    headers={"Cache-Control": "no-store", "Content-Disposition": "inline"})


@router.get("/clients/{client_id}/audio", dependencies=[Depends(acceso.exigir_cliente)])
def fragmentos(client_id: str, version: int | None = None):
    """Para cada dato del perfil (última versión, o `version`), el fragmento de audio de cada evidencia."""
    try:
        perfil = store.perfil(client_id, version)
    except store.NoEncontrado as e:
        raise HTTPException(404, f"No encontrado: {e}") from e
    return {"client_id": client_id, "profile_version": perfil.version, "available": store.audio_disponible(),
            "evidence": fragmentos_del_perfil(perfil)}
