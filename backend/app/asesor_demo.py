"""Modo asesor de demostración (DATOS SIMULADOS). Desactivado por defecto.

Recupera el paso «Validar perfil» del pitch sin reabrir la autovalidación que cerró la PR #21:

- Autorización propia: cabecera `X-Demo-Advisor-Token` con `DEMO_ADVISOR_TOKEN`. No se lee
  `Authorization`, así que ni el Bearer del cliente ni un `client_id` o `session_id` dan permiso
  de asesor. Debe ser distinto de `ADMIN_TOKEN`, `CLIENT_ACCESS_SECRET` y `VOICE_USER_ID_SECRET`.
- Solo clientes ficticios: `DEMO_ADVISOR_CLIENTS` (por defecto `carmen-68,carmen-corta`), fixtures de `backend/fixtures/`
  marcados como «DATOS SIMULADOS», y los clientes nuevos que un operador autorice explícitamente
  (demo_operador.py y demo_autorizaciones.py): uno a uno, con caducidad y solo mientras dure este proceso.
- Solo local: la conexión debe llegar desde loopback, con `Host` local y sin cabeceras de proxy.
  Un despliegue detrás de un proxy o con un dominio público lo rechaza aunque se active por error.
- Apagado (`DEMO_ADVISOR_MODE` distinto de `1`), sus rutas responden 404 como si no existieran.

La validación es la misma de siempre (`store.validar`): atómica, sin correcciones y con las mismas
reglas de estado. Esto no es autenticación de asesores reales: ver docs/modo-asesor-demo.md.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from . import acceso, demo_autorizaciones
from .perfil import revision, store, validacion

log = logging.getLogger("perfil.asesor_demo")

router = APIRouter(prefix="/api/demo/asesor", tags=["demo asesor"])
CLIENTES_POR_DEFECTO = "carmen-68,carmen-corta"
CANALES = {"voice", "text"}

CABECERA = "X-Demo-Advisor-Token"
IPS_LOCALES = frozenset({"127.0.0.1", "::1"})
HOSTS_LOCALES = frozenset({"localhost", "127.0.0.1", "::1"})
CABECERAS_PROXY = ("forwarded", "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "x-real-ip")
SECRETOS_DISTINTOS = ("ADMIN_TOKEN", "CLIENT_ACCESS_SECRET", "VOICE_USER_ID_SECRET")
MIN_BYTES_TOKEN = 32
MARCA_FICTICIO = "DATOS SIMULADOS"
_NOMBRE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Configuracion:
    token: bytes
    clientes: frozenset[str]
    asesor_id: str


def activado() -> bool:
    return os.getenv("DEMO_ADVISOR_MODE", "0").strip() == "1"


def _mal_configurado(motivo: str) -> HTTPException:
    return HTTPException(503, f"Modo asesor de demo mal configurado: {motivo}")


def es_cliente_ficticio(nombre: str) -> bool:
    """True si `nombre` es un fixture de DATOS SIMULADOS cuyo client_id coincide."""
    if not _NOMBRE.match(nombre):
        return False
    ruta = store.FIXTURES_DIR / f"{nombre}.json"
    if not ruta.is_file():
        return False
    try:
        datos = json.loads(ruta.read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return (isinstance(datos, dict) and datos.get("client_id") == nombre
            and str(datos.get("reason", "")).startswith(MARCA_FICTICIO))


def configuracion() -> Configuracion:
    token = os.getenv("DEMO_ADVISOR_TOKEN", "").strip()
    if len(token.encode()) < MIN_BYTES_TOKEN:
        raise _mal_configurado(f"DEMO_ADVISOR_TOKEN necesita al menos {MIN_BYTES_TOKEN} bytes")
    for nombre in SECRETOS_DISTINTOS:
        otro = os.getenv(nombre, "").strip()
        if otro and hmac.compare_digest(otro.encode(), token.encode()):
            raise _mal_configurado(f"DEMO_ADVISOR_TOKEN debe ser distinto de {nombre}")
    clientes = [c.strip() for c in os.getenv("DEMO_ADVISOR_CLIENTS", CLIENTES_POR_DEFECTO).split(",") if c.strip()]
    if not clientes:
        raise _mal_configurado("DEMO_ADVISOR_CLIENTS está vacío")
    no_ficticios = [c for c in clientes if not es_cliente_ficticio(c)]
    if no_ficticios:
        raise _mal_configurado(f"solo admite clientes ficticios de backend/fixtures; no lo son: {no_ficticios}")
    asesor = os.getenv("DEMO_ADVISOR_ID", "asesor-demo").strip()
    try:
        validacion.comprobar_autor(f"advisor:{asesor}")
    except validacion.DatoInvalido as e:
        raise _mal_configurado("DEMO_ADVISOR_ID no es válido") from e
    return Configuracion(token=token.encode(), clientes=frozenset(clientes), asesor_id=asesor)


def _hostname(host: str | None) -> str:
    try:
        return (urlsplit(f"//{host or ''}").hostname or "").lower()
    except ValueError:
        return ""


def es_peticion_local(request: Request) -> bool:
    ip = request.client.host if request.client else ""
    if ip.startswith("::ffff:"):
        ip = ip[len("::ffff:"):]
    if ip not in IPS_LOCALES:
        return False
    if _hostname(request.headers.get("host")) not in HOSTS_LOCALES:
        return False
    return not any(cabecera in request.headers for cabecera in CABECERAS_PROXY)


def exigir_asesor_demo(request: Request,
                       x_demo_advisor_token: str | None = Header(default=None)) -> Configuracion:
    """Orden: apagado (404) → no local (403) → mal configurado (503) → sin token válido (401)."""
    if not activado():
        raise HTTPException(404, "Not Found")
    if not es_peticion_local(request):
        raise HTTPException(403, "El modo asesor de demo solo funciona en local y sin proxy")
    conf = configuracion()
    if not x_demo_advisor_token or not hmac.compare_digest(x_demo_advisor_token.encode(), conf.token):
        raise HTTPException(401, "Autorización de asesor de demo ausente o no válida",
                            headers={"Cache-Control": "no-store"})
    return conf


def _cliente_permitido(client_id: str, conf: Configuracion) -> str:
    """Fixture ficticio de la lista o cliente nuevo con autorización vigente del operador."""
    if client_id not in conf.clientes and demo_autorizaciones.activa(client_id) is None:
        raise HTTPException(404, "Recurso no encontrado")
    return client_id


def clientes_permitidos(conf: Configuracion) -> list[str]:
    return sorted(conf.clientes | {a["client_id"] for a in demo_autorizaciones.listar()})


def _llamar(fn, *args):
    try:
        return fn(*args)
    except store.NoEncontrado as e:
        raise HTTPException(404, "Recurso no encontrado") from e
    except store.Conflicto as e:
        raise HTTPException(409, str(e)) from e
    except store.DatoInvalido as e:
        raise HTTPException(422, str(e)) from e


def _perfil_para_asesor(client_id: str) -> dict[str, Any]:
    # La capa personal no hace falta para validar: no se muestra en la vista de la entidad.
    return _llamar(store.perfil, client_id).model_copy(update={"personal": {}}).model_dump(mode="json")


@router.get("/estado")
def estado(conf: Configuracion = Depends(exigir_asesor_demo)) -> dict[str, Any]:
    return {"enabled": True, "simulated": True, "clients": clientes_permitidos(conf), "advisor_id": conf.asesor_id}


@router.get("/clientes/{client_id}")
def expediente(client_id: str, conf: Configuracion = Depends(exigir_asesor_demo)) -> dict[str, Any]:
    """Lo que ve el asesor: última versión, restricciones tal como las sirve el MCP e historial."""
    cid = _cliente_permitido(client_id, conf)
    return {"profile": _perfil_para_asesor(cid),
            "constraints": _llamar(store.restricciones_para_consumidor, cid).model_dump(mode="json"),
            "versions": [{**v, "created_at": v["created_at"].isoformat(), "status": v["status"].value}
                         for v in _llamar(store.versiones, cid)],
            "review": revision.vista(_llamar(revision.en_curso, cid)),
            "changes": (c.model_dump(mode="json") if (c := _llamar(revision.comparar, cid)) else None)}


@router.post("/clientes/{client_id}/validar")
def validar(client_id: str, conf: Configuracion = Depends(exigir_asesor_demo)) -> dict[str, Any]:
    """Validación atómica de siempre, sin correcciones, firmada por `advisor:<DEMO_ADVISOR_ID>`."""
    cid = _cliente_permitido(client_id, conf)
    _llamar(store.validar, cid, conf.asesor_id, [])
    log.warning("Modo asesor de demo: %s validado por advisor:%s (DATOS SIMULADOS)", cid, conf.asesor_id)
    return _perfil_para_asesor(cid)


@router.post("/clientes/{client_id}/reiniciar")
def reiniciar(client_id: str, conf: Configuracion = Depends(exigir_asesor_demo)) -> dict[str, Any]:
    """Vuelve a cargar el fixture como versión nueva, para repetir el ensayo. No borra el historial.
    Solo fixtures: un cliente nuevo no tiene fixture que recargar."""
    if client_id not in conf.clientes:
        raise HTTPException(404, "Recurso no encontrado")
    cid = client_id
    _llamar(store.cargar_fixture, cid)
    return _perfil_para_asesor(cid)


@router.post("/clientes/{client_id}/entrevista")
def entrevista_corta(client_id: str, channel: str = "voice",
                     conf: Configuracion = Depends(exigir_asesor_demo)) -> dict[str, Any]:
    """Entrevista corta en directo para el pitch, sobre un fixture ficticio casi completo.

    Recarga el fixture (versión nueva, sin borrar historial), abre una sesión y emite la credencial de
    cliente de ESE fixture para que el navegador pueda hablar o escribir. Mismas guardas que el resto del
    modo asesor: apagado por defecto, solo local, `X-Demo-Advisor-Token` y solo fixtures de la lista.
    """
    if client_id not in conf.clientes:
        raise HTTPException(404, "Recurso no encontrado")
    if channel not in CANALES:
        raise HTTPException(422, "channel debe ser voice o text")
    emitir = acceso.preparar_emision()  # falla antes de tocar el almacén si falta CLIENT_ACCESS_SECRET
    _llamar(store.cargar_fixture, client_id)
    sesion = _llamar(store.crear_sesion, client_id, channel)
    log.warning("Modo asesor de demo: entrevista corta de %s (DATOS SIMULADOS)", client_id)
    return {**sesion, "access_token": emitir(client_id)}


def avisar_si_activo() -> None:
    """Al arrancar: deja claro en el log que el modo está activo, o por qué no funcionará."""
    if not activado():
        return
    try:
        conf = configuracion()
    except HTTPException as e:
        log.error("DEMO_ADVISOR_MODE=1 pero %s", e.detail)
        return
    log.warning("MODO ASESOR DE DEMO ACTIVO: solo local y para %s (DATOS SIMULADOS). "
                "Desactívalo fuera de la presentación.", ", ".join(sorted(conf.clientes)))
