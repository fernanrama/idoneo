"""Almacén en memoria (por defecto). Sustituye al store en memoria de la PR #7 con el mismo formato
de volcado a JSON en DATA_DIR (`perfil_<client_id>.json`), si DATA_PERSIST=1.

Útil para desarrollo, tests y la demo sin base de datos. Las sesiones no se vuelcan a disco.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..modelos import EstadoPerfil, Perfil, Turno
from ..personal import CapaPersonal
from .base import ConflictoVersion, id_turno

DATA_DIR_POR_DEFECTO = Path(__file__).resolve().parents[3] / "data"


class AlmacenMemoria:
    tipo = "memoria"

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or os.getenv("DATA_DIR", DATA_DIR_POR_DEFECTO))
        self._candado = threading.RLock()
        self._versiones: dict[str, list[Perfil]] = {}
        self._personal: dict[str, list[CapaPersonal]] = {}
        self._sesiones: dict[str, dict[str, Any]] = {}
        self._turnos: dict[str, list[Turno]] = {}

    # ---------- volcado a disco (mismo formato que la PR #7) ----------

    @staticmethod
    def _persistir() -> bool:
        return os.getenv("DATA_PERSIST", "1") == "1"

    def _ruta(self, client_id: str, tipo: str = "perfil") -> Path:
        return self.data_dir / f"{tipo}_{client_id}.json"  # client_id ya validado por store

    def _guardar(self, client_id: str) -> None:
        if not self._persistir():
            return
        self.data_dir.mkdir(parents=True, exist_ok=True)
        versiones = [p.model_dump(mode="json") for p in self._versiones.get(client_id, [])]
        self._ruta(client_id).write_text(json.dumps(versiones, ensure_ascii=False, indent=2), "utf-8")
        personal = [c.model_dump(mode="json") for c in self._personal.get(client_id, [])]
        ruta_personal = self._ruta(client_id, "personal")
        if personal:
            ruta_personal.write_text(json.dumps(personal, ensure_ascii=False, indent=2), "utf-8")
        elif ruta_personal.exists():
            ruta_personal.unlink()  # derecho de supresión también en disco

    def _cargar(self, client_id: str) -> None:
        if client_id in self._versiones or not self._persistir():
            return
        ruta = self._ruta(client_id)
        if ruta.exists():
            self._versiones[client_id] = [Perfil.model_validate(p) for p in json.loads(ruta.read_text("utf-8"))]
            ruta_personal = self._ruta(client_id, "personal")
            if ruta_personal.exists():
                self._personal[client_id] = [CapaPersonal.model_validate(c)
                                             for c in json.loads(ruta_personal.read_text("utf-8"))]

    def _lista(self, client_id: str) -> list[Perfil]:
        self._cargar(client_id)
        return self._versiones.get(client_id, [])

    # ---------- perfil ----------

    def ultima(self, client_id: str) -> Perfil | None:
        with self._candado:
            vs = self._lista(client_id)
            return vs[-1].model_copy(deep=True) if vs else None

    def version(self, client_id: str, version: int) -> Perfil | None:
        with self._candado:
            p = next((p for p in self._lista(client_id) if p.version == version), None)
            return p.model_copy(deep=True) if p else None

    def ultima_activa(self, client_id: str, desde: int) -> Perfil | None:
        with self._candado:
            activas = [p for p in self._lista(client_id) if p.status == EstadoPerfil.active and p.version >= desde]
            return activas[-1].model_copy(deep=True) if activas else None

    def ultima_de_autor(self, client_id: str, autor: str) -> int | None:
        with self._candado:
            vs = [p.version for p in self._lista(client_id) if p.author == autor]
            return vs[-1] if vs else None

    def historial(self, client_id: str) -> list[dict[str, Any]]:
        with self._candado:
            return [{"version": p.version, "created_at": p.created_at, "reason": p.reason,
                     "author": p.author, "status": p.status} for p in self._lista(client_id)]

    def crear(self, perfil: Perfil) -> bool:
        with self._candado:
            if self._lista(perfil.client_id):
                return False
            self._versiones[perfil.client_id] = [perfil.model_copy(deep=True)]
            self._guardar(perfil.client_id)
            return True

    def insertar(self, perfil: Perfil) -> None:
        with self._candado:
            vs = self._lista(perfil.client_id)
            if not vs:
                raise ConflictoVersion(f"{perfil.client_id} no existe")
            if any(p.version == perfil.version for p in vs):
                raise ConflictoVersion(f"La versión {perfil.version} de {perfil.client_id} ya existe")
            vs.append(perfil.model_copy(deep=True))
            self._guardar(perfil.client_id)

    # ---------- capa personal ----------

    def ultima_personal(self, client_id: str) -> CapaPersonal | None:
        with self._candado:
            self._cargar(client_id)
            capas = self._personal.get(client_id)
            return capas[-1].model_copy(deep=True) if capas else None

    def insertar_personal(self, capa: CapaPersonal) -> None:
        with self._candado:
            capas = self._personal.setdefault(capa.client_id, [])
            if any(c.version == capa.version for c in capas):
                raise ConflictoVersion(f"La versión personal {capa.version} de {capa.client_id} ya existe")
            capas.append(capa.model_copy(deep=True))
            self._guardar(capa.client_id)

    def borrar_personal(self, client_id: str) -> int:
        with self._candado:
            self._cargar(client_id)
            n = len(self._personal.pop(client_id, []))
            self._guardar(client_id)
            return n

    # ---------- sesiones ----------

    def crear_sesion(self, session_id: str, client_id: str, canal: str, momento: datetime) -> None:
        with self._candado:
            self._sesiones[session_id] = {"session_id": session_id, "client_id": client_id, "channel": canal,
                                          "started_at": momento, "ended_at": None, "conversation_id": None}
            self._turnos[session_id] = []

    def sesion(self, session_id: str) -> dict[str, Any] | None:
        with self._candado:
            s = self._sesiones.get(session_id)
            return dict(s) if s else None

    def insertar_turno(self, session_id: str, turno: Turno, momento: datetime) -> tuple[Turno, bool]:
        with self._candado:
            lista = self._turnos[session_id]
            if turno.turn_id:
                previo = next((t for t in lista if t.turn_id == turno.turn_id), None)
                if previo is not None:
                    return previo.model_copy(), False
            else:
                ids = {t.turn_id for t in lista}
                candidato = id_turno(len(lista))
                turno = turno.model_copy(update={
                    "turn_id": candidato if candidato not in ids else f"{candidato}-{uuid.uuid4().hex[:4]}"})
            lista.append(turno.model_copy())
            return turno, True

    def turnos(self, session_id: str) -> list[Turno]:
        with self._candado:
            return [t.model_copy() for t in self._turnos.get(session_id, [])]

    # ---------- utilidades ----------

    def reiniciar(self) -> None:
        with self._candado:
            self._versiones.clear()
            self._personal.clear()
            self._sesiones.clear()
            self._turnos.clear()

    def cerrar(self) -> None:
        pass
