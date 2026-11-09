# Real Betis Balompié 💚

Onboarding por voz, pensado primero para móvil, que convierte el test MiFID en un **perfil de cliente verificado**: cada dato enlaza con el fragmento de la entrevista que lo justifica, y se detecta cuándo el cliente declara saber algo que luego no demuestra. El perfil se sirve por API y MCP a los agentes de la entidad (GPTadvisor, Claude…), que lo usan, por ejemplo, para filtrar el catálogo real de MyInvestor. Idóneo no recomienda productos.

Proyecto para Hack Finance UC3M 2026. **Estado: en desarrollo (v0).** Este README se completará como README de entrega.

## Estructura

| Ruta | Contenido |
|---|---|
| `backend/` | API FastAPI, perfil versionado, cálculos deterministas, agentes y MCP |
| `frontend/` | Feature móvil Next.js: onboarding por voz ([cómo arrancar](frontend/README.md)) |
| `docs/` | [Diseño](docs/DISENO.md), [contratos](docs/CONTRATOS.md) y [reparto](docs/REPARTO.md) |
| `gestion/` | Organización del hackathon: análisis del reto, coordinación, evaluación, pitch y archivo |

## Arrancar el backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Abre http://localhost:8000/docs. Al arrancar se carga a **Carmen**, un perfil con **datos simulados**. Prueba con `GET /api/clients/carmen-68/constraints`.

Tests: `cd backend && python -m pytest -q`

## Servidor MCP

La misma API sirve un servidor MCP en **http://localhost:8000/mcp** (transporte HTTP) con 4 herramientas de solo lectura: `get_client_profile`, `get_investment_constraints`, `get_evidence` y `get_client_context`. Para usarlo en Claude junto al conector de MyInvestor hace falta una URL pública: ver [backend/app/mcp/README.md](backend/app/mcp/README.md). El backend nunca llama al MCP de MyInvestor; eso lo hace el agente en la conversación, como permiten sus términos.

## Arrancar el frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Abre http://localhost:3000. Prueba la «demo guiada» en `/onboarding/entrevista` y la vista de la entidad en `/entidad/carmen-68`.

## Persistencia del perfil

El backend guarda el perfil en memoria por defecto, sin base de datos. Para persistirlo:

| `PERFIL_ALMACEN` | Dónde se guarda |
|---|---|
| `memoria` (por defecto) | En memoria; con `DATA_PERSIST=1`, versiones y capa personal se vuelcan a JSON en `DATA_DIR` |
| `bd` | `DATABASE_URL`: Postgres/Supabase (Session pooler, puerto 5432), o vacío = SQLite en `backend/data/perfil.db` |

Cada cambio crea una versión nueva que nunca se modifica, y en Postgres la propia base bloquea `UPDATE`, `DELETE` y `TRUNCATE` del registro. Antes de usar Postgres o Supabase hay que aplicar las migraciones: procedimiento, comprobaciones y qué hacer si algo falla en [backend/migraciones/README.md](backend/migraciones/README.md) (desde `backend/`: `python -m app.perfil.persistencia.verificar previo`, luego `ensayo`, y `python -m app.perfil.persistencia.migrar --aplicar` solo con autorización).

Comportamiento del backend (almacenes, validación, versionado, estados, capa personal, rechazos y códigos de error): [docs/CONTRATOS.md](docs/CONTRATOS.md#backend-integrado-persistencia-validación-y-versionado).

Para repetir los tests también contra un Postgres **local y desechable** (nunca Supabase; se vacía en cada test y su nombre debe llevar `test`):

```bash
cd backend
TEST_POSTGRES_URL=postgresql://usuario@127.0.0.1:5432/perfil_test python -m pytest -q
```

## Configuración

Copia `.env.example` a `.env` y rellena las claves en local. No subas nunca `.env`. Arranca el backend desde `backend/`: las rutas relativas (`DATA_DIR=./data`) se resuelven desde ahí y `backend/data/` está ignorada por Git.

Variables del backend (todas en `.env.example`):

| Variable | Por defecto | Para qué |
|---|---|---|
| `PERFIL_ALMACEN` | `memoria` | `memoria` o `bd` (ver [Persistencia](#persistencia-del-perfil)) |
| `DATABASE_URL` | vacío | Solo con `bd`. La contraseña, solo en tu `.env` |
| `DATA_DIR` | `backend/data` | Carpeta de los volcados JSON (memoria) y de la base SQLite |
| `DATA_PERSIST` | `1` | `1` vuelca el almacén en memoria a `DATA_DIR`; `0` no escribe nada en disco (lo usan los tests) |
| `LOAD_DEMO_FIXTURE` | `1` | Carga a Carmen (DATOS SIMULADOS) al arrancar, solo si no existe |
| `ADMIN_TOKEN` | vacío | Si se define, `POST /validate` y `POST /api/demo/reset` exigen la cabecera `X-Admin-Token`. El front aún no la envía |
| `DEMO_ENDPOINTS` | `1` | `0` desactiva `POST /api/demo/reset` (para un despliegue público) |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes del front permitidos, separados por comas |
| `MCP_ALLOWED_HOSTS` | vacío | Hosts públicos del MCP (túnel o despliegue) |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID` | vacío | Voz: el backend firma la URL; sin ellas, `/api/voice/signed-url` da 503 |
