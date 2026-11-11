"""Interfaz común de los almacenes del perfil.

Los almacenes solo guardan y leen: no validan, no calculan y no deciden estados. Todo eso lo hace
`store.py` una única vez, así que el almacén en memoria y el de base de datos se comportan igual.

Garantías que debe cumplir cualquier almacén:
- `insertar` nunca sobrescribe: si la versión ya existe, lanza ConflictoVersion.
- `insertar_lote` guarda versiones consecutivas de un cliente: todas o ninguna.
- `insertar_turno` es idempotente por `turn_id` y asigna `t-001`, `t-002`… si no viene.
- la capa personal se guarda aparte del perfil y se puede borrar sin tocar las versiones.
- `guardar_audio` nunca sobrescribe: si la sesión ya tiene audio, devuelve False y no cambia nada.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from ..modelos import Perfil, Turno
from ..personal import CapaPersonal


class ConflictoVersion(Exception):
    """Otra escritura ya creó esa versión: hay que releer y reintentar."""


@dataclass(frozen=True)
class AudioSesion:
    """Audio de una sesión de voz y tiempos reales de cada turno (sin los bytes del audio)."""

    session_id: str
    conversation_id: str
    content_type: str
    size_bytes: int
    duration_s: float | None
    timings: dict[str, list[float]] = field(default_factory=dict)  # turn_id -> [inicio, fin] en segundos
    transcript: list[dict[str, Any]] = field(default_factory=list)  # transcripción oficial de ElevenLabs
    created_at: datetime | None = None


class TransaccionPersonal(Protocol):
    """Todas las operaciones de una capa usan el mismo bloqueo/conexión."""

    def ultima(self) -> CapaPersonal | None: ...
    def cantidad(self) -> int: ...
    def insertar(self, capa: CapaPersonal) -> None: ...
    def borrar(self) -> int: ...


class Almacen(Protocol):
    tipo: str

    # perfil (capa MiFID), de solo añadir
    def ultima(self, client_id: str) -> Perfil | None: ...
    def version(self, client_id: str, version: int) -> Perfil | None: ...
    def ultima_activa(self, client_id: str, desde: int) -> Perfil | None: ...
    def ultima_de_autor(self, client_id: str, autor: str) -> int | None: ...
    def historial(self, client_id: str) -> list[dict[str, Any]]: ...
    def clientes(self, limite: int) -> list[dict[str, Any]]: ...  # los más recientes primero
    def crear(self, perfil: Perfil) -> bool: ...
    def insertar(self, perfil: Perfil) -> None: ...
    def insertar_lote(self, perfiles: list[Perfil]) -> None: ...

    # capa personal
    def transaccion_personal(self, client_id: str) -> AbstractContextManager[TransaccionPersonal]: ...
    def ultima_personal(self, client_id: str) -> CapaPersonal | None: ...
    def insertar_personal(self, capa: CapaPersonal) -> None: ...
    def borrar_personal(self, client_id: str) -> int: ...

    # sesiones y transcripción
    def crear_sesion(self, session_id: str, client_id: str, canal: str, momento: datetime) -> None: ...
    def sesion(self, session_id: str) -> dict[str, Any] | None: ...
    def finalizar_sesion(self, session_id: str, conversation_id: str, momento: datetime) -> bool: ...
    def insertar_turno(self, session_id: str, turno: Turno, momento: datetime) -> tuple[Turno, bool]: ...
    def turnos(self, session_id: str) -> list[Turno]: ...

    # audio de las sesiones de voz, de solo añadir (una vez por sesión)
    def audio_disponible(self) -> bool: ...
    def guardar_audio(self, registro: AudioSesion, datos: bytes, momento: datetime) -> bool: ...
    def audio(self, session_id: str) -> tuple[AudioSesion, bytes] | None: ...
    def info_audio(self, session_ids: list[str]) -> dict[str, AudioSesion]: ...

    def reiniciar(self) -> None: ...  # solo tests
    def cerrar(self) -> None: ...


def id_turno(indice: int) -> str:
    """Mismo formato que la PR #7: t-001, t-002…"""
    return f"t-{indice + 1:03d}"


def cliente_del_lote(perfiles: list[Perfil]) -> str:
    """Los lotes internos son no vacíos, de un solo cliente y sin huecos."""
    if not perfiles:
        raise ValueError("Un lote de versiones no puede estar vacío")
    cid, inicio = perfiles[0].client_id, perfiles[0].version
    if any(p.client_id != cid or p.version != inicio + i for i, p in enumerate(perfiles)):
        raise ValueError("El lote debe contener versiones consecutivas de un solo cliente")
    return cid
