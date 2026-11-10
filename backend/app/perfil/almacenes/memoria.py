"""Almacén en memoria (por defecto). Sustituye al store en memoria de la PR #7 con el mismo formato
de volcado a JSON en DATA_DIR (`perfil_<client_id>.json`), si DATA_PERSIST=1.

Útil para desarrollo, tests y la demo sin base de datos. Las sesiones no se vuelcan a disco.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..modelos import EstadoPerfil, Perfil, Turno
from ..personal import CapaPersonal
from .base import ConflictoVersion, cliente_del_lote, id_turno

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

    def _guardar_json(self, ruta: Path, contenido: str) -> None:
        """Sustituye el JSON completo; un fallo previo no altera el archivo anterior."""
        if not self._persistir():
            return
        self.data_dir.mkdir(parents=True, exist_ok=True)
        temporal = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.data_dir,
                                             prefix=".perfil-", suffix=".tmp", delete=False) as archivo:
                temporal = Path(archivo.name)
                archivo.write(contenido)
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, ruta)
        finally:
            if temporal is not None and temporal.exists():
                temporal.unlink()

    def _guardar_versiones(self, client_id: str, versiones: list[Perfil]) -> None:
        self._guardar_json(self._ruta(client_id), json.dumps(
            [p.model_dump(mode="json") for p in versiones], ensure_ascii=False, indent=2))

    def _guardar(self, client_id: str) -> None:
        # Una escritura MiFID nunca reescribe el archivo personal.
        self._guardar_versiones(client_id, self._versiones.get(client_id, []))

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

    def insertar_lote(self, perfiles: list[Perfil]) -> None:
        cid = cliente_del_lote(perfiles)
        with self._candado:
            vs = self._lista(cid)
            if not vs or perfiles[0].version != vs[-1].version + 1:
                raise ConflictoVersion(f"La versión de {cid} ha cambiado")
            nuevas = vs + [p.model_copy(deep=True) for p in perfiles]
            # Persistir antes de cambiar la referencia: los lectores no ven un lote parcial.
            # La capa personal no cambia durante validar(), ni se reescribe su fichero.
            self._guardar_versiones(cid, nuevas)
            self._versiones[cid] = nuevas

    # ---------- capa personal ----------

    @contextmanager
    def transaccion_personal(self, client_id: str):
        # Coordina hilos de UN proceso. Para varios procesos debe usarse SQL.
        with self._candado:
            self._cargar(client_id)
            transaccion = _PersonalMemoria(client_id, self._personal.get(client_id, []))
            yield transaccion
            if transaccion.modificada:
                self._guardar_json(self._ruta(client_id, "personal"), json.dumps(
                    [c.model_dump(mode="json") for c in transaccion.capas], ensure_ascii=False, indent=2))
                self._personal[client_id] = transaccion.capas

    def ultima_personal(self, client_id: str) -> CapaPersonal | None:
        with self._candado:
            self._cargar(client_id)
            capas = self._personal.get(client_id)
            return capas[-1].model_copy(deep=True) if capas else None

    def insertar_personal(self, capa: CapaPersonal) -> None:
        with self.transaccion_personal(capa.client_id) as transaccion:
            transaccion.insertar(capa)

    def borrar_personal(self, client_id: str) -> int:
        with self.transaccion_personal(client_id) as transaccion:
            return transaccion.borrar()

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

    def finalizar_sesion(self, session_id: str, conversation_id: str, momento: datetime) -> bool:
        with self._candado:
            s = self._sesiones.get(session_id)
            if s is None:
                return False
            if s["conversation_id"] not in (None, conversation_id):
                raise ConflictoVersion(f"La sesión {session_id} ya pertenece a otra conversación")
            if s["ended_at"] is None:
                s["ended_at"] = momento
                s["conversation_id"] = conversation_id
                return True
            return False

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


class _PersonalMemoria:
    def __init__(self, client_id: str, capas: list[CapaPersonal]):
        self.client_id = client_id
        self.capas = [c.model_copy(deep=True) for c in capas]
        self.modificada = False

    def ultima(self) -> CapaPersonal | None:
        return self.capas[-1].model_copy(deep=True) if self.capas else None

    def cantidad(self) -> int:
        return len(self.capas)

    def insertar(self, capa: CapaPersonal) -> None:
        if capa.client_id != self.client_id:
            raise ValueError("La capa pertenece a otro cliente")
        if any(c.version == capa.version for c in self.capas):
            raise ConflictoVersion(f"La versión personal {capa.version} ya existe")
        self.capas.append(capa.model_copy(deep=True))
        self.modificada = True

    def borrar(self) -> int:
        n = len(self.capas)
        self.capas = []
        self.modificada |= n > 0
        return n
