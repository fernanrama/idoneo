"""API REST (contrato v1).

Especificación: docs/proyecto/04_CONTRATO_PERFIL.md; implementación y desviaciones: docs/CONTRATOS.md.
Arranque:  uvicorn app.main:app --reload --port 8000   (desde backend/)
Docs interactivas: http://localhost:8000/docs
"""

from __future__ import annotations

import hmac
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # .env en la raíz del repo

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import voz  # noqa: E402
from .agentes import chat as entrevistador  # noqa: E402
from .agentes import claude, contexto, extractor, verificador  # noqa: E402
from .mcp.servidor import mcp  # noqa: E402
from .perfil import calculos, store  # noqa: E402
from .perfil.modelos import Parche, Perfil, Restricciones, Turno  # noqa: E402

log = logging.getLogger("perfil.api")

mcp_app = mcp.streamable_http_app()  # crea el gestor de sesiones MCP; se monta al final del archivo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.tipo_almacen()  # configura el almacén (PERFIL_ALMACEN) y falla pronto si la base no está lista
    if os.getenv("LOAD_DEMO_FIXTURE", "1") == "1":
        store.asegurar_fixture("carmen-68")  # solo si falta: no pisa datos guardados en la base
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="API del perfil", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(voz.router)


def _llamar(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except store.NoEncontrado as e:
        raise HTTPException(404, f"No encontrado: {e}") from e
    except store.Conflicto as e:
        raise HTTPException(409, str(e)) from e
    except store.DatoInvalido as e:
        raise HTTPException(422, str(e)) from e


def requiere_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Si ADMIN_TOKEN está definido, las escrituras de la entidad y de la demo exigen esa cabecera.
    Sin ADMIN_TOKEN (desarrollo local) no se pide nada, para no romper el front."""
    esperado = os.getenv("ADMIN_TOKEN", "")
    if esperado and not hmac.compare_digest((x_admin_token or "").encode(), esperado.encode()):
        raise HTTPException(401, "Falta o no es válida la cabecera X-Admin-Token")


class NuevaSesion(BaseModel):
    client_id: str | None = None
    channel: str = "voice"  # "voice" | "text"


class MensajeChat(BaseModel):
    text: str | None = Field(default=None, max_length=2000)  # vacío = que el asistente empiece


class Validacion(BaseModel):
    advisor_id: str
    changes: list[Parche] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- entrevista ----------

@app.post("/api/sessions")
def crear_sesion(body: NuevaSesion):
    return _llamar(store.crear_sesion, body.client_id, body.channel)


AUTOR_EXTRACTOR, AUTOR_VERIFICADOR = "agent:extractor", "agent:verifier"


def _lista_de(resultado, origen: str, rechazar) -> list:
    """Lo que devuelve un agente debe ser una lista; si no, se rechaza entero de forma visible."""
    if resultado is None:
        return []
    if isinstance(resultado, (list, tuple)):
        return list(resultado)
    rechazar(origen, "error", f"devolvió {type(resultado).__name__} en vez de una lista")
    return []


async def _procesar_turno(session_id: str) -> None:
    """Extractor y verificador sobre el turno nuevo, en segundo plano.

    Aceptación parcial: cada parche y cada alerta se valida por separado (mismas reglas que store:
    esquema, tipos, autoría y evidencia). Los válidos se guardan; los inválidos y los fallos de un
    agente quedan registrados con su motivo y visibles en GET /api/sessions/{id} (`rejections`).
    Si el extractor falla, el verificador se ejecuta igualmente, y al revés.
    """
    try:
        s = store.sesion(session_id)
    except store.NoEncontrado:
        log.error("Turno de una sesión que no existe: %s", session_id)
        return
    cid, turnos = s["client_id"], s["turns"]

    def rechazar(origen: str, tipo: str, motivo: str, path: str | None = None) -> None:
        store.registrar_rechazo(store.Rechazo(session_id=session_id, client_id=cid, origen=origen,
                                              tipo=tipo, path=path, motivo=motivo))

    # 1. Extractor: datos nuevos del perfil.
    try:
        brutos = _lista_de(await extractor.extraer(turnos[-6:], store.perfil(cid), session_id), "extractor", rechazar)
    except Exception as e:
        log.exception("Fallo del extractor en %s", session_id)
        rechazar("extractor", "error", f"el extractor falló: {type(e).__name__}: {str(e)[:300]}")
        brutos = []
    parches, malos = store.separar_parches(brutos, AUTOR_EXTRACTOR)
    for path, motivo in malos:
        rechazar("extractor", "parche", motivo, path)
    if parches:
        try:
            store.aplicar(cid, parches, f"extractor · {session_id}", AUTOR_EXTRACTOR)
        except Exception as e:  # p. ej. demasiadas escrituras simultáneas
            log.exception("No se pudieron guardar los parches de %s", session_id)
            for p in parches:
                rechazar("backend", "parche", f"no se pudo guardar: {str(e)[:300]}", p.path)

    # 2. Verificador: alertas sobre el perfil ya actualizado (aunque el extractor haya fallado).
    try:
        brutas = _lista_de(await verificador.verificar(store.perfil(cid), turnos), "verificador", rechazar)
    except Exception as e:
        log.exception("Fallo del verificador en %s", session_id)
        rechazar("verificador", "error", f"el verificador falló: {type(e).__name__}: {str(e)[:300]}")
        brutas = []
    alertas, malas = store.separar_alertas(brutas)
    for path, motivo in malas:
        rechazar("verificador", "alerta", motivo, path)
    if alertas:
        try:
            store.anadir_alertas(cid, alertas, AUTOR_VERIFICADOR)
        except Exception as e:
            log.exception("No se pudieron guardar las alertas de %s", session_id)
            for a in alertas:
                rechazar("backend", "alerta", f"no se pudo guardar: {str(e)[:300]}", a.path)


@app.post("/api/sessions/{session_id}/turns", status_code=202)
def anadir_turno(session_id: str, turno: Turno, tareas: BackgroundTasks):
    t = _llamar(store.anadir_turno, session_id, turno)
    if turno.speaker == "client":
        tareas.add_task(_procesar_turno, session_id)
    return {"turn_id": t.turn_id}


def _segundos(sesion: dict) -> float:
    """Segundos desde el inicio de la sesión (tiempos de los turnos en modo texto)."""
    inicio = sesion.get("started_at")
    if not isinstance(inicio, datetime):
        return 0.0
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - inicio).total_seconds(), 1)


@app.post("/api/sessions/{session_id}/chat")
async def chat(session_id: str, body: MensajeChat, tareas: BackgroundTasks):
    """Modo texto: guarda el mensaje del cliente (si lo hay) y devuelve la siguiente intervención del
    entrevistador. El perfil lo actualizan el extractor y el verificador en segundo plano, como en la voz."""
    s = _llamar(store.sesion, session_id)
    if not claude.disponible():
        raise HTTPException(503, "Modo texto no disponible: falta ANTHROPIC_API_KEY en el backend")
    cliente = None
    if body.text and body.text.strip():
        t = _segundos(s)
        cliente = _llamar(store.anadir_turno, session_id, Turno(speaker="client", text=body.text.strip(), t_start=t, t_end=t))
        tareas.add_task(_procesar_turno, session_id)
    turnos = store.sesion(session_id)["turns"]
    try:
        r = await entrevistador.responder(turnos[-40:], store.perfil(s["client_id"]))
    except Exception as e:  # rechazo del modelo, red, límite de uso…
        log.exception("Fallo del entrevistador en %s", session_id)
        raise HTTPException(502, f"El entrevistador no pudo responder: {type(e).__name__}") from e
    t = _segundos(s)
    agente = _llamar(store.anadir_turno, session_id, Turno(speaker="agent", text=r.texto, t_start=t, t_end=t))
    return {"client_turn": cliente, "agent_turn": agente, "finished": r.terminada}


@app.get("/api/sessions/{session_id}")
def ver_sesion(session_id: str):
    """Sesión con sus turnos y los rechazos del procesamiento (parches, alertas o fallos de agentes)."""
    s = _llamar(store.sesion, session_id)
    return {**s, "rejections": store.rechazos(session_id)}


# ---------- perfil ----------

@app.get("/api/clients/{client_id}/profile", response_model=Perfil)
def ver_perfil(client_id: str, version: int | None = None):
    """Última versión en cualquier estado (el front la necesita durante la entrevista)."""
    return _llamar(store.perfil, client_id, version)


@app.get("/api/clients/{client_id}/versions")
def ver_versiones(client_id: str):
    return _llamar(store.versiones, client_id)


@app.post("/api/clients/{client_id}/validate", response_model=Perfil, dependencies=[Depends(requiere_admin)])
def validar(client_id: str, body: Validacion):
    return _llamar(store.validar, client_id, body.advisor_id, body.changes)


@app.get("/api/clients/{client_id}/constraints", response_model=Restricciones)
def ver_restricciones(client_id: str):
    """Para consumidores: perfil activo más reciente; si no hay, el último con usable=false."""
    return calculos.restricciones(_llamar(store.perfil_para_consumidor, client_id))


@app.get("/api/clients/{client_id}/evidence/{path}")
def ver_evidencia(client_id: str, path: str):
    p = _llamar(store.perfil, client_id)
    if path not in p.mifid:
        raise HTTPException(404, f"Campo sin datos: {path}")
    f = p.mifid[path]
    return {"path": path, "value": f.value, "source": f.source, "evidence": f.evidence}


@app.get("/api/clients/{client_id}/context")
async def ver_contexto(client_id: str):
    p = _llamar(store.perfil_para_consumidor, client_id)
    return {"client_id": client_id, "text": await contexto.resumen(p)}


@app.post("/api/demo/reset", dependencies=[Depends(requiere_admin)])
def reset_demo():
    """Vuelve a cargar el perfil simulado de Carmen (útil antes de cada ensayo).
    Añade una versión nueva: el historial no se borra. Se apaga con DEMO_ENDPOINTS=0."""
    if os.getenv("DEMO_ENDPOINTS", "1") != "1":
        raise HTTPException(404, "Endpoint de demo desactivado")
    return _llamar(store.cargar_fixture, "carmen-68")


# ---------- MCP ----------
# Servidor MCP en /mcp (transporte HTTP). Se monta en la raíz y al final para que las rutas de arriba
# tengan prioridad y la URL sea exactamente /mcp, sin redirección a /mcp/.
app.mount("/", mcp_app)
