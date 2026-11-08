"""Almacén de perfiles versionados (contrato 04). Fachada pública del perfil.

La API pública es la de la PR #7 y la usan el front (vía main.py), los agentes y el MCP:
    perfil, perfil_para_consumidor, versiones, crear, aplicar, anadir_alertas, validar,
    crear_sesion, sesion, anadir_turno, cargar_fixture, reiniciar, NoEncontrado, Conflicto
Se añaden: DatoInvalido, comprobar_parche, guardar_personal, personal, borrar_personal,
asegurar_fixture, configurar, tipo_almacen y bus (eventos para el SSE).

Dónde se guarda lo decide `PERFIL_ALMACEN=memoria|bd` (por defecto memoria; ver almacenes/).
El algoritmo de escritura está aquí una sola vez, así que ambos almacenes se comportan igual:
  1. leer la versión vigente y copiarla (nunca se modifica una versión guardada);
  2. validar la entrada (validacion.py) y aplicar el cambio;
  3. recalcular con calculos.py (la lógica financiera de la PR #7, sin cambios) y decidir el estado;
  4. insertar la versión nueva; si otra escritura se adelantó, releer y reintentar;
  5. publicar los eventos para el panel en vivo.

Estados (docs/proyecto/04_CONTRATO_PERFIL.md):
  draft → pending_validation   cuando suitability.complete y sin alertas needs_advisor abiertas
  pending_validation → active  cuando valida la entidad (solo desde draft o pending_validation)
  active → review_due          cuando un agente cambia un dato (o un evento vital)
  review_due → draft           al empezar una entrevista nueva

La capa personal se guarda aparte (personal.py) y se une al perfil al leerlo.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from . import calculos, validacion
from .almacenes import Almacen, ConflictoVersion, crear_almacen
from .eventos import BusEventos, Evento
from .modelos import (
    CALCULADOS,
    Alerta,
    EstadoAlerta,
    EstadoPerfil,
    Fact,
    Flag,
    Fuente,
    Parche,
    Perfil,
    Revision,
    Turno,
    ahora,
)
from .personal import CapaPersonal, separar
from .validacion import DatoInvalido, EscrituraCalculada

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
AUTOR_FIXTURE = "fixture"
CANALES = ("voice", "text")
MAX_REINTENTOS = 5
DIAS_HASTA_REVISION = 365
_NOMBRE_FIXTURE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class NoEncontrado(KeyError):
    pass


class Conflicto(ValueError):
    pass


__all__ = [
    "NoEncontrado", "Conflicto", "DatoInvalido", "bus", "configurar", "tipo_almacen",
    "perfil", "perfil_para_consumidor", "versiones", "crear", "comprobar_parche", "aplicar",
    "anadir_alertas", "validar", "crear_sesion", "sesion", "anadir_turno", "cargar_fixture",
    "asegurar_fixture", "guardar_personal", "personal", "borrar_personal", "reiniciar",
]


class _SinCambios(Exception):
    """La operación no cambia nada: no se crea versión."""


# ---------- configuración ----------

_almacen: Almacen | None = None
_conf = threading.Lock()
_candados: dict[str, threading.RLock] = {}
bus = BusEventos()


def configurar(tipo: str | None = None, url: str | None = None) -> Almacen:
    """Elige el almacén. Sin argumentos usa PERFIL_ALMACEN (y DATABASE_URL si es 'bd')."""
    global _almacen
    nuevo = crear_almacen(tipo, url)
    with _conf:
        anterior, _almacen = _almacen, nuevo
        _candados.clear()
    if anterior is not None:
        anterior.cerrar()
    return nuevo


_inicio = threading.Lock()


def _a() -> Almacen:
    """Almacén configurado; la primera vez lo crea a partir de PERFIL_ALMACEN."""
    if _almacen is None:
        with _inicio:
            if _almacen is None:
                configurar()
    return _almacen  # type: ignore[return-value]


def tipo_almacen() -> str:
    return _a().tipo


def _candado(client_id: str) -> threading.RLock:
    with _conf:
        return _candados.setdefault(client_id, threading.RLock())


# ---------- lectura ----------

def _con_personal(p: Perfil) -> Perfil:
    capa = _a().ultima_personal(p.client_id)
    return p.model_copy(update={"personal": capa.exportar() if capa else {}})


def _ultima(client_id: str) -> Perfil:
    p = _a().ultima(client_id)
    if p is None:
        raise NoEncontrado(client_id)
    return p


def perfil(client_id: str, version: int | None = None) -> Perfil:
    """Última versión (cualquier estado) o una versión concreta. La usa el front."""
    if version is None:
        return _con_personal(_ultima(client_id))
    p = _a().version(client_id, version)
    if p is None:
        raise NoEncontrado(f"{client_id}@v{version}")
    return _con_personal(p)


def perfil_para_consumidor(client_id: str) -> Perfil:
    """Para el MCP y las restricciones: el activo más reciente; si no hay, el último (usable=false).

    Un reinicio de la demo (fixture) abre una época nueva: no se sirven perfiles activos anteriores.
    """
    ultima = _ultima(client_id)
    desde = _a().ultima_de_autor(client_id, AUTOR_FIXTURE) or 1
    activa = _a().ultima_activa(client_id, desde)
    return _con_personal(activa or ultima)


def versiones(client_id: str) -> list[dict[str, Any]]:
    h = _a().historial(client_id)
    if not h:
        raise NoEncontrado(client_id)
    return h


# ---------- núcleo de escritura ----------

def _estado_tras_cambio(p: Perfil, revisar_si_activo: bool) -> EstadoPerfil:
    """Reglas de la PR #7. `p` ya tiene sus resultados recalculados."""
    estado = p.status
    if estado == EstadoPerfil.active and revisar_si_activo:
        estado = EstadoPerfil.review_due
    necesita_asesor = any(a.status == EstadoAlerta.open and a.flag == Flag.needs_advisor for a in p.alerts)
    completo = p.assessments.suitability.complete
    if estado == EstadoPerfil.draft and completo and not necesita_asesor:
        return EstadoPerfil.pending_validation
    if estado == EstadoPerfil.pending_validation and (not completo or necesita_asesor):
        return EstadoPerfil.draft
    return estado


def _escribir(client_id: str, mutar: Callable[[Perfil], str], autor: str,
              estado: Callable[[Perfil], EstadoPerfil]) -> Perfil:
    with _candado(client_id):
        for _ in range(MAX_REINTENTOS):
            actual = _ultima(client_id)
            n = actual.model_copy(deep=True)
            n.version, n.created_at, n.author, n.personal = actual.version + 1, ahora(), autor, {}
            try:
                n.reason = mutar(n)
            except _SinCambios:
                return _con_personal(actual)
            calculos.recalcular(n)
            n.status = estado(n)
            try:
                _a().insertar(n)
            except ConflictoVersion:
                continue  # otra escritura (p. ej. de otro proceso) se adelantó: releer y reintentar
            _publicar(actual, n)
            return _con_personal(n)
    raise Conflicto(f"{client_id}: demasiadas escrituras simultáneas, inténtalo de nuevo")


def _fact(p: Parche, autor: str, momento) -> Fact:
    return Fact(value=p.value, declared=p.declared, source=p.source, confidence=p.confidence,
                confidence_basis=p.confidence_basis, evidence=p.evidence, flags=p.flags,
                updated_at=momento, updated_by=autor)


def _iguales(a: Fact, b: Fact) -> bool:
    excluir = {"updated_at", "updated_by"}
    return a.model_dump(exclude=excluir) == b.model_dump(exclude=excluir)


def _motivo(motivo: str) -> str:
    if not isinstance(motivo, str) or not motivo.strip() or len(motivo) > 200:
        raise DatoInvalido("El motivo de la versión es obligatorio (máx. 200 caracteres)")
    return motivo.strip()


# ---------- escritura ----------

def crear(client_id: str | None = None) -> Perfil:
    cid = validacion.comprobar_client_id(client_id) if client_id else f"cliente-{uuid.uuid4().hex[:12]}"
    if (existente := _a().ultima(cid)) is not None:
        return _con_personal(existente)
    p = Perfil(client_id=cid, created_at=ahora())
    calculos.recalcular(p)
    p.status = _estado_tras_cambio(p, revisar_si_activo=False)
    if _a().crear(p):
        _publicar(None, p)
        return _con_personal(p)
    return perfil(cid)  # otra petición lo creó a la vez


def comprobar_parche(parche: Parche, autor: str) -> Parche:
    """Valida un parche sin escribirlo (p. ej. para descartar uno inválido del extractor)."""
    try:
        return validacion.comprobar_parche(parche, autor)
    except EscrituraCalculada as e:
        raise Conflicto(str(e)) from e


def aplicar(client_id: str, parches: Iterable[Parche], motivo: str, autor: str) -> Perfil:
    """Escribe datos. `autor`: "agent:extractor", "agent:verifier" o "advisor:<id>".
    Si un parche no es válido no se escribe ninguno. Reescribir lo mismo no crea versión."""
    validacion.comprobar_autor(autor)
    motivo = _motivo(motivo)
    normalizados = [comprobar_parche(p, autor) for p in parches]

    def mutar(n: Perfil) -> str:
        cambiado = False
        for c in normalizados:
            previo = n.mifid.get(c.path)
            if c.value is None:
                cambiado |= n.mifid.pop(c.path, None) is not None
                continue
            nuevo = _fact(c, autor, n.created_at)
            if previo is None or not _iguales(previo, nuevo):
                n.mifid[c.path] = nuevo
                cambiado = True
        if not cambiado:
            raise _SinCambios
        return motivo

    revisar = not autor.startswith("advisor:")
    return _escribir(client_id, mutar, autor, lambda n: _estado_tras_cambio(n, revisar_si_activo=revisar))


def anadir_alertas(client_id: str, alertas: Iterable[Alerta], autor: str = "agent:verifier") -> Perfil:
    """Añade alertas; ignora las que ya están abiertas para el mismo flag y dato."""
    validacion.comprobar_autor(autor)
    alertas = [validacion.comprobar_alerta(a) for a in alertas]

    def mutar(n: Perfil) -> str:
        abiertas = {(a.flag, a.path) for a in n.alerts if a.status == EstadoAlerta.open}
        ids = {a.id for a in n.alerts}
        nuevas = []
        for a in alertas:
            if (a.flag, a.path) in abiertas or a.id in ids:
                continue
            nuevas.append(a.model_copy(update={"status": EstadoAlerta.open, "created_by": a.created_by or autor}))
            abiertas.add((a.flag, a.path))
            ids.add(a.id)
            if a.path in n.mifid and a.flag not in n.mifid[a.path].flags:
                n.mifid[a.path].flags.append(a.flag)
        if not nuevas:
            raise _SinCambios
        n.alerts.extend(nuevas)
        return f"{len(nuevas)} alerta(s)"

    return _escribir(client_id, mutar, autor, lambda n: _estado_tras_cambio(n, revisar_si_activo=False))


def validar(client_id: str, asesor_id: str, cambios: Iterable[Parche] = ()) -> Perfil:
    """La entidad corrige (opcional) y valida: el perfil pasa a 'active'.
    Solo desde draft o pending_validation (desde review_due hay que reentrevistar)."""
    autor = validacion.comprobar_autor(f"advisor:{asesor_id}")
    actual = _ultima(client_id)
    if actual.status not in (EstadoPerfil.draft, EstadoPerfil.pending_validation):
        raise Conflicto(f"No se puede validar un perfil en estado '{actual.status.value}'")
    cambios = [c.model_copy(update={"source": Fuente.advisor}) for c in cambios]  # sin tocar la entrada
    if cambios:
        aplicar(client_id, cambios, "advisor_correction", autor)

    def mutar(n: Perfil) -> str:
        # Regla de la PR #7: la revisión humana cierra las alertas abiertas. Queda registrado quién y cuándo.
        n.alerts = [a.model_copy(update={"status": EstadoAlerta.resolved, "resolved_by": autor,
                                         "resolved_at": n.created_at})
                    if a.status == EstadoAlerta.open else a for a in n.alerts]
        n.review = Revision(validated_by=asesor_id, validated_at=n.created_at,
                            next_review=(n.created_at + timedelta(days=DIAS_HASTA_REVISION)).date().isoformat())
        return "validated"

    def estado(n: Perfil) -> EstadoPerfil:
        if n.status not in (EstadoPerfil.draft, EstadoPerfil.pending_validation):
            raise Conflicto(f"No se puede validar un perfil en estado '{n.status.value}'")
        if not n.assessments.suitability.complete:
            raise Conflicto(f"Faltan datos obligatorios: {', '.join(n.assessments.suitability.missing)}")
        return EstadoPerfil.active

    return _escribir(client_id, mutar, autor, estado)


# ---------- capa personal ----------

def personal(client_id: str) -> CapaPersonal | None:
    _ultima(client_id)
    return _a().ultima_personal(client_id)


def guardar_personal(client_id: str, datos: dict[str, Any], consentimiento: bool, autor: str) -> CapaPersonal:
    """Guarda una versión nueva de la capa personal. Sin consentimiento no admite datos."""
    validacion.comprobar_autor(autor)
    _ultima(client_id)
    with _candado(client_id):
        previa = _a().ultima_personal(client_id)
        momento = ahora()
        consentido_en = None
        if consentimiento:
            consentido_en = previa.consent_at if previa and previa.consent_given else momento
        try:
            capa = CapaPersonal(client_id=client_id, version=(previa.version + 1) if previa else 1,
                                consent_given=consentimiento, consent_at=consentido_en,
                                data=datos, author=autor, created_at=momento)
        except ValidationError as e:
            raise DatoInvalido(f"Capa personal no válida: {e.errors()[0]['msg']}") from e
        _a().insertar_personal(capa)
        return capa


def borrar_personal(client_id: str) -> int:
    """Derecho de supresión: borra la capa personal. El registro MiFID no se toca."""
    _ultima(client_id)
    return _a().borrar_personal(client_id)


# ---------- sesiones ----------

def crear_sesion(client_id: str | None = None, channel: str = "voice") -> dict:
    if channel not in CANALES:
        raise DatoInvalido(f"Canal {channel!r} no válido: {list(CANALES)}")
    p = crear(client_id)
    if p.status == EstadoPerfil.review_due:
        _escribir(p.client_id, lambda n: "reassessment_started", "system", lambda n: EstadoPerfil.draft)
    sid, momento = f"s-{uuid.uuid4().hex[:12]}", ahora()
    _a().crear_sesion(sid, p.client_id, channel, momento)
    return {"session_id": sid, "client_id": p.client_id, "started_at": momento, "channel": channel}


def sesion(session_id: str) -> dict:
    s = _a().sesion(session_id)
    if s is None:
        raise NoEncontrado(session_id)
    return {**s, "turns": _a().turnos(session_id)}


def anadir_turno(session_id: str, turno: Turno) -> Turno:
    """Guarda un turno. Con el mismo turn_id no se duplica. Sin turn_id se asigna t-001, t-002…"""
    s = _a().sesion(session_id)
    if s is None:
        raise NoEncontrado(session_id)
    if s.get("ended_at") is not None:
        raise Conflicto(f"La sesión {session_id} ya terminó")
    guardado, _nuevo = _a().insertar_turno(session_id, turno, ahora())
    return guardado


# ---------- fixtures (DATOS SIMULADOS) ----------

def _leer_fixture(nombre: str) -> tuple[Perfil, list[Parche], dict | None]:
    if not _NOMBRE_FIXTURE.match(nombre or ""):
        raise DatoInvalido(f"Nombre de fixture no válido: {nombre!r}")
    ruta = FIXTURES_DIR / f"{nombre}.json"
    if not ruta.is_file():
        raise NoEncontrado(f"fixture {nombre}")
    datos = json.loads(ruta.read_text("utf-8"))
    personal_fixture = datos.pop("personal", None)
    plantilla = Perfil.model_validate(datos)
    validacion.comprobar_client_id(plantilla.client_id)
    parches = [
        comprobar_parche(Parche(path=r, value=f.value, source=f.source, declared=f.declared,
                                confidence=f.confidence, confidence_basis=f.confidence_basis,
                                evidence=f.evidence, flags=f.flags), AUTOR_FIXTURE)
        for r, f in plantilla.mifid.items() if r not in CALCULADOS
    ]
    for a in plantilla.alerts:
        validacion.comprobar_alerta(a)
    return plantilla, parches, personal_fixture


def cargar_fixture(nombre: str) -> Perfil:
    """Carga un perfil de ejemplo. Si el cliente ya existe, es un reinicio de demo: se añade una versión
    nueva (nunca se borra el historial) y el consumidor deja de servir perfiles activos anteriores."""
    plantilla, parches, personal_fixture = _leer_fixture(nombre)
    cid = plantilla.client_id

    def mutar(n: Perfil) -> str:
        n.mifid = {c.path: _fact(c, AUTOR_FIXTURE, n.created_at) for c in parches if c.value is not None}
        n.alerts = [a.model_copy(update={"created_by": a.created_by or AUTOR_FIXTURE}) for a in plantilla.alerts]
        n.review = Revision()
        n.status = EstadoPerfil.draft  # reinicio de demo: fuera del flujo normal, queda en el historial
        return plantilla.reason if n.version == 1 else f"demo_reset: {plantilla.reason}"

    with _candado(cid):
        if _a().ultima(cid) is None:
            p = Perfil(client_id=cid, version=1, created_at=ahora(), author=AUTOR_FIXTURE)
            p.reason = mutar(p)
            calculos.recalcular(p)
            p.status = _estado_tras_cambio(p, revisar_si_activo=False)
            if _a().crear(p):
                _publicar(None, p)
            else:  # pragma: no cover - carrera con otra carga
                _escribir(cid, mutar, AUTOR_FIXTURE, lambda n: _estado_tras_cambio(n, False))
        else:
            _escribir(cid, mutar, AUTOR_FIXTURE, lambda n: _estado_tras_cambio(n, False))
        _a().borrar_personal(cid)
        if personal_fixture:
            consentimiento, datos = separar(personal_fixture)
            guardar_personal(cid, datos, consentimiento, AUTOR_FIXTURE)
    return perfil(cid)


def asegurar_fixture(nombre: str) -> Perfil:
    """Carga el fixture solo si el cliente no existe (arranque del backend sin pisar datos guardados)."""
    plantilla, _, _ = _leer_fixture(nombre)
    if _a().ultima(plantilla.client_id) is None:
        return cargar_fixture(nombre)
    return perfil(plantilla.client_id)


def reiniciar() -> None:
    """Solo para tests."""
    _a().reiniciar()
    with _conf:
        _candados.clear()


# ---------- eventos para el panel en vivo ----------

def _publicar(anterior: Perfil | None, nueva: Perfil) -> None:
    cid, v = nueva.client_id, nueva.version
    previos = anterior.mifid if anterior else {}
    for r in sorted(set(previos) | set(nueva.mifid)):
        antes, dato = previos.get(r), nueva.mifid.get(r)
        # calculos.recalcular rehace los calculados con fecha nueva: solo cuenta si cambia el contenido.
        if antes is None or dato is None or not _iguales(antes, dato):
            bus.publicar(Evento("profile.patch", cid, v, {"path": r, "fact": dato.model_dump(mode="json") if dato else None}))
    ids_previos = {a.id for a in anterior.alerts} if anterior else set()
    for a in nueva.alerts:
        if a.id not in ids_previos:
            bus.publicar(Evento("flag.raised", cid, v, {"path": a.path, "flag": a.flag.value,
                                                         "message": a.message, "alert_id": a.id}))
    s = nueva.assessments.suitability
    bus.publicar(Evento("profile.status", cid, v, {"status": nueva.status.value,
                                                    "complete": s.complete, "missing": s.missing}))
