"""API REST (contrato v1).

Especificación: docs/proyecto/04_CONTRATO_PERFIL.md; implementación y desviaciones: docs/CONTRATOS.md.
Arranque:  uvicorn app.main:app --reload --port 8000   (desde backend/)
Docs interactivas: http://localhost:8000/docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # .env en la raíz del repo

from fastapi import BackgroundTasks, FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import voz  # noqa: E402
from .agentes import contexto, extractor, verificador  # noqa: E402
from .mcp.servidor import mcp  # noqa: E402
from .perfil import calculos, store  # noqa: E402
from .perfil.modelos import Parche, Perfil, Restricciones, Turno  # noqa: E402


mcp_app = mcp.streamable_http_app()  # crea el gestor de sesiones MCP; se monta al final del archivo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.getenv("LOAD_DEMO_FIXTURE", "1") == "1":
        store.cargar_fixture("carmen-68")
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


class NuevaSesion(BaseModel):
    client_id: str | None = None
    channel: str = "voice"  # "voice" | "text"


class Validacion(BaseModel):
    advisor_id: str
    changes: list[Parche] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- entrevista ----------

@app.post("/api/sessions")
def crear_sesion(body: NuevaSesion):
    return store.crear_sesion(body.client_id)


async def _procesar_turno(session_id: str) -> None:
    s = store.sesion(session_id)
    cid, turnos = s["client_id"], s["turns"]
    parches = await extractor.extraer(turnos[-6:], store.perfil(cid), session_id)
    if parches:
        store.aplicar(cid, parches, f"extractor · {session_id}", "agent:extractor")
    alertas = await verificador.verificar(store.perfil(cid), turnos)
    if alertas:
        store.anadir_alertas(cid, alertas)


@app.post("/api/sessions/{session_id}/turns", status_code=202)
def anadir_turno(session_id: str, turno: Turno, tareas: BackgroundTasks):
    t = _llamar(store.anadir_turno, session_id, turno)
    if turno.speaker == "client":
        tareas.add_task(_procesar_turno, session_id)
    return {"turn_id": t.turn_id}


@app.get("/api/sessions/{session_id}")
def ver_sesion(session_id: str):
    return _llamar(store.sesion, session_id)


# ---------- perfil ----------

@app.get("/api/clients/{client_id}/profile", response_model=Perfil)
def ver_perfil(client_id: str, version: int | None = None):
    """Última versión en cualquier estado (el front la necesita durante la entrevista)."""
    return _llamar(store.perfil, client_id, version)


@app.get("/api/clients/{client_id}/versions")
def ver_versiones(client_id: str):
    return _llamar(store.versiones, client_id)


@app.post("/api/clients/{client_id}/validate", response_model=Perfil)
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


@app.post("/api/demo/reset")
def reset_demo():
    """Vuelve a cargar el perfil simulado de Carmen (útil antes de cada ensayo)."""
    return store.cargar_fixture("carmen-68")


# ---------- MCP ----------
# Servidor MCP en /mcp (transporte HTTP). Se monta en la raíz y al final para que las rutas de arriba
# tengan prioridad y la URL sea exactamente /mcp, sin redirección a /mcp/.
app.mount("/", mcp_app)
