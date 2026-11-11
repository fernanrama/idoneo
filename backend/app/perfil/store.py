"""Almacén de perfiles versionados (contrato 04). Fachada pública del perfil.

La API pública es la de la PR #7 y la usan el front (vía main.py), los agentes y el MCP:
    perfil, perfil_para_consumidor, versiones, crear, aplicar, anadir_alertas, validar,
    crear_sesion, sesion, anadir_turno, cargar_fixture, reiniciar, NoEncontrado, Conflicto
Se añaden: DatoInvalido, comprobar_parche, guardar_personal, personal, borrar_personal,
asegurar_fixture, configurar, tipo_almacen y bus (eventos para el SSE).
Y revision_pendiente y restricciones_para_consumidor (`pending_review`, §4.6 del diseño 06).

Dónde se guarda lo decide `PERFIL_ALMACEN=memoria|bd` (por defecto memoria; ver almacenes/).
El algoritmo de escritura está aquí una sola vez, así que ambos almacenes se comportan igual:
  1. leer la versión vigente y copiarla (nunca se modifica una versión guardada);
  2. validar la entrada (validacion.py) y aplicar el cambio;
  3. recalcular con calculos.py (la lógica financiera de la PR #7, sin cambios) y decidir el estado;
  4. insertar la versión nueva; si otra escritura se adelantó, releer y reintentar;
  5. publicar los eventos para el panel en vivo.

Estados (docs/diseno/03-contrato-perfil.md):
  draft → pending_validation   cuando suitability.complete y sin alertas needs_advisor abiertas
  pending_validation → active  cuando valida la entidad (solo desde draft o pending_validation)
  active → review_due          cuando un agente cambia un dato (no por una confirmación pura, D3)
  review_due → active          cuando valida la entidad (D2), sin otra entrevista
  review_due → draft           al empezar una entrevista nueva
  (abrir una revisión del cliente no cambia el estado: pedir_revision)

La capa personal se guarda aparte (personal.py) y se une al perfil al leerlo.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from collections import deque
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, ValidationError

from . import alcance, calculos, personal as personal_mod, validacion
from .almacenes import Almacen, ConflictoVersion, crear_almacen
from .almacenes.base import AudioSesion, TransaccionPersonal
from .eventos import BusEventos, Evento
from .modelos import (
    CALCULADOS,
    Alerta,
    EstadoAlerta,
    EstadoPerfil,
    Evidencia,
    Fact,
    Flag,
    Fuente,
    Parche,
    Perfil,
    Restricciones,
    Revision,
    RevisionPendiente,
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


class PrecondicionRequerida(Conflicto):
    """Una escritura pública necesita la revisión personal que vio el cliente."""


class RevisionObsoleta(Conflicto):
    """La capa cambió; el llamador debe revisar y confirmar de nuevo su intención."""


__all__ = [
    "NoEncontrado", "Conflicto", "DatoInvalido", "PrecondicionRequerida", "RevisionObsoleta",
    "bus", "configurar", "tipo_almacen", "crear_nuevo", "borrar_personal_interno", "revocar_personal",
    "perfil", "perfil_para_consumidor", "versiones", "crear", "comprobar_parche", "aplicar",
    "anadir_alertas", "validar", "crear_sesion", "sesion", "anadir_turno", "cargar_fixture",
    "asegurar_fixture", "guardar_personal", "actualizar_personal", "personal", "borrar_personal",
    "finalizar_sesion", "reiniciar",
    "Rechazo", "separar_parches", "separar_alertas", "registrar_rechazo", "rechazos",
]

log = logging.getLogger("perfil.store")


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


def revision_pendiente(client_id: str, servido: Perfil | None = None) -> RevisionPendiente | None:
    """Qué ha cambiado desde el perfil que se sirve a los consumidores (§4.6 del diseño 06, opción B).

    Solo si se sirve un `active` y hay versiones posteriores con datos cambiados (`alcance.cambiados`: valor,
    declarado o flags; una confirmación no cuenta) o alertas nuevas abiertas. Los calculados no cuentan:
    cambian porque cambian sus entradas, que ya aparecen. Determinista; no escribe nada.
    """
    with _candado(client_id):
        servido = servido or perfil_para_consumidor(client_id)
        ultima = _ultima(client_id)
        if servido.status != EstadoPerfil.active or ultima.version <= servido.version:
            return None
        rutas = set(alcance.cambiados(servido, ultima))
        previas = {a.id for a in servido.alerts}
        rutas |= {a.path for a in ultima.alerts
                  if a.path and a.status == EstadoAlerta.open and a.id not in previas}
        if not rutas:
            return None
        siguiente = _a().version(client_id, servido.version + 1)
        return RevisionPendiente(
            since_version=servido.version + 1, latest_version=ultima.version, latest_status=ultima.status,
            paths=alcance.orden_guion(rutas),
            opened_at=(siguiente or ultima).created_at, material=alcance.es_material(servido, ultima))


def restricciones_para_consumidor(client_id: str) -> Restricciones:
    """Restricciones del perfil servido (último `active`) con lo que está en revisión (`pending_review`).

    Es lo que reciben la API, el MCP y el panel del asesor: todos ven lo mismo.
    """
    with _candado(client_id):
        servido = perfil_para_consumidor(client_id)
        r = calculos.restricciones(servido)
        r.pending_review = pendiente = revision_pendiente(client_id, servido)
        if pendiente is not None:  # R6: no presentarlas como inequívocamente vigentes
            efecto = (f" El cambio afecta a: {', '.join(pendiente.material)}." if pendiente.material
                      else " El cambio no altera estas restricciones según las reglas actuales.")
            r.rationale.append(
                f"Datos en revisión sin validar (versión {pendiente.latest_version}): {', '.join(pendiente.paths)}. "
                f"Estas restricciones son las de la versión {servido.version} validada y pueden estar "
                f"desactualizadas: no apoyar ninguna recomendación en esos datos.{efecto}")
        return r


def pedir_revision(client_id: str, motivo: str) -> Perfil:
    """Abre (o amplía) una revisión pedida por el cliente SIN cambiar el estado MiFID (R1, R5).

    Escribe una versión de trámite (`review_requested:<motivos>`) con los mismos datos y el mismo estado que
    la vigente: un perfil `active` sigue `active` y uno en revisión sigue en revisión. Es necesaria para la
    trazabilidad y para que la revisión abierta sobreviva a un reinicio y la vea la entidad sin una tabla
    nueva (`revision.en_curso` la reconstruye del historial). Abandonarla no cambia nada. Lo que el cliente
    cambie después pasa a `review_due` por la regla de siempre; lo que solo confirme no (D3)."""
    motivo = _motivo(motivo)
    return _escribir(client_id, lambda n: motivo, "system", lambda n: n.status)


def cerrar_revision(client_id: str, motivo: str, version_esperada: int) -> Perfil:
    """Cierra la revisión del cliente: versión de trámite `review_closed:<resultado>` sin tocar datos ni estado.

    Finalizar la sesión del inversor no es validar el perfil: un `active` sigue `active` y un `review_due`
    sigue esperando a la entidad. `version_esperada` es la versión sobre la que se decidió cerrar (sin
    preguntas pendientes): si otra escritura se adelanta (p. ej. otra respuesta), Conflicto y no se escribe.
    """
    motivo = _motivo(motivo)

    def mutar(n: Perfil) -> str:
        if n.version - 1 != version_esperada:  # n es la candidata: la vigente es la anterior
            raise Conflicto(f"La revisión ha cambiado desde la versión {version_esperada}: vuelve a intentarlo")
        return motivo

    return _escribir(client_id, mutar, "system", lambda n: n.status)


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


def _preparar_version(actual: Perfil, mutar: Callable[[Perfil], str], autor: str,
                      estado: Callable[[Perfil], EstadoPerfil]) -> Perfil:
    """Construye un candidato sin guardar ni publicar eventos."""
    n = actual.model_copy(deep=True)
    n.version, n.created_at, n.author, n.personal = actual.version + 1, ahora(), autor, {}
    n.reason = mutar(n)
    calculos.recalcular(n)
    n.status = estado(n)
    return n


def _escribir(client_id: str, mutar: Callable[[Perfil], str], autor: str,
              estado: Callable[[Perfil], EstadoPerfil]) -> Perfil:
    with _candado(client_id):
        for _ in range(MAX_REINTENTOS):
            actual = _ultima(client_id)
            try:
                n = _preparar_version(actual, mutar, autor, estado)
            except _SinCambios:
                return _con_personal(actual)
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


def crear_nuevo(client_id: str) -> Perfil:
    """Alta exclusiva: nunca permite acreditar la posesión de un cliente ya existente."""
    cid = validacion.comprobar_client_id(client_id)
    p = Perfil(client_id=cid, created_at=ahora())
    calculos.recalcular(p)
    p.status = _estado_tras_cambio(p, revisar_si_activo=False)
    if not _a().crear(p):
        raise Conflicto("El cliente ya existe")
    _publicar(None, p)
    return _con_personal(p)


def comprobar_parche(parche: Parche, autor: str) -> Parche:
    """Valida un parche sin escribirlo (p. ej. para descartar uno inválido del extractor)."""
    try:
        return validacion.comprobar_parche(parche, autor)
    except EscrituraCalculada as e:
        raise Conflicto(str(e)) from e


def _es_confirmacion(previo: Fact, nuevo: Fact) -> bool:
    """D1: mismo valor, mismo declarado y misma fuente, aunque cambie la confianza de la extracción."""
    return (previo.value, previo.declared, previo.source) == (nuevo.value, nuevo.declared, nuevo.source)


def _clave_cita(e: Evidencia) -> tuple:
    """Una cita ya guardada: mismo turno de la misma sesión (o, sin turno, la misma cita exacta)."""
    return (e.session_id, e.turn_id) if e.turn_id else (e.session_id, e.t, e.quote)


def _confirmar(previo: Fact, nuevo: Fact, momento, autor: str) -> Fact | None:
    """Une una confirmación con el dato guardado. None si no aporta nada (p. ej. reprocesar una cita).

    - Evidencia: se conserva la anterior y se añaden las citas nuevas (sin duplicar turnos).
    - Confianza: la más alta, con su base (la del dato guardado si empatan o la nueva no consta).
    - Flags: los que trae la escritura nueva (el extractor limpia, p. ej., una duda tras una repregunta).
      Si cambian, NO es una confirmación pura: aplicar() lo tratará como cambio para el estado.
    - `confirmed_at`/`confirmed_by` solo si hay una cita nueva. `value` y `updated_at` no cambian.
    """
    guardadas = {_clave_cita(e) for e in previo.evidence}
    nuevas = [e for e in nuevo.evidence if _clave_cita(e) not in guardadas]
    cambian_flags = set(nuevo.flags) != set(previo.flags)
    if not nuevas and not cambian_flags:
        return None
    sube = nuevo.confidence is not None and (previo.confidence is None or nuevo.confidence > previo.confidence)
    cambios: dict[str, Any] = {"evidence": [*previo.evidence, *nuevas], "flags": list(nuevo.flags)}
    if sube:
        cambios.update(confidence=nuevo.confidence, confidence_basis=nuevo.confidence_basis)
    if nuevas:
        cambios.update(confirmed_at=momento, confirmed_by=autor)
    return previo.model_copy(update=cambios)


def _aplicar_parches(n: Perfil, normalizados: list[Parche], motivo: str, autor: str) -> str:
    """Misma mutación para aplicar() y para los candidatos de validar().

    Confirmar (mismo valor, declarado y fuente con una cita nueva) acumula la evidencia y anota
    `confirmed_at`, sin cambiar el valor ni `updated_at` (`_confirmar`). Un cambio de valor, declarado o
    fuente sustituye el dato, como siempre. Reescribir lo mismo o reprocesar una cita no crea versión.
    """
    cambiado = False
    for c in normalizados:
        previo = n.mifid.get(c.path)
        if c.value is None:
            cambiado |= n.mifid.pop(c.path, None) is not None
            continue
        nuevo = _fact(c, autor, n.created_at)
        if previo is not None and _iguales(previo, nuevo):
            continue
        if previo is not None and _es_confirmacion(previo, nuevo):
            unido = _confirmar(previo, nuevo, n.created_at, autor)
            if unido is None:
                continue
            n.mifid[c.path] = unido
        else:
            n.mifid[c.path] = nuevo
        cambiado = True
    if not cambiado:
        raise _SinCambios
    return motivo


def aplicar(client_id: str, parches: Iterable[Parche], motivo: str, autor: str) -> Perfil:
    """Escribe datos. `autor`: "agent:extractor", "agent:verifier" o "advisor:<id>".
    Si un parche no es válido no se escribe ninguno. Reescribir lo mismo no crea versión."""
    validacion.comprobar_autor(autor)
    motivo = _motivo(motivo)
    normalizados = [comprobar_parche(p, autor) for p in parches]
    revisar = not autor.startswith("advisor:")
    antes: dict[str, Perfil] = {}

    def mutar(n: Perfil) -> str:
        antes["perfil"] = n.model_copy(deep=True)  # la versión vigente, ya calculada, antes de escribir
        return _aplicar_parches(n, normalizados, motivo, autor)

    def estado(n: Perfil) -> EstadoPerfil:
        if revisar and n.status == EstadoPerfil.active and _solo_confirmaciones(antes["perfil"], n):
            return EstadoPerfil.active  # D3: confirmación pura, versión de trazabilidad
        return _estado_tras_cambio(n, revisar_si_activo=revisar)

    return _escribir(client_id, mutar, autor, estado)


_RESTRICCIONES_VOLATILES = {"client_id", "profile_version", "status", "usable", "pending_review"}


def _solo_confirmaciones(antes: Perfil, despues: Perfil) -> bool:
    """D3: la escritura solo confirma datos y no cambia nada de lo que se usa para decidir.

    Se exige todo a la vez, comparando el perfil completo (no solo los parches):
    - cada dato MiFID es el mismo valor, declarado y fuente, con los mismos flags (solo cambian evidencia,
      confianza y fechas de confirmación);
    - los calculados, la idoneidad (incluido el perfil de riesgo), la conveniencia y las restricciones
      que se servirían son idénticos;
    - las alertas no cambian.
    Solo se llama sobre un perfil `active`: una confirmación nunca reactiva un perfil en revisión.
    """
    for ruta in set(antes.mifid) | set(despues.mifid):
        a, d = antes.mifid.get(ruta), despues.mifid.get(ruta)
        if a is None or d is None:
            return False
        if ruta in CALCULADOS:
            if a.value != d.value:
                return False
        elif not _es_confirmacion(a, d) or set(a.flags) != set(d.flags):
            return False
    if antes.assessments.model_dump() != despues.assessments.model_dump():
        return False
    if [(x.id, x.status) for x in antes.alerts] != [(x.id, x.status) for x in despues.alerts]:
        return False
    ra = calculos.restricciones(antes).model_dump(exclude=_RESTRICCIONES_VOLATILES)
    rd = calculos.restricciones(despues).model_dump(exclude=_RESTRICCIONES_VOLATILES)
    return ra == rd


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


VALIDABLES = (EstadoPerfil.draft, EstadoPerfil.pending_validation, EstadoPerfil.review_due)


def validar(client_id: str, asesor_id: str, cambios: Iterable[Parche] = (),
            version_esperada: int | None = None) -> Perfil:
    """La entidad corrige (opcional) y valida: el perfil pasa a 'active'.

    Desde draft, pending_validation o review_due (D2: tras una microentrevista, sin otra entrevista completa).
    Un perfil ya `active` no se valida otra vez. Correcciones y validación se guardan juntas, o ninguna.
    `version_esperada`: la versión que ha revisado la entidad; si el perfil ha cambiado desde entonces
    (p. ej. otra respuesta del extractor), se rechaza para no validar lo que nadie ha visto.
    """
    autor = validacion.comprobar_autor(f"advisor:{asesor_id}")

    def comprobar_estado(n: Perfil) -> None:
        if n.status not in VALIDABLES:
            raise Conflicto(f"No se puede validar un perfil en estado '{n.status.value}'")

    def comprobar_vigente(actual: Perfil) -> None:
        """Sobre la versión guardada (no sobre la candidata que se va a crear)."""
        comprobar_estado(actual)
        if version_esperada is not None and actual.version != version_esperada:
            raise Conflicto(f"El perfil ha cambiado desde la versión {version_esperada} que revisó la entidad "
                            f"(ahora es la {actual.version}): vuelve a revisarlo antes de validar")

    def mutar(n: Perfil) -> str:
        # Regla de la PR #7: la revisión humana cierra las alertas abiertas. Queda registrado quién y cuándo.
        n.alerts = [a.model_copy(update={"status": EstadoAlerta.resolved, "resolved_by": autor,
                                         "resolved_at": n.created_at})
                    if a.status == EstadoAlerta.open else a for a in n.alerts]
        n.review = Revision(validated_by=asesor_id, validated_at=n.created_at,
                            next_review=(n.created_at + timedelta(days=DIAS_HASTA_REVISION)).date().isoformat())
        return "validated"

    def estado(n: Perfil) -> EstadoPerfil:
        comprobar_estado(n)
        if not n.assessments.suitability.complete:
            raise Conflicto(f"Faltan datos obligatorios: {', '.join(n.assessments.suitability.missing)}")
        return EstadoPerfil.active

    with _candado(client_id):
        comprobar_vigente(_ultima(client_id))
        normalizados = [comprobar_parche(c.model_copy(update={"source": Fuente.advisor}), autor)
                        for c in cambios]  # no modifica los parches del llamante
        for _ in range(MAX_REINTENTOS):
            actual = _ultima(client_id)
            comprobar_vigente(actual)  # también la versión esperada: otra escritura pudo adelantarse
            candidatos = []
            if normalizados:
                try:
                    corregido = _preparar_version(
                        actual, lambda n: _aplicar_parches(n, normalizados, "advisor_correction", autor), autor,
                        lambda n: _estado_tras_cambio(n, revisar_si_activo=False))
                except _SinCambios:
                    pass
                else:
                    candidatos.append(corregido)
            validado = _preparar_version(candidatos[-1] if candidatos else actual, mutar, autor, estado)
            candidatos.append(validado)
            try:
                _a().insertar_lote(candidatos)
            except ConflictoVersion:
                continue  # releer y preparar de nuevo todo el lote, incluidas las reglas de estado
            anterior = actual
            for candidato in candidatos:
                _publicar(anterior, candidato)
                anterior = candidato
            return _con_personal(validado)
    raise Conflicto(f"{client_id}: demasiadas escrituras simultáneas, inténtalo de nuevo")


# ---------- capa personal ----------

def personal(client_id: str) -> CapaPersonal | None:
    _ultima(client_id)
    return _a().ultima_personal(client_id)


def guardar_personal(client_id: str, datos: dict[str, Any], consentimiento: bool, autor: str) -> CapaPersonal:
    """Escritura interna de confianza (fixtures). La API debe usar actualizar_personal con CAS."""
    validacion.comprobar_autor(autor)
    _ultima(client_id)
    datos = _datos_personales_nuevos(datos)
    return _operar_personal(client_id, lambda t: _guardar_capa(t, client_id, datos, consentimiento, autor))


def _datos_personales_nuevos(datos: dict[str, Any]) -> dict[str, Any]:
    try:
        return personal_mod.DatosPersonalesNuevos(data=datos).data
    except ValidationError as e:
        raise DatoInvalido(f"Capa personal no válida: {e.errors()[0]['msg']}") from e


_ResultadoPersonal = TypeVar("_ResultadoPersonal")


def _operar_personal(client_id: str, operacion: Callable[[TransaccionPersonal], _ResultadoPersonal]) -> _ResultadoPersonal:
    # Solo se repite tras rollback por bloqueo/serialización. La revisión esperada
    # permanece en la clausura y nunca se sustituye por una revisión más reciente.
    for _ in range(MAX_REINTENTOS):
        try:
            with _a().transaccion_personal(client_id) as transaccion:
                resultado = operacion(transaccion)
            return resultado
        except ConflictoVersion:
            continue
    raise Conflicto("No se pudo confirmar la escritura personal; inténtalo de nuevo")


def _guardar_capa(transaccion: TransaccionPersonal, client_id: str, datos: dict[str, Any],
                  consentimiento: bool, autor: str) -> CapaPersonal:
    previa = transaccion.ultima()
    if type(consentimiento) is not bool:
        raise DatoInvalido("El consentimiento debe ser explícito y booleano")
    momento = ahora()
    consentido_en = (previa.consent_at if previa and previa.consent_given else momento) if consentimiento else None
    try:
        capa = CapaPersonal(client_id=client_id, version=previa.version + 1 if previa else 1,
                            consent_given=consentimiento, consent_at=consentido_en,
                            data=datos, author=autor, created_at=momento)
    except ValidationError as e:
        raise DatoInvalido(f"Capa personal no válida: {e.errors()[0]['msg']}") from e
    if previa and previa.consent_given == capa.consent_given and previa.data == capa.data:
        return previa
    transaccion.insertar(capa)
    return capa


def _revision_esperada(version_esperada: int | None) -> int:
    if version_esperada is None:
        raise PrecondicionRequerida("Falta la revisión esperada de la memoria")
    if type(version_esperada) is not int or version_esperada < 0:
        raise DatoInvalido("La revisión personal debe ser un entero no negativo")
    return version_esperada


def _comprobar_revision(transaccion: TransaccionPersonal, esperada: int) -> CapaPersonal | None:
    capa = transaccion.ultima()
    if (capa.version if capa else 0) != esperada:
        raise RevisionObsoleta("La memoria ha cambiado; revisa la versión vigente antes de confirmar")
    return capa


def actualizar_personal(client_id: str, cambios: dict[str, Any], olvidar: Iterable[str], autor: str,
                        *, version_esperada: int | None = None, consentimiento: bool | None = None) -> CapaPersonal:
    """Mezcla bloques explícitos sobre la revisión vista, dentro de la misma transacción."""
    validacion.comprobar_autor(autor)
    _ultima(client_id)
    esperada = _revision_esperada(version_esperada)
    if consentimiento is not True:
        raise DatoInvalido("Guardar memoria requiere consentimiento explícito")
    cambios = _datos_personales_nuevos(cambios)
    olvidar = list(olvidar)
    if len(olvidar) > personal_mod.MAX_ELEMENTOS or not all(isinstance(k, str) for k in olvidar):
        raise DatoInvalido("Las claves a olvidar no son válidas")
    desconocidas = set(olvidar) - set(personal_mod.BLOQUES)
    if desconocidas:
        raise DatoInvalido(f"Bloques personales no previstos: {sorted(desconocidas)}")

    def actualizar(transaccion):
        previa = _comprobar_revision(transaccion, esperada)
        datos = dict(previa.data) if previa and previa.consent_given else {}
        for clave in olvidar:
            datos.pop(clave, None)
        datos.update(cambios)
        return _guardar_capa(transaccion, client_id, datos, consentimiento, autor)
    return _operar_personal(client_id, actualizar)


def _borrar_capa(transaccion: TransaccionPersonal, client_id: str, autor: str) -> int:
    previa = transaccion.ultima()
    if previa and not previa.consent_given and not previa.data and transaccion.cantidad() == 1:
        return 0  # revocación repetida: conserva revisión y metadatos originales
    n = transaccion.borrar()
    transaccion.insertar(CapaPersonal(client_id=client_id, version=previa.version + 1 if previa else 1,
                                     consent_given=False, data={}, author=autor, created_at=ahora()))
    return n


def revocar_personal(client_id: str, *, version_esperada: int | None = None,
                     autor: str = "agent:memory") -> tuple[int, CapaPersonal]:
    """Devuelve el contador y snapshot confirmado, sin releer posibles escrituras posteriores."""
    validacion.comprobar_autor(autor)
    _ultima(client_id)
    esperada = _revision_esperada(version_esperada)

    def borrar(transaccion):
        _comprobar_revision(transaccion, esperada)
        n = _borrar_capa(transaccion, client_id, autor)
        snapshot = transaccion.ultima()
        assert snapshot is not None  # el borrado siempre deja una revisión técnica
        return n, snapshot
    return _operar_personal(client_id, borrar)


def borrar_personal(client_id: str, *, version_esperada: int | None = None, autor: str = "agent:memory") -> int:
    """Suprime contenido e historial personal; conserva una revisión técnica vacía durable."""
    return revocar_personal(client_id, version_esperada=version_esperada, autor=autor)[0]


def borrar_personal_interno(client_id: str, autor: str = "system") -> int:
    """Revocación interna de confianza para fixtures; nunca usar desde una API pública."""
    validacion.comprobar_autor(autor)
    _ultima(client_id)
    return _operar_personal(client_id, lambda t: _borrar_capa(t, client_id, autor))


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


def finalizar_sesion(session_id: str, conversation_id: str) -> bool:
    """Vincula y cierra una sesión desde un webhook verificado; repetir el mismo evento es inocuo."""
    if not isinstance(conversation_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", conversation_id):
        raise DatoInvalido("conversation_id no válido")
    if _a().sesion(session_id) is None:
        raise NoEncontrado(session_id)
    try:
        return _a().finalizar_sesion(session_id, conversation_id, ahora())
    except ConflictoVersion as e:
        raise Conflicto(str(e)) from e


# ---------- audio de las sesiones de voz (pruebas de cada dato) ----------

def audio_disponible() -> bool:
    """False si la base de datos aún no tiene la tabla del audio (migración 0002 sin aplicar)."""
    return _a().audio_disponible()


def guardar_audio(registro: AudioSesion, datos: bytes) -> bool:
    """Guarda el audio de una sesión que ya terminó. Nunca lo sustituye: True solo la primera vez."""
    s = _a().sesion(registro.session_id)
    if s is None:
        raise NoEncontrado(registro.session_id)
    if s.get("conversation_id") not in (None, registro.conversation_id):
        raise Conflicto(f"La sesión {registro.session_id} pertenece a otra conversación")
    if not datos:
        raise DatoInvalido("Audio vacío")
    return _a().guardar_audio(registro, datos, ahora())


def audio(session_id: str) -> tuple[AudioSesion, bytes]:
    encontrado = _a().audio(session_id)
    if encontrado is None:
        raise NoEncontrado(f"audio de {session_id}")
    return encontrado


def info_audio(session_ids: Iterable[str]) -> dict[str, AudioSesion]:
    """Metadatos y tiempos del audio de varias sesiones (sin los bytes)."""
    return _a().info_audio(sorted(set(session_ids)))


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
        # No crear tombstone en una carga inicial que nunca tuvo capa personal.
        if _a().ultima_personal(cid) is not None:
            borrar_personal_interno(cid, AUTOR_FIXTURE)
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
    with _candado_rechazos:
        _rechazos.clear()


# ---------- aceptación parcial de lo que proponen los agentes ----------
# El extractor y el verificador pueden devolver elementos mal formados. Se valida cada uno por separado:
# los válidos se guardan y los inválidos se rechazan con su motivo, que queda registrado y visible.

class Rechazo(BaseModel):
    session_id: str | None = None
    client_id: str
    origen: Literal["extractor", "verificador", "backend"]
    tipo: Literal["parche", "alerta", "error"]  # error: el agente falló o devolvió algo inutilizable
    path: str | None = None
    motivo: str
    created_at: datetime = Field(default_factory=ahora)


MAX_RECHAZOS_POR_SESION = 200
_rechazos: dict[str, deque[Rechazo]] = {}
_candado_rechazos = threading.Lock()


def _motivo_de(e: Exception) -> str:
    texto = str(e).splitlines()[0] if str(e) else ""
    return (texto or type(e).__name__)[:300]


def separar_parches(elementos: Iterable[Any], autor: str) -> tuple[list[Parche], list[tuple[str | None, str]]]:
    """Valida cada elemento por separado. Devuelve (parches válidos, [(ruta, motivo)] rechazados).
    Mismas reglas que `aplicar` (esquema, tipos, autoría, evidencia): solo cambia que no es todo o nada."""
    validos: list[Parche] = []
    rechazados: list[tuple[str | None, str]] = []
    for elemento in elementos:
        ruta = elemento.get("path") if isinstance(elemento, dict) else getattr(elemento, "path", None)
        try:
            parche = elemento if isinstance(elemento, Parche) else Parche.model_validate(elemento)
            comprobar_parche(parche, autor)
        except ValidationError as e:
            rechazados.append((ruta if isinstance(ruta, str) else None,
                               f"no es un parche válido: {e.errors()[0]['msg']}"))
        except (DatoInvalido, Conflicto) as e:
            rechazados.append((ruta, _motivo_de(e)))
        else:
            validos.append(parche)
    return validos, rechazados


def separar_alertas(elementos: Iterable[Any]) -> tuple[list[Alerta], list[tuple[str | None, str]]]:
    """Valida cada alerta por separado. Devuelve (alertas válidas, [(ruta, motivo)] rechazadas)."""
    validas: list[Alerta] = []
    rechazadas: list[tuple[str | None, str]] = []
    for elemento in elementos:
        ruta = elemento.get("path") if isinstance(elemento, dict) else getattr(elemento, "path", None)
        try:
            alerta = elemento if isinstance(elemento, Alerta) else Alerta.model_validate(elemento)
            validacion.comprobar_alerta(alerta)
        except ValidationError as e:
            rechazadas.append((ruta if isinstance(ruta, str) else None,
                               f"no es una alerta válida: {e.errors()[0]['msg']}"))
        except DatoInvalido as e:
            rechazadas.append((ruta, _motivo_de(e)))
        else:
            validas.append(alerta)
    return validas, rechazadas


def registrar_rechazo(rechazo: Rechazo) -> Rechazo:
    """Deja el rechazo en el log, en la sesión (consultable por la API) y en el bus de eventos."""
    log.warning("Rechazado (%s/%s) %s: %s", rechazo.origen, rechazo.tipo, rechazo.path or "-", rechazo.motivo)
    if rechazo.session_id:
        with _candado_rechazos:
            _rechazos.setdefault(rechazo.session_id, deque(maxlen=MAX_RECHAZOS_POR_SESION)).append(rechazo)
    bus.publicar(Evento("item.rejected", rechazo.client_id, 0, rechazo.model_dump(mode="json")))
    return rechazo


def rechazos(session_id: str) -> list[Rechazo]:
    """Rechazos de una sesión, del más antiguo al más reciente. Se guardan en la memoria del proceso
    (los últimos 200 por sesión); no sobreviven a un reinicio del backend."""
    with _candado_rechazos:
        return list(_rechazos.get(session_id, ()))


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
