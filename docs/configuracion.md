# Configuración

Variables de entorno y persistencia del backend y del frontend. Para arrancar en local basta con `python scripts/preparar_demo.py` ([README](../README.md#pruébalo)); esta página es la referencia completa.

**Producción** (Vercel + Render + Supabase, con topes de gasto): [docs/despliegue.md](despliegue.md). Desplegada en <https://hack-finance-uc3m-2026.vercel.app>.

El `.env` va en la raíz del repo (plantilla en `.env.example`) y nunca se sube a Git. Arranca el backend desde `backend/`: las rutas relativas (`DATA_DIR=./data`) se resuelven desde ahí y `backend/data/` está ignorada por Git.

<details>
<summary><b>Variables del backend</b></summary>

Todas están en `.env.example`.

| Variable | Por defecto | Para qué |
|---|---|---|
| `PERFIL_ALMACEN` | `memoria` | `memoria` o `bd` (ver «Persistencia del perfil» más abajo) |
| `DATABASE_URL` | vacío | Solo con `bd`. La contraseña, solo en tu `.env` |
| `DATA_DIR` | `backend/data` | Carpeta de los volcados JSON (memoria) y de la base SQLite |
| `DATA_PERSIST` | `1` | `1` vuelca el almacén en memoria a `DATA_DIR`; `0` no escribe nada en disco (lo usan los tests) |
| `LOAD_DEMO_FIXTURE` | `1` | Carga a Carmen (DATOS SIMULADOS) al arrancar, solo si no existe |
| `ADMIN_TOKEN` | vacío | Credencial de servicio: `POST /validate` (junto con el Bearer del propietario), `POST /api/demo/reset` y consumidores del MCP. Nunca va al frontend |
| `DEMO_ADVISOR_MODE`, `DEMO_ADVISOR_TOKEN` | `0`, vacío | [Modo asesor de demostración](modo-asesor-demo.md): habilita «Validar perfil» solo en local y para clientes ficticios. El mismo token en `frontend/.env.local` |
| `DEMO_ADVISOR_CLIENTS`, `DEMO_ADVISOR_ID` | `carmen-68,carmen-corta`, `asesor-demo` | Clientes ficticios permitidos y autor de la validación en ese modo |
| `DEMO_ENDPOINTS` | `1` | `0` desactiva `POST /api/demo/reset` (para un despliegue público) |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes del front permitidos, separados por comas |
| `MCP_ALLOWED_HOSTS` | vacío | Hosts públicos del MCP (túnel o despliegue) |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID` | vacío | Voz privada: el backend crea el bootstrap firmado; sin ellas usa el agente público si el front tiene ID |
| `VOICE_USER_ID_SECRET` | desarrollo local | Seudonimiza el `client_id` enviado como `userId`; debe ser aleatorio en despliegues |
| `ELEVENLABS_WEBHOOK_SECRET` | vacío | Verifica el post-call webhook; sin él la ruta responde 503 |
| `ELEVENLABS_SERVER_LOCATION` | vacío | Opcional: `us`, `global`, `eu-residency` o `in-residency`; no implica residencia contratada |
| `ALLOW_LEGACY_SIGNED_URL` | `0` | Solo compatibilidad local con la antigua ruta sin sesión; no activar en despliegues |
| `ANTHROPIC_API_KEY` | vacío | Activa el extractor, la revisión con Claude del verificador y el modo texto. Sin clave el extractor no hace nada, el verificador solo aplica sus reglas fijas y `/chat` responde 503 |
| `MODEL_EXTRACTOR`, `MODEL_ENTREVISTADOR`, `MODEL_VERIFICADOR` | `claude-sonnet-5-5` | Modelo de Claude de cada agente |
| `VERIFICADOR_CLAUDE` | `1` | `0` apaga la revisión con Claude del verificador; sus reglas fijas siguen funcionando |
| `EFFORT_EXTRACTOR`, `EFFORT_ENTREVISTADOR`, `EFFORT_VERIFICADOR` | `low` | Esfuerzo de razonamiento (`low`…`max`): más alto, más preciso y más lento |
| `MODEL_JUEZ`, `EFFORT_JUEZ` | `claude-sonnet-5-5`, `medium` | Juez LLM de las evaluaciones; no interviene en entrevistas reales |
| `TRAZAS_ARCHIVO`, `TRAZAS_MAX` | vacío, `2000` | Trazas de LLMOps: archivo JSONL con una línea por ejecución (sin texto del cliente) y tamaño del búfer en memoria |

Variables del frontend, en `frontend/.env.local` (plantilla en `frontend/.env.example`): `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000`) y `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` (solo si el agente de voz es público).
</details>

<details>
<summary><b>Persistencia del perfil (memoria, SQLite o Postgres)</b></summary>


El backend guarda el perfil en memoria por defecto, sin base de datos. Para persistirlo:

| `PERFIL_ALMACEN` | Dónde se guarda |
|---|---|
| `memoria` (por defecto) | En memoria; con `DATA_PERSIST=1`, versiones y capa personal se vuelcan a JSON en `DATA_DIR` |
| `bd` | `DATABASE_URL`: Postgres/Supabase (Session pooler, puerto 5432), o vacío = SQLite en `backend/data/perfil.db` |

Cada cambio crea una versión nueva que nunca se modifica, y en Postgres la propia base bloquea `UPDATE`, `DELETE` y `TRUNCATE` del registro. Antes de usar Postgres o Supabase hay que aplicar las migraciones: procedimiento, comprobaciones y qué hacer si algo falla en [backend/migraciones/README.md](../backend/migraciones/README.md) (desde `backend/`: `python -m app.perfil.persistencia.verificar previo`, luego `ensayo`, y `python -m app.perfil.persistencia.migrar --aplicar` solo con autorización; todos exigen `--destino host:puerto/base` y no leen el `.env` por su cuenta).

Comportamiento del backend (almacenes, validación, versionado, estados, capa personal, rechazos y códigos de error): [docs/contratos.md](contratos.md#backend-integrado-persistencia-validación-y-versionado).

Para repetir los tests también contra un Postgres **local y desechable** (nunca Supabase; se vacía en cada test, su nombre debe llevar `test` y la base debe estar marcada con `COMMENT ON DATABASE perfil_test IS 'idoneo:base-desechable-de-pruebas'`):

```bash
cd backend
TEST_POSTGRES_URL=postgresql://usuario@127.0.0.1:5432/perfil_test python -m pytest -q
```
</details>
