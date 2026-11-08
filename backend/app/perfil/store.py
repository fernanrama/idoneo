"""Almacén de perfiles versionados. Nunca se sobrescribe: cada cambio crea una versión.

v0: en memoria con volcado a JSON en DATA_DIR (suficiente para la demo).
Dev A puede sustituirlo por SQLite/Postgres manteniendo estas funciones.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path

from . import calculos
from .modelos import (
    ActualizacionCampo,
    Alerta,
    Autor,
    Campo,
    EstadoPerfil,
    Fuente,
    Perfil,
    Turno,
    ahora,
)

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"

_lock = threading.Lock()
_versiones: dict[str, list[Perfil]] = {}         # client_id -> versiones, la última es la vigente
_sesiones: dict[str, dict] = {}                   # session_id -> {client_id, started_at, turns}


class NoEncontrado(KeyError):
    pass


# ---------- persistencia simple ----------

def _ruta(client_id: str) -> Path:
    return DATA_DIR / f"perfil_{client_id}.json"


def _guardar(client_id: str) -> None:
    if os.getenv("DATA_PERSIST", "1") != "1":
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    datos = [p.model_dump(mode="json") for p in _versiones[client_id]]
    _ruta(client_id).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _cargar(client_id: str) -> None:
    ruta = _ruta(client_id)
    if client_id not in _versiones and ruta.exists():
        _versiones[client_id] = [Perfil.model_validate(p) for p in json.loads(ruta.read_text("utf-8"))]


def cargar_fixture(nombre: str) -> Perfil:
    """Carga un perfil de ejemplo (p. ej. 'carmen-68') como versión nueva."""
    datos = json.loads((FIXTURES_DIR / f"{nombre}.json").read_text("utf-8"))
    perfil = Perfil.model_validate(datos)
    _recalcular(perfil)
    with _lock:
        _versiones[perfil.client_id] = [perfil]
        _guardar(perfil.client_id)
    return perfil


# ---------- lectura ----------

def perfil(client_id: str, version: int | None = None) -> Perfil:
    with _lock:
        _cargar(client_id)
        versiones = _versiones.get(client_id)
        if not versiones:
            raise NoEncontrado(client_id)
        if version is None:
            return versiones[-1]
        for p in versiones:
            if p.version == version:
                return p
        raise NoEncontrado(f"{client_id}@v{version}")


def versiones(client_id: str) -> list[dict]:
    perfil(client_id)  # lanza NoEncontrado si no existe
    return [
        {"version": p.version, "created_at": p.created_at, "reason": p.reason, "status": p.status}
        for p in _versiones[client_id]
    ]


# ---------- escritura (siempre crea versión nueva) ----------

def _nueva_version(actual: Perfil, motivo: str) -> Perfil:
    nueva = actual.model_copy(deep=True)
    nueva.version = actual.version + 1
    nueva.created_at = ahora()
    nueva.reason = motivo
    return nueva


def _recalcular(p: Perfil) -> None:
    """Rellena los campos calculados a partir de los datos disponibles."""
    v = {k: c.value for k, c in p.mifid.items()}
    gastos = v.get("financial.monthly_fixed_costs_eur")
    if gastos is not None:
        colchon = calculos.colchon_emergencia(float(gastos))
        p.mifid["financial.emergency_fund_eur"] = Campo(
            value=colchon, source=Fuente.calculated, updated_by=Autor.calculo,
            inputs=["financial.monthly_fixed_costs_eur"],
        )
        ahorro, deudas = v.get("financial.liquid_savings_eur"), v.get("financial.debts_eur")
        if ahorro is not None and deudas is not None:
            p.mifid["financial.loss_capacity_eur"] = Campo(
                value=calculos.capacidad_perdida(float(ahorro), colchon, float(deudas)),
                source=Fuente.calculated, updated_by=Autor.calculo,
                inputs=["financial.liquid_savings_eur", "financial.emergency_fund_eur", "financial.debts_eur"],
            )


def crear(client_id: str | None = None) -> Perfil:
    client_id = client_id or f"cliente-{uuid.uuid4().hex[:6]}"
    with _lock:
        _cargar(client_id)
        if client_id not in _versiones:
            _versiones[client_id] = [Perfil(client_id=client_id)]
            _guardar(client_id)
        return _versiones[client_id][-1]


def aplicar(client_id: str, cambios: list[ActualizacionCampo], motivo: str, autor: Autor) -> Perfil:
    with _lock:
        actual = _versiones[client_id][-1]
        nueva = _nueva_version(actual, motivo)
        for c in cambios:
            nueva.mifid[c.field] = Campo(
                value=c.value, source=c.source, declared=c.declared, confidence=c.confidence,
                evidence=c.evidence, flags=c.flags, updated_by=autor,
            )
        _recalcular(nueva)
        if nueva.status != EstadoPerfil.draft and autor != Autor.asesor:
            nueva.status = EstadoPerfil.review_pending  # un cambio tras validar obliga a revisar
        _versiones[client_id].append(nueva)
        _guardar(client_id)
        return nueva


def anadir_alertas(client_id: str, alertas: list[Alerta]) -> Perfil:
    with _lock:
        nueva = _nueva_version(_versiones[client_id][-1], f"{len(alertas)} alerta(s) del verificador")
        nueva.alerts.extend(alertas)
        _versiones[client_id].append(nueva)
        _guardar(client_id)
        return nueva


def validar(client_id: str, asesor_id: str, correcciones: list[ActualizacionCampo]) -> Perfil:
    """El asesor corrige (opcional) y valida: el perfil pasa a 'active'."""
    if correcciones:
        aplicar(client_id, correcciones, f"correcciones de {asesor_id}", Autor.asesor)
    with _lock:
        nueva = _nueva_version(_versiones[client_id][-1], f"validado por {asesor_id}")
        nueva.status = EstadoPerfil.active
        nueva.review.validated_by = asesor_id
        nueva.review.validated_at = ahora()
        _versiones[client_id].append(nueva)
        _guardar(client_id)
        return nueva


# ---------- sesiones de entrevista ----------

def crear_sesion(client_id: str | None = None) -> dict:
    p = crear(client_id)
    sid = f"s-{uuid.uuid4().hex[:8]}"
    with _lock:
        _sesiones[sid] = {"session_id": sid, "client_id": p.client_id, "started_at": ahora(), "turns": []}
    return {k: v for k, v in _sesiones[sid].items() if k != "turns"}


def sesion(session_id: str) -> dict:
    if session_id not in _sesiones:
        raise NoEncontrado(session_id)
    return _sesiones[session_id]


def anadir_turno(session_id: str, turno: Turno) -> int:
    s = sesion(session_id)
    with _lock:
        s["turns"].append(turno)
        return len(s["turns"]) - 1


def reiniciar() -> None:
    """Solo para tests."""
    with _lock:
        _versiones.clear()
        _sesiones.clear()
