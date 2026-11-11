"""API REST (contrato v1).

Especificación: docs/diseno/03-contrato-perfil.md; implementación y desviaciones: docs/contratos.md.
Arranque:  uvicorn app.main:app --reload --port 8000   (desde backend/)
Docs interactivas: http://localhost:8000/docs
"""

from __future__ import annotations

import asyncio
import logging
import json
import re
import uuid
import os
import weakref
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # .env en la raíz del repo

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field, field_validator  # noqa: E402

from . import acceso, asesor_demo, demo_operador, limites, voz  # noqa: E402
from .agentes import chat as entrevistador  # noqa: E402
from .agentes import claude, contexto, extractor, verificador  # noqa: E402
from .mcp import demo as mcp_demo  # noqa: E402
from .ops import evaluaciones, trazas  # noqa: E402
from .mcp.servidor import mcp  # noqa: E402
from .perfil import calculos, revision, store  # noqa: E402
from .perfil.modelos import EstadoPerfil, Parche, Perfil, Restricciones, Turno  # noqa: E402

log = logging.getLogger("perfil.api")

mcp_app = mcp.streamable_http_app()  # crea el gestor de sesiones MCP; se monta al final del archivo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.tipo_almacen()  # configura el almacén (PERFIL_ALMACEN) y falla pronto si la base no está lista
    if os.getenv("LOAD_DEMO_FIXTURE", "1") == "1":
        store.asegurar_fixture("carmen-68")  # solo si falta: no pisa datos guardados en la base
        store.asegurar_fixture("carmen-corta")  # entrevista corta del pitch (DATOS SIMULADOS)
    asesor_demo.avisar_si_activo()  # DEMO_ADVISOR_MODE: apagado por defecto
    mcp_demo.avisar_si_activa()  # MCP_DEMO_TOKEN: desactivada por defecto
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="API del perfil", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag"],
)
app.include_router(voz.router)
app.include_router(voz.webhook_router)
app.include_router(asesor_demo.router)  # 404 salvo DEMO_ADVISOR_MODE=1 (docs/modo-asesor-demo.md)
app.include_router(demo_operador.router)  # ídem; solo local y con X-Admin-Token


def _llamar(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except store.NoEncontrado as e:
        raise HTTPException(404, f"No encontrado: {e}") from e
    except store.PrecondicionRequerida as e:
        raise HTTPException(428, str(e)) from e
    except store.RevisionObsoleta as e:
        raise HTTPException(412, str(e)) from e
    except store.Conflicto as e:
        raise HTTPException(409, str(e)) from e
    except store.DatoInvalido as e:
        raise HTTPException(422, str(e)) from e


def requiere_admin(x_admin_token: str | None = Header(default=None)) -> None:
    acceso.exigir_servicio(x_admin_token)


@app.middleware("http")
async def respuestas_privadas(request: Request, call_next):
    respuesta = await call_next(request)
    if request.url.path.startswith(("/api/clients/", "/api/sessions", "/api/voice/", "/api/demo/asesor", "/api/demo/operador", "/mcp")):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


class NuevaSesion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    channel: Literal["voice", "text"] = "voice"


class PeticionRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reasons: list[str] = Field(min_length=1, max_length=8)


class MensajeChat(BaseModel):
    text: str | None = Field(default=None, max_length=2000)  # vacío = que el asistente empiece


class Validacion(BaseModel):
    advisor_id: str
    changes: list[Parche] = []


class ActualizacionMemoria(BaseModel):
    """Consentimiento explícito del poseedor autorizado, independiente de MiFID."""

    model_config = ConfigDict(extra="forbid")
    consent_given: Literal[True]
    updates: dict[str, Any] = Field(default_factory=dict)
    forget: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("consent_given", mode="before")
    @classmethod
    def consentimiento_literal(cls, valor):
        if valor is not True:
            raise ValueError("Debe aceptar explícitamente la memoria personal")
        return valor


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- entrevista ----------

@app.post("/api/sessions")
def crear_sesion(body: NuevaSesion, authorization: str | None = Header(default=None),
                 x_admin_token: str | None = Header(default=None)):
    if body.client_id is not None:
        acceso.exigir_cliente(body.client_id, authorization, x_admin_token)
        return _llamar(store.crear_sesion, body.client_id, body.channel)
    # Verificar configuración antes de alterar el almacén; solo un alta exclusiva emite posesión.
    emitir = acceso.preparar_emision()
    limites.consumir("sesion", "LIMITE_SESIONES_DIA")  # tope de gasto en un despliegue público
    cid = f"cliente-{uuid.uuid4().hex}"
    _llamar(store.crear_nuevo, cid)
    sesion = _llamar(store.crear_sesion, cid, body.channel)
    return {**sesion, "access_token": emitir(cid)}


AUTOR_EXTRACTOR, AUTOR_VERIFICADOR = "agent:extractor", "agent:verifier"


def _lista_de(resultado, origen: str, rechazar) -> list:
    """Lo que devuelve un agente debe ser una lista; si no, se rechaza entero de forma visible."""
    if resultado is None:
        return []
    if isinstance(resultado, (list, tuple)):
        return list(resultado)
    rechazar(origen, "error", f"devolvió {type(resultado).__name__} en vez de una lista")
    return []


_candados_sesion: "weakref.WeakValueDictionary[str, asyncio.Lock]" = weakref.WeakValueDictionary()


async def _procesar_turno(session_id: str) -> None:
    """Un procesamiento por sesión a la vez: si el cliente habla dos veces seguidas, el segundo espera y
    trabaja sobre el perfil que ya dejó el primero (sin carreras entre extracciones)."""
    candado = _candados_sesion.get(session_id)
    if candado is None:
        candado = _candados_sesion[session_id] = asyncio.Lock()
    async with candado:
        with trazas.ejecucion("turno", session_id) as traza:
            traza.resultado = await _procesar_turno_sin_candado(session_id)


async def _procesar_turno_sin_candado(session_id: str) -> dict:
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
        return {"error": "sesion_inexistente"}
    cid, turnos = s["client_id"], s["turns"]
    cuenta = {"parches": 0, "alertas": 0, "rechazos": 0}

    def rechazar(origen: str, tipo: str, motivo: str, path: str | None = None) -> None:
        cuenta["rechazos"] += 1
        store.registrar_rechazo(store.Rechazo(session_id=session_id, client_id=cid, origen=origen,
                                              tipo=tipo, path=path, motivo=motivo))

    # 1. Extractor: datos nuevos del perfil.
    try:
        brutos = _lista_de(await extractor.extraer(turnos, store.perfil(cid), session_id), "extractor", rechazar)
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
            cuenta["parches"] = len(parches)
        except Exception as e:  # p. ej. demasiadas escrituras simultáneas
            log.exception("No se pudieron guardar los parches de %s", session_id)
            for p in parches:
                rechazar("backend", "parche", f"no se pudo guardar: {str(e)[:300]}", p.path)

    # 2. Verificador: alertas sobre el perfil ya actualizado (aunque el extractor haya fallado).
    try:
        brutas = _lista_de(await verificador.verificar(store.perfil(cid), turnos, session_id), "verificador", rechazar)
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
            cuenta["alertas"] = len(alertas)
        except Exception as e:
            log.exception("No se pudieron guardar las alertas de %s", session_id)
            for a in alertas:
                rechazar("backend", "alerta", f"no se pudo guardar: {str(e)[:300]}", a.path)
    return cuenta


@app.post("/api/sessions/{session_id}/turns", dependencies=[Depends(acceso.exigir_sesion)], status_code=202)
def anadir_turno(session_id: str, turno: Turno, tareas: BackgroundTasks):
    if turno.speaker == "client":
        limites.comprobar_turnos(_turnos_cliente(session_id))
    t = _llamar(store.anadir_turno, session_id, turno)
    if turno.speaker == "client":
        tareas.add_task(_procesar_turno, session_id)
    return {"turn_id": t.turn_id}


def _turnos_cliente(session_id: str) -> int:
    return sum(1 for t in _llamar(store.sesion, session_id)["turns"] if t.speaker == "client")


def _segundos(sesion: dict) -> float:
    """Segundos desde el inicio de la sesión (tiempos de los turnos en modo texto)."""
    inicio = sesion.get("started_at")
    if not isinstance(inicio, datetime):
        return 0.0
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - inicio).total_seconds(), 1)


@app.post("/api/sessions/{session_id}/chat", dependencies=[Depends(acceso.exigir_sesion)])
async def chat(session_id: str, body: MensajeChat, tareas: BackgroundTasks):
    """Modo texto: guarda el mensaje del cliente (si lo hay) y devuelve la siguiente intervención del
    entrevistador. El perfil lo actualizan el extractor y el verificador en segundo plano, como en la voz."""
    s = _llamar(store.sesion, session_id)
    if not claude.disponible():
        raise HTTPException(503, "Modo texto no disponible: falta ANTHROPIC_API_KEY en el backend")
    cliente = None
    if body.text and body.text.strip():
        limites.comprobar_turnos(sum(1 for x in s["turns"] if x.speaker == "client"))
        t = _segundos(s)
        cliente = _llamar(store.anadir_turno, session_id, Turno(speaker="client", text=body.text.strip(), t_start=t, t_end=t))
        tareas.add_task(_procesar_turno, session_id)
    turnos = store.sesion(session_id)["turns"]
    try:
        with trazas.ejecucion("chat", session_id) as traza:
            r = await entrevistador.responder(turnos[-40:], store.perfil(s["client_id"]),
                                              _llamar(revision.en_curso, s["client_id"]))
            traza.resultado = {"terminada": r.terminada}
    except Exception as e:  # rechazo del modelo, red, límite de uso…
        log.exception("Fallo del entrevistador en %s", session_id)
        raise HTTPException(502, f"El entrevistador no pudo responder: {type(e).__name__}") from e
    t = _segundos(s)
    agente = _llamar(store.anadir_turno, session_id, Turno(speaker="agent", text=r.texto, t_start=t, t_end=t))
    return {"client_turn": cliente, "agent_turn": agente, "finished": r.terminada}


@app.get("/api/sessions/{session_id}/trace", dependencies=[Depends(acceso.exigir_sesion)])
def traza_sesion(session_id: str):
    """Trazas de esta sesión: cada turno procesado y cada respuesta, con sus llamadas a Claude.

    Solo recuentos, tiempos, versiones de prompt y coste estimado; nunca texto del cliente ni del modelo."""
    _llamar(store.sesion, session_id)
    return {"session_id": session_id, "runs": trazas.de_sesion(session_id)}


# ---------- LLMOps ----------

@app.get("/api/ops/metrics")
def metricas_ops():
    """Agregado de las trazas desde que arrancó el backend: latencia p50/p95, tokens, caché, coste estimado
    y fallos por agente, por tipo de ejecución y por versión de prompt. Sin identificadores de sesión."""
    return trazas.resumen()


@app.get("/api/ops/evals")
def evaluaciones_ops():
    """Última evaluación registrada de cada componente, comparada con sus umbrales de calidad."""
    return evaluaciones.estado()


@app.get("/api/sessions/{session_id}", dependencies=[Depends(acceso.exigir_sesion)])
def ver_sesion(session_id: str):
    """Sesión con sus turnos y los rechazos del procesamiento (parches, alertas o fallos de agentes)."""
    s = _llamar(store.sesion, session_id)
    return {**s, "rejections": store.rechazos(session_id)}


ESPERA_PENDIENTES_S = 4.0


@app.get("/api/sessions/{session_id}/pending", dependencies=[Depends(acceso.exigir_sesion)])
async def pendientes(session_id: str):
    """Qué falta por preguntar: lo consulta el agente de voz con su herramienta `datos_pendientes`
    (el modo texto recibe la misma lista dentro del mensaje). Si el último turno se está procesando,
    espera un poco a que acabe para no pedir otra vez lo que el cliente acaba de decir."""
    s = _llamar(store.sesion, session_id)
    candado = _candados_sesion.get(session_id)
    if candado is not None and candado.locked():
        try:
            await asyncio.wait_for(candado.acquire(), ESPERA_PENDIENTES_S)
            candado.release()
        except asyncio.TimeoutError:
            pass
    perfil = store.perfil(s["client_id"])
    rev = _llamar(revision.en_curso, s["client_id"])
    return {"pending": entrevistador.pendientes(perfil, rev), "text": entrevistador.pendientes_para_voz(perfil, rev)}


def _vista_capa(capa) -> dict[str, Any]:
    revision = capa.version if capa else 0
    if capa is None or not capa.consent_given:
        return {"enabled": False, "version": revision, "data": {}}
    return {"enabled": True, "version": revision, "data": capa.data, "consent_at": capa.consent_at}


def _vista_memoria(session_id: str) -> dict[str, Any]:
    sesion = _llamar(store.sesion, session_id)
    return _vista_capa(_llamar(store.personal, sesion["client_id"]))


def _etag(respuesta: Response, vista: dict[str, Any]):
    respuesta.headers["ETag"] = f'"personal-{vista["version"]}"'
    return vista


def _revision(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(428, "If-Match es obligatorio para modificar memoria")
    coincidencia = re.fullmatch(r'"personal-(0|[1-9][0-9]{0,18})"', if_match)
    if coincidencia is None:
        raise HTTPException(412, "If-Match debe contener la revisión personal vigente")
    return int(coincidencia.group(1))


@app.get("/api/sessions/{session_id}/memory", dependencies=[Depends(acceso.exigir_sesion)])
def ver_memoria(session_id: str, response: Response):
    return _etag(response, _vista_memoria(session_id))


@app.put("/api/sessions/{session_id}/memory", dependencies=[Depends(acceso.exigir_sesion)])
def actualizar_memoria(session_id: str, body: ActualizacionMemoria, response: Response,
                       if_match: str | None = Header(default=None)):
    revision = _revision(if_match)
    sesion = _llamar(store.sesion, session_id)
    capa = _llamar(store.actualizar_personal, sesion["client_id"], body.updates, body.forget,
                  "agent:memory", version_esperada=revision, consentimiento=body.consent_given)
    return _etag(response, _vista_capa(capa))


@app.delete("/api/sessions/{session_id}/memory", dependencies=[Depends(acceso.exigir_sesion)])
def borrar_memoria(session_id: str, response: Response, if_match: str | None = Header(default=None)):
    revision = _revision(if_match)
    sesion = _llamar(store.sesion, session_id)
    borradas, capa = _llamar(store.revocar_personal, sesion["client_id"], version_esperada=revision,
                            autor="agent:memory")
    return _etag(response, {**_vista_capa(capa), "deleted_versions": borradas})


# ---------- perfil ----------

@app.get("/api/clients/{client_id}/profile", dependencies=[Depends(acceso.exigir_cliente)], response_model=Perfil)
def ver_perfil(client_id: str, version: int | None = None):
    """Última versión en cualquier estado (el front la necesita durante la entrevista)."""
    return _llamar(store.perfil, client_id, version)


@app.get("/api/clients/{client_id}/versions", dependencies=[Depends(acceso.exigir_cliente)])
def ver_versiones(client_id: str):
    return _llamar(store.versiones, client_id)


@app.post("/api/clients/{client_id}/validate", response_model=Perfil, dependencies=[Depends(acceso.exigir_propietario), Depends(requiere_admin)])
def validar(client_id: str, body: Validacion):
    return _llamar(store.validar, client_id, body.advisor_id, body.changes)


@app.get("/api/clients/{client_id}/constraints", dependencies=[Depends(acceso.exigir_cliente)], response_model=Restricciones)
def ver_restricciones(client_id: str):
    """Para consumidores: perfil activo más reciente; si no hay, el último con usable=false.
    `pending_review` dice qué datos están en revisión en una versión posterior (no usarlos para recomendar)."""
    return _llamar(store.restricciones_para_consumidor, client_id)


# ---------- perfil vivo: microentrevista de revisión y antes/después ----------

@app.get("/api/review-reasons")
def motivos_revision():
    """Qué puede contar el cliente en «Ha cambiado algo». Catálogo cerrado."""
    return revision.opciones()


@app.get("/api/clients/{client_id}/review", dependencies=[Depends(acceso.exigir_cliente)])
def ver_revision(client_id: str):
    """Revisión en curso: motivos, preguntas (con lo que consta) y cuáles ya se han contestado."""
    return revision.vista(_llamar(revision.en_curso, client_id))


@app.post("/api/clients/{client_id}/review/preview", dependencies=[Depends(acceso.exigir_cliente)])
def previsualizar_revision(client_id: str, body: PeticionRevision):
    """Qué se preguntaría con estos motivos. No escribe nada."""
    return revision.vista(_llamar(revision.previsualizar, client_id, body.reasons))


@app.post("/api/clients/{client_id}/review", dependencies=[Depends(acceso.exigir_cliente)], status_code=201)
def abrir_revision(client_id: str, body: PeticionRevision):
    """Abre la revisión (versión nueva en borrador). Después se abre una sesión normal con este cliente."""
    return revision.vista(_llamar(revision.abrir, client_id, body.reasons))


@app.get("/api/clients/{client_id}/changes", dependencies=[Depends(acceso.exigir_cliente)])
def ver_cambios(client_id: str):
    """Último perfil validado frente al último guardado: qué cambia y qué efecto tiene. null si nada."""
    c = _llamar(revision.comparar, client_id)
    return c.model_dump(mode="json") if c else None


@app.get("/api/clients/{client_id}/evidence/{path}", dependencies=[Depends(acceso.exigir_cliente)])
def ver_evidencia(client_id: str, path: str):
    p = _llamar(store.perfil, client_id)
    if path not in p.mifid:
        raise HTTPException(404, f"Campo sin datos: {path}")
    f = p.mifid[path]
    return {"path": path, "value": f.value, "source": f.source, "evidence": f.evidence}


@app.get("/api/clients/{client_id}/context", dependencies=[Depends(acceso.exigir_cliente)])
async def ver_contexto(client_id: str):
    p = _llamar(store.perfil_para_consumidor, client_id)
    pendiente = store.revision_pendiente(client_id, p)
    return {"client_id": client_id, "text": await contexto.resumen(p),
            "pending_review": pendiente.model_dump(mode="json") if pendiente else None}


def _perfil_demo_fijo() -> Perfil:
    if os.getenv("DEMO_ENDPOINTS", "1") != "1":
        raise HTTPException(404, "Endpoint de demo desactivado")
    datos = json.loads((store.FIXTURES_DIR / "carmen-68.json").read_text(encoding="utf-8"))
    datos["personal"] = {}
    perfil = Perfil.model_validate(datos)
    calculos.recalcular(perfil)
    perfil.status = EstadoPerfil.pending_validation if perfil.assessments.suitability.complete else EstadoPerfil.draft
    return perfil


@app.get("/api/demo/profile", response_model=Perfil)
def perfil_demo():
    """Fixture fijo y ficticio; no lee la memoria ni el estado persistido de Carmen."""
    return _perfil_demo_fijo()


@app.get("/api/demo/constraints", response_model=Restricciones)
def restricciones_demo():
    return calculos.restricciones(_perfil_demo_fijo())


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
app.mount("/", acceso.TransporteMCPAutorizado(mcp_app))
