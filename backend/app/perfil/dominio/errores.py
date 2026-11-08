"""Errores del dominio del perfil. La API los traduce a códigos HTTP (404, 409, 422)."""

from __future__ import annotations


class ErrorDominio(Exception):
    """Base de todos los errores del perfil."""


class NoEncontrado(ErrorDominio):
    """El cliente, la versión, la sesión o el dato no existen (HTTP 404)."""


class CampoInvalido(ErrorDominio):
    """La ruta no existe en el esquema o el valor no tiene el tipo esperado (HTTP 422)."""


class EscrituraNoPermitida(ErrorDominio):
    """El autor no puede escribir ese dato así: p. ej. un agente escribiendo un campo calculado (HTTP 422)."""


class TransicionNoPermitida(ErrorDominio):
    """El cambio de estado no está permitido por la máquina de estados (HTTP 409)."""


class ConflictoVersion(ErrorDominio):
    """Otra escritura creó antes la misma versión: hay que releer y reintentar (HTTP 409)."""
