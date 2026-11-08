"""Aplica las migraciones SQL numeradas de backend/migraciones/ a la base de DATABASE_URL (Postgres).

Uso (desde backend/):
    python -m app.perfil.persistencia.migrar            # solo muestra el plan, no cambia nada
    python -m app.perfil.persistencia.migrar --aplicar  # aplica las pendientes, cada una en su transacción

Cada migración aplicada queda registrada en `schema_migrations` con su huella SHA-256: si alguien
edita una migración ya aplicada, el script se niega a continuar. Nunca imprime la cadena de conexión.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import make_url

from .db import crear_motor, url_desde_entorno

DIR_MIGRACIONES = Path(__file__).resolve().parents[3] / "migraciones"
_NOMBRE = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")

TABLA_REGISTRO = """
create table if not exists schema_migrations (
    version     text primary key,
    nombre      text not null,
    sha256      text not null,
    applied_at  timestamptz not null default now()
);
alter table schema_migrations enable row level security;
do $$
declare
    rol text;
begin
    foreach rol in array array['anon', 'authenticated'] loop
        if exists (select 1 from pg_roles where rolname = rol) then
            execute format('revoke all on schema_migrations from %I', rol);
        end if;
    end loop;
end
$$;
"""


@dataclass(frozen=True)
class Migracion:
    version: str
    nombre: str
    sql: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def listar(directorio: Path = DIR_MIGRACIONES) -> list[Migracion]:
    migraciones = []
    for f in sorted(directorio.glob("*.sql")):
        m = _NOMBRE.match(f.name)
        if not m:
            raise ValueError(f"Nombre de migración no válido: {f.name} (formato 0001_descripcion.sql)")
        migraciones.append(Migracion(m.group(1), f.name, f.read_text("utf-8")))
    versiones = [m.version for m in migraciones]
    if len(set(versiones)) != len(versiones):
        raise ValueError("Hay dos migraciones con el mismo número")
    return migraciones


def aplicadas(motor: Engine) -> dict[str, str]:
    """Solo lee: si aún no existe schema_migrations, no hay ninguna aplicada (y no la crea)."""
    if "schema_migrations" not in inspect(motor).get_table_names():
        return {}
    with motor.connect() as c:
        return {f.version: f.sha256 for f in c.execute(text("select version, sha256 from schema_migrations"))}


def pendientes(motor: Engine, directorio: Path = DIR_MIGRACIONES) -> list[Migracion]:
    hechas = aplicadas(motor)
    resultado = []
    for m in listar(directorio):
        if m.version in hechas:
            if hechas[m.version] != m.sha256:
                raise RuntimeError(f"La migración {m.nombre} ya aplicada ha cambiado: crea una nueva en su lugar")
            continue
        resultado.append(m)
    return resultado


def _ejecutar_script(conexion, sql: str) -> None:
    """Ejecuta un script SQL completo sin parámetros: así los '%' de PL/pgSQL no se toman por marcadores."""
    cursor = conexion.connection.dbapi_connection.cursor()
    try:
        cursor.execute(sql)
    finally:
        cursor.close()


def aplicar(motor: Engine, directorio: Path = DIR_MIGRACIONES) -> list[str]:
    hechas = []
    lista = pendientes(motor, directorio)
    if lista:
        with motor.begin() as c:
            _ejecutar_script(c, TABLA_REGISTRO)
    for m in lista:
        with motor.begin() as c:  # si falla, esa migración se deshace entera
            # Tiempos límite: si algo bloquea las tablas, fallar pronto en vez de quedarse esperando.
            c.execute(text("set local lock_timeout = '10s'"))
            c.execute(text("set local statement_timeout = '120s'"))
            _ejecutar_script(c, m.sql)
            c.execute(text("insert into schema_migrations (version, nombre, sha256) values (:v, :n, :s)"),
                      {"v": m.version, "n": m.nombre, "s": m.sha256})
        hechas.append(m.nombre)
    return hechas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="aplica las migraciones pendientes")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[4] / ".env")  # .env en la raíz del repo

    url = make_url(url_desde_entorno())
    if url.get_backend_name() != "postgresql":
        print("Las migraciones son para Postgres. En SQLite las tablas se crean solas al arrancar.")
        return 1
    print(f"Base de datos: {url.host} · base '{url.database}'")  # sin usuario ni contraseña
    motor = crear_motor(url.render_as_string(hide_password=False))
    lista = pendientes(motor)
    if not lista:
        print("No hay migraciones pendientes.")
        return 0
    print("Pendientes:", ", ".join(m.nombre for m in lista))
    if not args.aplicar:
        print("Modo plan: no se ha cambiado nada. Repite con --aplicar para ejecutarlas.")
        return 0
    for nombre in aplicar(motor):
        print("Aplicada:", nombre)
    return 0


if __name__ == "__main__":
    sys.exit(main())
