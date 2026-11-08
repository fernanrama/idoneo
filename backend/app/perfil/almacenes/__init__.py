"""Almacenes intercambiables del perfil: `PERFIL_ALMACEN=memoria|bd` (por defecto, memoria)."""

from __future__ import annotations

import os

from .base import Almacen, ConflictoVersion

TIPOS = ("memoria", "bd")


def crear_almacen(tipo: str | None = None, url: str | None = None) -> Almacen:
    tipo = (tipo or os.getenv("PERFIL_ALMACEN") or "memoria").strip().lower()
    if tipo == "memoria":
        from .memoria import AlmacenMemoria
        return AlmacenMemoria()
    if tipo == "bd":
        from .bd import AlmacenBD
        return AlmacenBD.desde_url(url)
    raise ValueError(f"PERFIL_ALMACEN={tipo!r} no válido: usa 'memoria' o 'bd'")


__all__ = ["Almacen", "ConflictoVersion", "TIPOS", "crear_almacen"]
