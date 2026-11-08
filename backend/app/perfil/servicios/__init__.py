"""Servicios del perfil. `construir_servicios()` monta todo sobre una base de datos."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine

from ..persistencia import db
from ..persistencia.repositorio import Repositorio
from .eventos import BusEventos
from .perfiles import ServicioPerfiles
from .sesiones import ServicioSesiones


@dataclass
class Servicios:
    motor: Engine
    repo: Repositorio
    bus: BusEventos
    perfiles: ServicioPerfiles
    sesiones: ServicioSesiones


def construir_servicios(url: str | None = None) -> Servicios:
    """Sin url usa DATABASE_URL (o SQLite local). En Postgres exige las migraciones aplicadas."""
    motor = db.crear_motor(url)
    db.preparar(motor)
    repo = Repositorio(motor)
    bus = BusEventos()
    perfiles = ServicioPerfiles(repo, bus)
    return Servicios(motor, repo, bus, perfiles, ServicioSesiones(repo, perfiles))
