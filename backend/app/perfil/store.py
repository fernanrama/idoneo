"""Almacén de perfiles versionados (contrato v1). Solo añadir: cada cambio crea una versión.

v1: en memoria con volcado a JSON en DATA_DIR. Juan (rol A) puede pasarlo a SQLite con una tabla
`profile_versions(client_id, version, snapshot_json, reason, author, created_at)` sin cambiar estas funciones.

Estados (docs/proyecto/04_CONTRATO_PERFIL.md):
  draft → pending_validation   cuando suitability.complete y sin alertas needs_advisor abiertas
  pending_validation → active  cuando valida la entidad
  active → review_due          cuando un agente cambia un dato (o llega next_review / evento vital)
  review_due → draft           al empezar una entrevista nueva
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import date, timedelta
from pathlib import Path

from . import calculos
from .modelos import Alerta, EstadoAlerta, EstadoPerfil, Fact, Flag, Fuente, Parche, Perfil, Turno, ahora

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"

_lock = threading.RLock()
_versiones: dict[str, list[Perfil]] = {}  # client_id -> versiones; la última es la vigente
_sesiones: dict[str, dict] = {}            # session_id -> {client_id, started_at, turns}


class NoEncontrado(KeyError):
    pass


class Conflicto(ValueError):
    pass


# ---------- persistencia simple ----------

def _persistir() -> bool:
    return os.getenv("DATA_PERSIST", "1") == "1"


def _ruta(client_id: str) -> Path:
    return DATA_DIR / f"perfil_{client_id}.json"


def _guardar(client_id: str) -> None:
    if not _persistir():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    datos = [p.model_dump(mode="json") for p in _versiones[client_id]]
    _ruta(client_id).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _cargar(client_id: str) -> None:
    ruta = _ruta(client_id)
    if client_id not in _versiones and _persistir() and ruta.exists():
        _versiones[client_id] = [Perfil.model_validate(p) for p in json.loads(ruta.read_text("utf-8"))]


def cargar_fixture(nombre: str) -> Perfil:
    """Carga un perfil de ejemplo (p. ej. 'carmen-68') como historial nuevo."""
    p = Perfil.model_validate(json.loads((FIXTURES_DIR / f"{nombre}.json").read_text("utf-8")))
    _ajustar_estado(p)
    with _lock:
        _versiones[p.client_id] = [p]
        _guardar(p.client_id)
    return p


# ---------- lectura ----------

def _historial(client_id: str) -> list[Perfil]:
    _cargar(client_id)
    vs = _versiones.get(client_id)
    if not vs:
        raise NoEncontrado(client_id)
    return vs


def perfil(client_id: str, version: int | None = None) -> Perfil:
    """Última versión (cualquier estado) o una versión concreta. La usa el front."""
    with _lock:
        vs = _historial(client_id)
        if version is None:
            return vs[-1]
        for p in vs:
            if p.version == version:
                return p
        raise NoEncontrado(f"{client_id}@v{version}")


def perfil_para_consumidor(client_id: str) -> Perfil:
    """Para el MCP: el activo más reciente; si nunca hubo uno, el último (con usable=false)."""
    with _lock:
        vs = _historial(client_id)
        activos = [p for p in vs if p.status == EstadoPerfil.active]
        return activos[-1] if activos else vs[-1]


def versiones(client_id: str) -> list[dict]:
    with _lock:
        return [
            {"version": p.version, "created_at": p.created_at, "reason": p.reason, "author": p.author, "status": p.status}
            for p in _historial(client_id)
        ]


# ---------- escritura ----------

def _ajustar_estado(p: Perfil) -> None:
    calculos.recalcular(p)
    necesita_asesor = any(a.status == EstadoAlerta.open and a.flag == Flag.needs_advisor for a in p.alerts)
    completo = p.assessments.suitability.complete
    if p.status == EstadoPerfil.draft and completo and not necesita_asesor:
        p.status = EstadoPerfil.pending_validation
    elif p.status == EstadoPerfil.pending_validation and (not completo or necesita_asesor):
        p.status = EstadoPerfil.draft


def _nueva(client_id: str, motivo: str, autor: str) -> Perfil:
    actual = _historial(client_id)[-1]
    n = actual.model_copy(deep=True)
    n.version, n.created_at, n.reason, n.author = actual.version + 1, ahora(), motivo, autor
    return n


def _confirmar(client_id: str, p: Perfil) -> Perfil:
    _ajustar_estado(p)
    _versiones[client_id].append(p)
    _guardar(client_id)
    return p


def crear(client_id: str | None = None) -> Perfil:
    client_id = client_id or f"cliente-{uuid.uuid4().hex[:6]}"
    with _lock:
        _cargar(client_id)
        if client_id not in _versiones:
            p = Perfil(client_id=client_id)
            calculos.recalcular(p)
            _versiones[client_id] = [p]
            _guardar(client_id)
        return _versiones[client_id][-1]


def aplicar(client_id: str, parches: list[Parche], motivo: str, autor: str) -> Perfil:
    """Escribe datos. `autor`: "agent:extractor", "agent:verifier" o "advisor:<id>"."""
    with _lock:
        n = _nueva(client_id, motivo, autor)
        for c in parches:
            if calculos.es_calculado(c.path):
                raise Conflicto(f"{c.path} es calculado: no se escribe a mano")
            n.mifid[c.path] = Fact(
                value=c.value, declared=c.declared, source=c.source, confidence=c.confidence,
                confidence_basis=c.confidence_basis, evidence=c.evidence, flags=c.flags, updated_by=autor,
            )
        if n.status == EstadoPerfil.active and not autor.startswith("advisor:"):
            n.status = EstadoPerfil.review_due
        return _confirmar(client_id, n)


def anadir_alertas(client_id: str, alertas: list[Alerta], autor: str = "agent:verifier") -> Perfil:
    with _lock:
        n = _nueva(client_id, f"{len(alertas)} alerta(s)", autor)
        for a in alertas:
            n.alerts.append(a)
            if a.path in n.mifid and a.flag not in n.mifid[a.path].flags:
                n.mifid[a.path].flags.append(a.flag)
        return _confirmar(client_id, n)


def validar(client_id: str, asesor_id: str, cambios: list[Parche]) -> Perfil:
    """La entidad corrige (opcional) y valida: el perfil pasa a 'active'."""
    with _lock:
        if cambios:
            for c in cambios:
                c.source = Fuente.advisor
            aplicar(client_id, cambios, "advisor_correction", f"advisor:{asesor_id}")
        actual = perfil(client_id)
        if not actual.assessments.suitability.complete:
            raise Conflicto(f"Faltan datos obligatorios: {', '.join(actual.assessments.suitability.missing)}")
        n = _nueva(client_id, "validated", f"advisor:{asesor_id}")
        n.status = EstadoPerfil.active
        n.review.validated_by = asesor_id
        n.review.validated_at = ahora()
        n.review.next_review = (date.today() + timedelta(days=365)).isoformat()
        for a in n.alerts:  # la revisión humana cierra las alertas abiertas
            a.status = EstadoAlerta.resolved
        calculos.recalcular(n)
        _versiones[client_id].append(n)
        _guardar(client_id)
        return n


# ---------- sesiones de entrevista ----------

def crear_sesion(client_id: str | None = None) -> dict:
    p = crear(client_id)
    with _lock:
        if p.status == EstadoPerfil.review_due:
            n = _nueva(p.client_id, "reassessment_started", "system")
            n.status = EstadoPerfil.draft
            _confirmar(p.client_id, n)
        sid = f"s-{uuid.uuid4().hex[:8]}"
        _sesiones[sid] = {"session_id": sid, "client_id": p.client_id, "started_at": ahora(), "turns": []}
        return {k: v for k, v in _sesiones[sid].items() if k != "turns"}


def sesion(session_id: str) -> dict:
    if session_id not in _sesiones:
        raise NoEncontrado(session_id)
    return _sesiones[session_id]


def anadir_turno(session_id: str, turno: Turno) -> Turno:
    with _lock:
        s = sesion(session_id)
        if not turno.turn_id:
            turno.turn_id = f"t-{len(s['turns']) + 1:03d}"
        s["turns"].append(turno)
        return turno


def reiniciar() -> None:
    """Solo para tests."""
    with _lock:
        _versiones.clear()
        _sesiones.clear()
