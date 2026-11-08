"""API REST de Idóneo (contrato v0, ver docs/CONTRATOS.md).

Arranque:  uvicorn app.main:app --reload --port 8000   (desde backend/)
Docs interactivas: http://localhost:8000/docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agentes import contexto, extractor, verificador
from .perfil import calculos, store
from .perfil.modelos import ActualizacionCampo, Autor, Perfil, Restricciones, Turno


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.getenv("LOAD_DEMO_FIXTURE", "1") == "1":
        store.cargar_fixture("carmen-68")
    yield


app = FastAPI(title="Idóneo API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


def _404(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except store.NoEncontrado as e:
        raise HTTPException(404, f"No encontrado: {e}") from e


class NuevaSesion(BaseModel):
    client_id: str | None = None


class Validacion(BaseModel):
    advisor_id: str
    corrections: list[ActualizacionCampo] = []


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
    cambios = await extractor.extraer(turnos[-6:], store.perfil(cid), session_id)
    if cambios:
        store.aplicar(cid, cambios, f"extractor · sesión {session_id}", Autor.extractor)
    alertas = await verificador.verificar(store.perfil(cid), turnos)
    if alertas:
        store.anadir_alertas(cid, alertas)


@app.post("/api/sessions/{session_id}/turns", status_code=202)
def anadir_turno(session_id: str, turno: Turno, tareas: BackgroundTasks):
    idx = _404(store.anadir_turno, session_id, turno)
    if turno.speaker == "client":
        tareas.add_task(_procesar_turno, session_id)
    return {"turn_index": idx}


@app.get("/api/sessions/{session_id}")
def ver_sesion(session_id: str):
    return _404(store.sesion, session_id)


# ---------- perfil ----------

@app.get("/api/clients/{client_id}/profile", response_model=Perfil)
def ver_perfil(client_id: str, version: int | None = None):
    return _404(store.perfil, client_id, version)


@app.get("/api/clients/{client_id}/profile/versions")
def ver_versiones(client_id: str):
    return _404(store.versiones, client_id)


@app.post("/api/clients/{client_id}/profile/validate", response_model=Perfil)
def validar(client_id: str, body: Validacion):
    _404(store.perfil, client_id)
    return store.validar(client_id, body.advisor_id, body.corrections)


@app.get("/api/clients/{client_id}/constraints", response_model=Restricciones)
def ver_restricciones(client_id: str):
    return calculos.restricciones(_404(store.perfil, client_id))


@app.get("/api/clients/{client_id}/evidence/{field}")
def ver_evidencia(client_id: str, field: str):
    p = _404(store.perfil, client_id)
    if field not in p.mifid:
        raise HTTPException(404, f"Campo sin datos: {field}")
    c = p.mifid[field]
    return {"field": field, "value": c.value, "source": c.source, "evidence": c.evidence}


@app.get("/api/clients/{client_id}/context")
async def ver_contexto(client_id: str):
    return {"client_id": client_id, "text": await contexto.resumen(_404(store.perfil, client_id))}


@app.post("/api/demo/reset")
def reset_demo():
    """Vuelve a cargar el perfil simulado de Carmen (útil antes de cada ensayo)."""
    return store.cargar_fixture("carmen-68")
