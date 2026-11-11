# Migraciones de Postgres / Supabase

`0001_esquema_inicial.sql` crea el esquema del perfil: `clients`, `profile_versions`,
`personal_versions`, `sessions` y `turns`. `0002_audio_de_sesion.sql` añade `session_audio`: el audio de cada
llamada de voz y los tiempos reales de cada turno ([pruebas de audio](../../docs/pruebas-de-audio.md)), de solo
añadir y con RLS sin políticas, como el resto. Es opcional para arrancar: un Postgres sin la 0002 arranca igual
y solo desactiva el audio (lo avisa en el log); el procedimiento de abajo es el mismo para aplicarla. Se aplica con `app.perfil.persistencia.migrar`, que la ejecuta
en una sola transacción, la registra en `schema_migrations` con su huella SHA-256 y no la repite.

Qué garantiza la 0001:

| Aspecto | Cómo |
|---|---|
| Solo añadir | Triggers que bloquean `UPDATE` y `DELETE` en `clients`, `profile_versions` y `turns`, y `UPDATE` en `personal_versions` (el `DELETE` de la capa personal se permite: derecho de supresión) |
| `TRUNCATE` | Triggers por sentencia en las 4 tablas; también bloquea `TRUNCATE ... CASCADE` |
| Integridad | Claves primarias y ajenas, `CHECK` de estado, canal, interlocutor, versión ≥ 1 e índice ≥ 0 |
| Data API de Supabase | RLS activado en todas las tablas, **sin políticas**, y `REVOKE` a `anon` y `authenticated` |
| Función del trigger | `search_path` fijo (evita el aviso *Function Search Path Mutable*) |
| Backend | Conecta como `postgres`, dueño de las tablas y con `BYPASSRLS` en Supabase |

## Procedimiento para aplicarla en Supabase

Todos los comandos desde `backend/`. **El destino es siempre explícito**: `migrar` y `verificar` no leen el
`.env` por su cuenta. Cada comando lleva `--destino host:puerto/base` (la base que esperas tocar) y toma la URL
de `DATABASE_URL` del entorno del proceso, o de un archivo con `--env-file RUTA` (solo esa variable: no carga
nada más). Si la URL apunta a otra base, el comando se niega **sin conectarse** (código 2). Ninguno imprime
usuario ni contraseña. **Detente en cuanto un paso dé FALLO o un código distinto de 0.**

Para Supabase (Session pooler, puerto 5432), con la URL en el `.env` de la raíz:

```bash
D="--env-file ../.env --destino aws-0-<región>.pooler.supabase.com:5432/postgres"   # el host de tu proyecto
```

| Paso | Comando | Cambia la base | Resultado esperado |
|---|---|---|---|
| 1. Comprobación previa | `python -m app.perfil.persistencia.verificar previo $D` | No (transacción de solo lectura) | `SIN FALLOS`, código 0, `0001` pendiente |
| 2. Ensayo | `python -m app.perfil.persistencia.verificar ensayo $D` | No: aplica en una transacción y **siempre** hace ROLLBACK | `SIN FALLOS` y `ensayo deshecho` |
| 3. Plan | `python -m app.perfil.persistencia.migrar $D` | No | `Pendientes: 0001_esquema_inicial.sql, 0002_audio_de_sesion.sql` (en una base ya migrada, solo la `0002`) |
| 4. Aplicar (**con autorización**) | `python -m app.perfil.persistencia.migrar $D --aplicar` | Sí | `Aplicada: …` por cada pendiente |
| 5. Verificación posterior | `python -m app.perfil.persistencia.verificar posterior $D --prueba-escritura` | No: la prueba de escritura se deshace | `SIN FALLOS`; bloquea UPDATE, DELETE y TRUNCATE |
| 6. Repetición | `python -m app.perfil.persistencia.migrar $D` | No | `No hay migraciones pendientes` |
| 7. Arranque de la app | `PERFIL_ALMACEN=bd uvicorn app.main:app --port 8000` | Sí: carga a Carmen (DATOS SIMULADOS) si no existe | `/api/health` ok; `/api/clients/carmen-68/profile` en v1 |

Avisos esperados en los pasos 1 y 2 (no son fallos): los disparadores de eventos de Supabase
(`ensure_rls`, `pgrst_*`, `issue_*`) y los permisos por defecto de `public` para `anon`/`authenticated`,
que la migración revoca en sus tablas.

### Si algo falla

- **Pasos 1, 2, 3, 5 o 6**: no han cambiado nada. Leer el FALLO, corregir y repetir.
- **Paso 4**: la migración es una sola transacción con `lock_timeout` de 10 s y `statement_timeout` de 120 s.
  Si falla, **no queda nada aplicado** y no se registra en `schema_migrations`. Corregir y volver al paso 1.
- **Paso 5 con FALLO después de aplicar**: no arrancar la app con `PERFIL_ALMACEN=bd`. El modo `memoria`
  sigue funcionando. Mientras no haya datos reales, se puede deshacer a mano desde el editor SQL de
  Supabase y volver a empezar:

  ```sql
  -- SOLO si no hay datos que conservar. Borra el esquema del perfil entero.
  drop table if exists turns, sessions, personal_versions, profile_versions, clients, schema_migrations;
  drop function if exists perfil_bloquear_cambio();
  ```

- **Nunca** editar una migración ya aplicada: crear `0002_...sql`. El paso 1 detecta huellas que no coinciden.

## Ensayo general en local (réplica de Supabase)

Antes de tocar Supabase, el procedimiento entero se puede repetir con la imagen oficial de su Postgres
(misma versión que el proyecto), en un contenedor desechable que solo escucha en `127.0.0.1`:

```bash
export PW=$(python -c "import secrets; print(secrets.token_hex(16))")   # contraseña local y desechable
docker run -d --name perfil-supabase-ensayo -e POSTGRES_PASSWORD=$PW -p 127.0.0.1:54417:5432 \
  public.ecr.aws/supabase/postgres:17.11.0.011
# (opcional) replicar el disparador ensure_rls del proyecto real antes de empezar
export DATABASE_URL="postgresql://postgres:$PW@127.0.0.1:54417/postgres"
D="--destino 127.0.0.1:54417/postgres"
# pasos 1 a 7 de la tabla anterior
docker rm -f perfil-supabase-ensayo
```

## Tests contra un Postgres local desechable

La suite vacía el esquema `public` de esa base en cada test. Por eso solo lo hace si la base es local, lleva
`test` en el nombre, no es de Supabase **y está marcada como desechable en el propio servidor**. Sin la marca,
los tests se niegan (`BaseNoAutorizada`) y no borran nada; así un `TEST_POSTGRES_URL` equivocado (otra base
local, un túnel) no puede vaciar una base que no sea de pruebas.

```bash
createdb -h 127.0.0.1 -p 54417 -U postgres perfil_test
psql -h 127.0.0.1 -p 54417 -U postgres -d perfil_test \
  -c "COMMENT ON DATABASE perfil_test IS 'idoneo:base-desechable-de-pruebas'"
TEST_POSTGRES_URL=postgresql://postgres:$PW@127.0.0.1:54417/perfil_test python -m pytest -q
```

Los tests arrancan siempre sin credenciales de pago ni red externa (`tests/aislamiento/`): las claves de
Anthropic y ElevenLabs quedan vacías aunque exista el `.env`, y solo se permiten conexiones a esta máquina,
también en los subprocesos que lanzan los tests.
