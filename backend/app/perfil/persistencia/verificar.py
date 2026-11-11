"""Verificación segura de la base de datos antes y después de aplicar las migraciones (Postgres/Supabase).

Uso (desde backend/). El destino es siempre explícito: no se lee el `.env` del repositorio por su cuenta.
Todos los modos exigen `--destino host:puerto/base` y toman la URL de DATABASE_URL del entorno del proceso
(o de `--env-file RUTA`, solo esa variable). Si la URL apunta a otra base, el script no se conecta.
    python -m app.perfil.persistencia.verificar previo --destino host:5432/base
        Solo lectura (transacción READ ONLY): conexión, versión, permisos del usuario, objetos que
        chocarían con la migración, disparadores de eventos, permisos por defecto y pendientes.
    python -m app.perfil.persistencia.verificar ensayo
        Aplica las migraciones pendientes DENTRO de una transacción, comprueba el resultado y hace
        SIEMPRE ROLLBACK. No deja cambios. Requiere autorización: ejecuta DDL aunque se deshaga.
    python -m app.perfil.persistencia.verificar posterior [--prueba-escritura]
        Solo lectura: comprueba el esquema ya aplicado (tablas, columnas, restricciones, triggers,
        RLS, políticas, permisos y huellas de las migraciones). Con --prueba-escritura intenta además
        las escrituras prohibidas (UPDATE, DELETE, TRUNCATE) en una transacción que se deshace.

Salida: una línea OK/AVISO/FALLO por comprobación. Código 0 si no hay fallos, 1 si los hay,
2 si el destino no es válido o no se puede conectar. Nunca imprime usuario ni contraseña.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from . import migrar, seguridad
from .db import crear_motor
from .tablas import metadata

TABLAS = sorted(metadata.tables)                       # las 5 del perfil
TABLAS_RLS = TABLAS + ["schema_migrations"]
FUNCION = "perfil_bloquear_cambio"
TRIGGERS = {                                           # nombre -> (tabla, operaciones bloqueadas)
    "clients_solo_anadir": ("clients", {"UPDATE", "DELETE"}),
    "clients_sin_truncate": ("clients", {"TRUNCATE"}),
    "profile_versions_solo_anadir": ("profile_versions", {"UPDATE", "DELETE"}),
    "profile_versions_sin_truncate": ("profile_versions", {"TRUNCATE"}),
    "turns_solo_anadir": ("turns", {"UPDATE", "DELETE"}),
    "turns_sin_truncate": ("turns", {"TRUNCATE"}),
    "personal_versions_sin_update": ("personal_versions", {"UPDATE"}),
    "personal_versions_sin_truncate": ("personal_versions", {"TRUNCATE"}),
}
ROLES_DATA_API = ("anon", "authenticated")
VERSION_MINIMA = 140000


@dataclass
class Informe:
    lineas: list[tuple[str, str, str]] = field(default_factory=list)  # (nivel, comprobación, detalle)

    def ok(self, nombre: str, detalle: str = "") -> None:
        self.lineas.append(("OK", nombre, detalle))

    def aviso(self, nombre: str, detalle: str) -> None:
        self.lineas.append(("AVISO", nombre, detalle))

    def fallo(self, nombre: str, detalle: str) -> None:
        self.lineas.append(("FALLO", nombre, detalle))

    def comprobar(self, condicion: bool, nombre: str, detalle_ok: str = "", detalle_fallo: str = "") -> None:
        (self.ok if condicion else self.fallo)(nombre, detalle_ok if condicion else detalle_fallo)  # type: ignore[operator]

    @property
    def fallos(self) -> int:
        return sum(1 for nivel, _, _ in self.lineas if nivel == "FALLO")

    def texto(self) -> str:
        return "\n".join(f"[{n:5}] {c}{(' · ' + d) if d else ''}" for n, c, d in self.lineas)


def _uno(c: Connection, sql: str, **p):
    return c.execute(text(sql), p).scalar()


def _lista(c: Connection, sql: str, **p) -> list:
    return [f[0] for f in c.execute(text(sql), p)]


# ---------- previo (solo lectura) ----------

def comprobar_previo(c: Connection, inf: Informe, directorio: Path = migrar.DIR_MIGRACIONES) -> None:
    num = int(_uno(c, "show server_version_num"))
    inf.comprobar(num >= VERSION_MINIMA, "versión de Postgres", _uno(c, "show server_version"),
                  f"{num} < {VERSION_MINIMA}")

    puede_crear = _uno(c, "select has_schema_privilege(current_user, 'public', 'CREATE')")
    inf.comprobar(bool(puede_crear), "el usuario puede crear objetos en public", "",
                  "sin privilegio CREATE en el esquema public")
    es_super, bypass = c.execute(text(
        "select rolsuper, rolbypassrls from pg_roles where rolname = current_user")).one()
    inf.ok("atributos del usuario", f"superusuario={es_super}, bypassrls={bypass}")

    roles = set(_lista(c, "select rolname from pg_roles where rolname in ('anon','authenticated','service_role')"))
    if roles:
        inf.ok("roles de la Data API de Supabase", ", ".join(sorted(roles)) + " (la migración revoca anon y authenticated)")
    else:
        inf.aviso("roles de la Data API de Supabase", "no existen (base que no es de Supabase)")

    registro_existe = bool(_uno(c, "select to_regclass('public.schema_migrations') is not null"))
    hechas = migrar.aplicadas(c.engine) if registro_existe else {}
    pendientes = [m for m in migrar.listar(directorio) if m.version not in hechas]
    alteradas = [m.nombre for m in migrar.listar(directorio) if m.version in hechas and hechas[m.version] != m.sha256]
    inf.comprobar(not alteradas, "migraciones aplicadas sin modificar", "",
                  f"cambiaron después de aplicarse: {alteradas}")
    inf.ok("migraciones pendientes", ", ".join(m.nombre for m in pendientes) or "ninguna")

    if any(m.version == "0001" for m in pendientes):
        existentes = _lista(c, "select tablename from pg_tables where schemaname = 'public' and tablename = any(:t)",
                            t=TABLAS)
        inf.comprobar(not existentes, "sin tablas que choquen con 0001", "",
                      f"ya existen en public: {existentes}")
        funcion = _uno(c, "select count(*) from pg_proc where proname = :f and pronamespace = 'public'::regnamespace",
                       f=FUNCION)
        inf.comprobar(funcion == 0, "sin función que choque con 0001", "", f"ya existe public.{FUNCION}")

    otras = _lista(c, "select tablename from pg_tables where schemaname = 'public' and tablename <> all(:t) "
                      "order by 1", t=TABLAS + ["schema_migrations"])
    if otras:
        inf.aviso("otras tablas en public (no se tocan)", ", ".join(otras))
    else:
        inf.ok("otras tablas en public", "ninguna")

    eventos = c.execute(text("select evtname, evtevent, evtenabled from pg_event_trigger order by 1")).all()
    if eventos:
        inf.aviso("disparadores de eventos (se ejecutarán durante la migración)",
                  "; ".join(f"{n} en {e}{'' if h != 'D' else ' (desactivado)'}" for n, e, h in eventos))
    else:
        inf.ok("disparadores de eventos", "ninguno")

    acl = _lista(c, "select array_to_string(defaclacl, ',') from pg_default_acl "
                    "where defaclnamespace = 'public'::regnamespace and defaclobjtype = 'r'")
    abiertos = [r for r in ROLES_DATA_API if any(f"{r}=" in a for a in acl)]
    if abiertos:
        inf.aviso("permisos por defecto en public", f"conceden tablas nuevas a {', '.join(abiertos)}; "
                                                    "la migración se los revoca a sus tablas")
    else:
        inf.ok("permisos por defecto en public", "no conceden nada a anon/authenticated")

    cursor = c.connection.dbapi_connection.cursor()
    try:
        cursor.execute("select 1; select 2")  # el pooler debe aceptar scripts con varias sentencias
        inf.ok("varias sentencias en una llamada", "admitidas por la conexión")
    except Exception as e:  # pragma: no cover - depende del pooler
        inf.fallo("varias sentencias en una llamada", type(e).__name__)
    finally:
        cursor.close()


# ---------- posterior (solo lectura) ----------

def comprobar_posterior(c: Connection, inf: Informe, directorio: Path = migrar.DIR_MIGRACIONES) -> None:
    existe_registro = bool(_uno(c, "select to_regclass('public.schema_migrations') is not null"))
    inf.comprobar(existe_registro, "registro de migraciones", "schema_migrations existe", "no existe schema_migrations")
    if existe_registro:
        hechas = {f.version: f.sha256 for f in c.execute(text("select version, sha256 from schema_migrations"))}
        for m in migrar.listar(directorio):
            inf.comprobar(hechas.get(m.version) == m.sha256, f"migración {m.nombre}", "aplicada y sin cambios",
                          "no aplicada" if m.version not in hechas else "su huella no coincide con el fichero")

    existentes = set(_lista(c, "select tablename from pg_tables where schemaname = 'public'"))
    for tabla in TABLAS:
        if tabla not in existentes:
            inf.fallo(f"tabla {tabla}", "no existe")
            continue
        columnas = set(_lista(c, "select column_name from information_schema.columns "
                                 "where table_schema = 'public' and table_name = :t", t=tabla))
        esperadas = {col.name for col in metadata.tables[tabla].columns}
        inf.comprobar(columnas == esperadas, f"tabla {tabla}", f"{len(columnas)} columnas",
                      f"columnas distintas: sobran {sorted(columnas - esperadas)}, faltan {sorted(esperadas - columnas)}")

    restricciones = set(_lista(c, "select conname from pg_constraint where connamespace = 'public'::regnamespace"))
    esperadas = {"profile_versions_status_check", "profile_versions_version_check", "personal_versions_version_check",
                 "sessions_channel_check", "turns_idx_check", "turns_speaker_check", "turns_session_id_idx_key",
                 "profile_versions_client_id_fkey", "personal_versions_client_id_fkey", "sessions_client_id_fkey",
                 "turns_session_id_fkey", "clients_client_id_check"}
    faltan = sorted(esperadas - restricciones)
    inf.comprobar(not faltan, "restricciones y claves ajenas", f"{len(esperadas)} presentes", f"faltan {faltan}")

    filas = c.execute(text(
        "select t.tgname, c.relname, t.tgenabled, t.tgtype from pg_trigger t join pg_class c on c.oid = t.tgrelid "
        "where not t.tgisinternal and c.relnamespace = 'public'::regnamespace")).all()
    reales = {n: (tabla, habil, tipo) for n, tabla, habil, tipo in filas}
    for nombre, (tabla, ops) in TRIGGERS.items():
        if nombre not in reales:
            inf.fallo(f"trigger {nombre}", "no existe")
            continue
        t_tabla, habil, tipo = reales[nombre]
        # bits de tgtype: 4 INSERT, 8 DELETE, 16 UPDATE, 32 TRUNCATE
        cubre = {op for op, bit in (("DELETE", 8), ("UPDATE", 16), ("TRUNCATE", 32)) if tipo & bit}
        bien = t_tabla == tabla and habil != "D" and ops <= cubre
        inf.comprobar(bien, f"trigger {nombre}", f"{tabla}: bloquea {', '.join(sorted(ops))}",
                      f"tabla={t_tabla}, activo={habil != 'D'}, bloquea={sorted(cubre)}")

    config = _uno(c, "select array_to_string(proconfig, ',') from pg_proc "
                     "where proname = :f and pronamespace = 'public'::regnamespace", f=FUNCION)
    inf.comprobar(bool(config) and "search_path" in config, f"función {FUNCION}", "search_path fijado",
                  "sin search_path fijado (aviso de seguridad de Supabase)")

    sin_rls = _lista(c, "select relname from pg_class where relnamespace = 'public'::regnamespace "
                        "and relkind = 'r' and relname = any(:t) and not relrowsecurity", t=TABLAS_RLS)
    inf.comprobar(not sin_rls, "RLS activado", f"en {len(TABLAS_RLS)} tablas", f"sin RLS: {sin_rls}")
    politicas = _lista(c, "select tablename || '.' || policyname from pg_policies "
                          "where schemaname = 'public' and tablename = any(:t)", t=TABLAS_RLS)
    inf.comprobar(not politicas, "sin políticas RLS (nadie entra por la Data API)", "", f"hay políticas: {politicas}")

    roles = _lista(c, "select rolname from pg_roles where rolname = any(:r)", r=list(ROLES_DATA_API))
    if roles:
        permisos = _lista(c, "select grantee || ':' || table_name || ':' || privilege_type "
                             "from information_schema.role_table_grants where table_schema = 'public' "
                             "and grantee = any(:r) and table_name = any(:t)", r=roles, t=TABLAS_RLS)
        inf.comprobar(not permisos, f"sin permisos para {', '.join(roles)}", "", f"permisos: {permisos[:6]}")
    else:
        inf.aviso("permisos de la Data API", "no existen los roles anon/authenticated (no es Supabase)")


def prueba_escritura(c: Connection, inf: Informe) -> None:
    """Intenta escrituras prohibidas sobre filas de prueba. Debe ejecutarse en una transacción que se deshace."""
    cid = f"verificacion-{uuid.uuid4().hex[:8]}"
    c.execute(text("set local lock_timeout = '5s'"))  # TRUNCATE pide un bloqueo exclusivo: no esperar
    c.execute(text("insert into clients (client_id, created_at) values (:c, now())"), {"c": cid})
    c.execute(text("insert into profile_versions (client_id, version, status, reason, author, snapshot, created_at) "
                   "values (:c, 1, 'draft', 'verificación', 'system', '{}', now())"), {"c": cid})
    inf.ok("insertar versión", "permitido")
    intentos = {
        "UPDATE profile_versions": "update profile_versions set reason = 'x' where client_id = :c",
        "DELETE profile_versions": "delete from profile_versions where client_id = :c",
        "UPDATE clients": "update clients set created_at = now() where client_id = :c",
        "TRUNCATE profile_versions": "truncate profile_versions",
        "TRUNCATE turns": "truncate turns",
        "TRUNCATE personal_versions": "truncate personal_versions",
        "TRUNCATE clients CASCADE": "truncate clients cascade",
    }
    for nombre, sql in intentos.items():
        punto = c.begin_nested()
        try:
            c.execute(text(sql), {"c": cid})
            punto.rollback()
            inf.fallo(f"bloquea {nombre}", "la base lo permitió")
        except Exception as e:
            punto.rollback()
            inf.comprobar("solo añadir" in str(e), f"bloquea {nombre}", "",
                          f"falló por otro motivo: {str(e).splitlines()[0][:120]}")
    quedan = _uno(c, "select count(*) from profile_versions where client_id = :cid", cid=cid)
    inf.comprobar(quedan == 1, "la versión de prueba sigue intacta", "", f"quedan {quedan}")


# ---------- modos ----------

def previo(motor: Engine) -> Informe:
    inf = Informe()
    with motor.connect() as c:
        c.execute(text("set transaction read only"))
        comprobar_previo(c, inf)
        c.rollback()
    return inf


def posterior(motor: Engine, con_prueba_escritura: bool = False) -> Informe:
    inf = Informe()
    with motor.connect() as c:
        c.execute(text("set transaction read only"))
        comprobar_posterior(c, inf)
        c.rollback()
    if con_prueba_escritura:
        with motor.connect() as c:
            try:
                prueba_escritura(c, inf)
            finally:
                c.rollback()  # no queda nada
    return inf


def ensayo(motor: Engine, directorio: Path = migrar.DIR_MIGRACIONES) -> Informe:
    """Aplica las pendientes en una transacción, comprueba y deshace SIEMPRE."""
    inf = previo(motor)
    if inf.fallos:
        inf.fallo("ensayo", "no se ejecuta: hay fallos en la comprobación previa")
        return inf
    pendientes = migrar.pendientes(motor, directorio)
    with motor.connect() as c:
        try:
            c.execute(text("set local lock_timeout = '10s'"))
            c.execute(text("set local statement_timeout = '120s'"))
            migrar._ejecutar_script(c, migrar.TABLA_REGISTRO)  # noqa: SLF001
            for m in pendientes:
                migrar._ejecutar_script(c, m.sql)  # noqa: SLF001
                c.execute(text("insert into schema_migrations (version, nombre, sha256) values (:v, :n, :s)"),
                          {"v": m.version, "n": m.nombre, "s": m.sha256})
                inf.ok(f"ensayo: {m.nombre}", "se ejecuta sin errores")
            comprobar_posterior(c, inf, directorio)
            if pendientes:
                prueba_escritura(c, inf)
        except Exception as e:
            inf.fallo("ensayo", f"{type(e).__name__}: {str(e).splitlines()[0][:200]}")
        finally:
            c.rollback()
    inf.ok("ensayo deshecho", "ROLLBACK: la base queda como estaba")
    return inf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modo", choices=["previo", "ensayo", "posterior"])
    parser.add_argument("--prueba-escritura", action="store_true", help="solo en 'posterior'")
    seguridad.anadir_argumentos_destino(parser)
    args = parser.parse_args(argv)

    try:
        url = seguridad.destino_explicito(args.destino, args.variable, args.env_file)
    except seguridad.DestinoNoValido as e:
        print(f"Destino no válido: {e}")
        return 2
    print(f"Base de datos: {seguridad.describir(url)} · modo {args.modo}")
    try:
        motor = crear_motor(url)
        if args.modo == "previo":
            inf = previo(motor)
        elif args.modo == "ensayo":
            inf = ensayo(motor)
        else:
            inf = posterior(motor, args.prueba_escritura)
    except Exception as e:
        print(f"[FALLO] conexión · {type(e).__name__}: {str(e).splitlines()[0][:200]}")
        return 2
    print(inf.texto())
    print(f"Resultado: {'SIN FALLOS' if not inf.fallos else f'{inf.fallos} FALLO(S)'}")
    return 1 if inf.fallos else 0


if __name__ == "__main__":
    sys.exit(main())
