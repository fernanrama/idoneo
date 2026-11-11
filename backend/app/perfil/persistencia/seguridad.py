"""Protecciones de la base de datos: destino explícito para las herramientas y bases desechables para borrar.

1. `destino_explicito`: `migrar` y `verificar` no leen el `.env` por su cuenta. La URL sale de una variable
   del entorno del proceso (por defecto DATABASE_URL) o de un archivo indicado con `--env-file`, y además
   hay que escribir el destino esperado (`--destino host:puerto/base`). Si no coinciden, no se conecta.
2. `vaciar_esquema_publico`: la única forma de borrar el esquema `public` (tests y `AlmacenBD.reiniciar`).
   Exige una base local, con `test` en el nombre, que no sea de Supabase y que esté MARCADA como desechable
   en el propio servidor:  COMMENT ON DATABASE <base> IS 'idoneo:base-desechable-de-pruebas';
   Así un `TEST_POSTGRES_URL` mal puesto (otra base local, un túnel a Supabase...) nunca borra nada.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import Connection, Engine, text
from sqlalchemy.engine import URL, make_url

MARCA_DESECHABLE = "idoneo:base-desechable-de-pruebas"
HOSTS_LOCALES = ("", "localhost", "127.0.0.1", "::1")


class BaseNoAutorizada(RuntimeError):
    """La operación destructiva no se permite sobre esta base."""


class DestinoNoValido(ValueError):
    """La herramienta no tiene un destino explícito y coherente."""


# ---------- bases desechables (operaciones destructivas) ----------

def comprobar_url_de_pruebas(url: str | URL) -> str:
    """Comprobación sin conectar: base local, nombre con 'test' y nunca Supabase. Devuelve la URL."""
    texto = url if isinstance(url, str) else url.render_as_string(hide_password=False)
    u = make_url(texto)
    if "supabase" in texto.lower() or (u.host or "") not in HOSTS_LOCALES or "test" not in (u.database or ""):
        raise BaseNoAutorizada("Solo un Postgres local de pruebas (nombre con 'test'), nunca Supabase")
    return texto


def exigir_base_desechable(conexion: Connection) -> None:
    """Comprobación en el servidor: la base conectada es de pruebas y está marcada como desechable."""
    base, marca = conexion.execute(text(
        "select current_database(), shobj_description(oid, 'pg_database') "
        "from pg_database where datname = current_database()")).one()
    if "test" not in base:
        raise BaseNoAutorizada(f"La base '{base}' no es de pruebas")
    if marca != MARCA_DESECHABLE:
        raise BaseNoAutorizada(
            f"La base '{base}' no está marcada como desechable. Si es una base local solo para tests: "
            f"COMMENT ON DATABASE {base} IS '{MARCA_DESECHABLE}';")


def vaciar_esquema_publico(motor: Engine) -> None:
    """Borra y recrea `public` (todos sus objetos y datos) SOLO en una base desechable autorizada."""
    if motor.dialect.name != "postgresql":
        raise BaseNoAutorizada("vaciar_esquema_publico es solo para Postgres")
    comprobar_url_de_pruebas(motor.url)
    with motor.begin() as c:
        exigir_base_desechable(c)
        c.execute(text("drop schema public cascade"))
        c.execute(text("create schema public"))


# ---------- destino explícito de las herramientas ----------

def _partes(u: URL) -> tuple[str, int, str]:
    return ((u.host or "").lower(), int(u.port or 5432), u.database or "")


def describir(url: str | URL) -> str:
    """host:puerto/base, sin usuario ni contraseña."""
    host, puerto, base = _partes(make_url(url) if isinstance(url, str) else url)
    return f"{host}:{puerto}/{base}"


def destino_explicito(destino: str, variable: str = "DATABASE_URL", env_file: str | None = None) -> str:
    """URL de Postgres cuyo host, puerto y base coinciden con `destino` ("host:puerto/base").

    La URL se toma de `env_file` (solo esa variable; no se carga nada más en el entorno) o, si no se indica,
    de la variable del entorno del proceso. Nunca del `.env` del repositorio de forma implícita.
    """
    if env_file:
        ruta = Path(env_file)
        if not ruta.is_file():
            raise DestinoNoValido(f"No existe el archivo {ruta}")
        from dotenv import dotenv_values

        url = (dotenv_values(ruta).get(variable) or "").strip()
        origen = f"{variable} de {ruta.name}"
    else:
        url = os.environ.get(variable, "").strip()
        origen = f"la variable de entorno {variable}"
    if not url:
        raise DestinoNoValido(f"No hay URL en {origen}")
    try:
        u = make_url(url)
    except Exception as e:  # noqa: BLE001 - nunca mostrar la URL (puede llevar contraseña)
        raise DestinoNoValido(f"La URL de {origen} no es válida") from e
    if u.get_backend_name() != "postgresql":
        raise DestinoNoValido("Las migraciones y la verificación son para Postgres")
    try:
        host, resto = destino.rsplit(":", 1)
        puerto, base = resto.split("/", 1)
        esperado = (host.strip("[]").lower(), int(puerto), base)
    except ValueError as e:
        raise DestinoNoValido("--destino debe tener la forma host:puerto/base") from e
    if _partes(u) != esperado:
        raise DestinoNoValido(f"{origen} apunta a {describir(u)}, no a {destino}: no me conecto")
    return url


def anadir_argumentos_destino(parser) -> None:
    """Argumentos comunes de `migrar` y `verificar`."""
    parser.add_argument("--destino", required=True, metavar="HOST:PUERTO/BASE",
                        help="base esperada; si la URL apunta a otra, no se conecta")
    parser.add_argument("--variable", default="DATABASE_URL",
                        help="variable con la URL (por defecto DATABASE_URL); se lee del entorno del proceso")
    parser.add_argument("--env-file", metavar="RUTA",
                        help="leer la variable de este archivo (solo esa; no se carga nada más)")
