# Real Betis Balompié 💚

> Nombre provisional: el definitivo está por decidir.

Onboarding por voz, pensado primero para móvil, que convierte el test MiFID en un **perfil de cliente verificado**. Cada dato enlaza con el fragmento de la entrevista que lo justifica, y el sistema detecta cuándo el cliente declara saber algo que luego no demuestra. El perfil cubre **idoneidad y conveniencia** y se sirve por API y por **MCP** a los agentes de la entidad (GPTadvisor, Claude con el conector de MyInvestor…).

**Qué no hace:** no recomienda productos. Calcula los límites que cualquier propuesta debe respetar (riesgo máximo, familias de producto convenientes, liquidez); qué productos ofrecer lo decide el agente de la entidad, y un asesor valida el perfil antes de que se pueda usar.

Proyecto para Hack Finance UC3M 2026. **Todos los datos de clientes son simulados** (la clienta de ejemplo es Carmen, 68 años).

## Probarlo en 10 minutos

### 1. Requisitos

- Python 3.11 o superior (probado con 3.13 y 3.14).
- Node.js 20 o superior, solo para el frontend (probado con 22).
- Git.

### 2. Instalar y arrancar el backend

Windows (PowerShell):

```powershell
git clone https://github.com/fernanrama/hack-finance-uc3m-2026
cd hack-finance-uc3m-2026
copy .env.example .env
cd backend
python -m venv .venv
.venv\Scripts\activate        # si falla: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

macOS / Linux:

```bash
git clone https://github.com/fernanrama/hack-finance-uc3m-2026
cd hack-finance-uc3m-2026
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Sin rellenar nada del `.env` funciona todo menos la voz. Al arrancar se carga a Carmen.

### 3. Arrancar el frontend (otra terminal)

```bash
cd frontend
npm install
cp .env.example .env.local      # Windows: copy .env.example .env.local
npm run dev
```

### 4. Recorrido de prueba

| Paso | Dónde | Qué se ve |
|---|---|---|
| 1 | http://localhost:3000 | La entrada a la feature dentro de la app (maqueta) |
| 2 | http://localhost:3000/onboarding/entrevista → «Ver demo guiada» | La entrevista de Carmen turno a turno, con subtítulos y barra de bloques |
| 3 | http://localhost:3000/entidad/carmen-68 | Vista de la entidad: cada dato con fuente, confianza y cita; perfil CONSERVADOR con riesgo máximo 3 sobre 7; renta variable no conveniente porque **declaró saber mucho y no lo demostró** |
| 4 | Botón de validar en esa vista | El perfil pasa a `active` y ya se puede usar |
| 5 | http://localhost:8000/api/clients/carmen-68/constraints | Las restricciones en el formato del catálogo de MyInvestor (`usable: true` tras validar) |
| 6 | http://localhost:8000/api/clients/carmen-68/evidence/knowledge.equity_funds | La prueba: «Eso no puede pasar, el fondo es del banco.», segundos 57–61 |
| 7 | http://localhost:8000/docs | Toda la API, para probarla a mano |

Si algo se queda en un estado raro: `POST /api/demo/reset` (desde `/docs`) vuelve a cargar a Carmen como versión nueva.

### 5. Tests

```bash
cd backend
python -m pytest -q
```

Unos 160 tests en verde; los que necesitan un Postgres local se omiten si no lo hay.

## Usarlo desde Claude con MyInvestor (el final de la demo)

El backend sirve un servidor MCP en `/mcp` con 4 herramientas de solo lectura: `get_client_profile`, `get_investment_constraints`, `get_evidence` y `get_client_context`. Claude lo usa junto al conector público de MyInvestor: pide los límites de Carmen a nuestro servidor y busca en el catálogo real con ellos.

Claude necesita una URL pública. Para la demo usamos un túnel temporal desde el portátil:

1. Instala cloudflared (Windows: `winget install --id Cloudflare.cloudflared`, y abre una terminal nueva) y ejecuta `cloudflared tunnel --url http://localhost:8000`. Apunta la URL `https://xxxx.trycloudflare.com`.
2. En `.env`: `MCP_ALLOWED_HOSTS=xxxx.trycloudflare.com` (sin `https://`) y un `ADMIN_TOKEN` largo y aleatorio (`python -c "import secrets; print(secrets.token_urlsafe(32))"`). Con la URL pública, el token es obligatorio: protege la validación.
3. Arranca (o reinicia) el backend y valida a Carmen enviando la cabecera `X-Admin-Token` (desde `/docs`, o con `curl -X POST http://localhost:8000/api/clients/carmen-68/validate -H "X-Admin-Token: <token>" -H "Content-Type: application/json" -d '{"advisor_id":"asesor-demo"}'`).
4. En claude.ai: Ajustes → Conectores → Añadir conector personalizado → `https://xxxx.trycloudflare.com/mcp`. Activa también el conector de MyInvestor (`https://mcp.myinvestor.es/mcp`).
5. En un chat nuevo: «Busca en MyInvestor fondos que encajen con la clienta carmen-68».

Probado el 9/11/2026: Claude recibe por la URL pública el perfil activo de Carmen y encuentra fondos de renta fija y monetarios en EUR con riesgo ≤ 3, ninguno de renta variable. Detalles en [backend/app/mcp/README.md](backend/app/mcp/README.md).

**Nuestro backend nunca llama al MCP de MyInvestor**: sus [términos](https://mcp.myinvestor.es/terms) solo permiten usarlo como conector en una conversación. Con `ADMIN_TOKEN` definido, el botón de validar del frontend todavía no envía la cabecera; para la demo, valida como en el paso 3.

## Estado

| Pieza | Estado |
|---|---|
| Perfil versionado, evidencias, validación de la entidad y persistencia (memoria, SQLite o Postgres) | Hecho y con tests |
| Idoneidad, conveniencia y restricciones calculadas con código (no con el modelo) | Hecho; los umbrales son **supuestos del equipo**, pendientes de revisión |
| Servidor MCP y conexión con Claude + MyInvestor | Hecho y probado con túnel |
| Frontend móvil: entrevista, demo guiada, perfil del cliente y vista de la entidad | Hecho |
| Extractor (de la conversación al perfil, con Claude) | **En desarrollo**: mientras tanto el perfil de Carmen viene de un fixture simulado |
| Verificador con Claude y resumen para agentes | Reglas deterministas hechas; versión con Claude en desarrollo |
| Voz con ElevenLabs | Integrado en código; **sin probar con cuenta real** |
| Medición de impacto (aciertos, alertas, latencia, coste) | Pendiente |

## Configuración

`.env` va en la raíz del repo (plantilla en `.env.example`). Nunca se sube a Git. Arranca el backend desde `backend/`: las rutas relativas (`DATA_DIR=./data`) se resuelven desde ahí y `backend/data/` está ignorada por Git.

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
| `ANTHROPIC_API_KEY`, `MODEL_EXTRACTOR`, `MODEL_VERIFICADOR` | vacío / modelos de Claude | Para los agentes con Claude (extractor y verificador), cuando estén integrados |

Variables del frontend, en `frontend/.env.local` (plantilla en `frontend/.env.example`): `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000`) y `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` (solo si el agente de voz es público).

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

## Estructura

| Ruta | Contenido |
|---|---|
| `backend/` | API FastAPI: perfil versionado (`app/perfil/`), cálculos deterministas (`calculos.py`), agentes (`app/agentes/`), MCP (`app/mcp/`), migraciones y tests |
| `frontend/` | Feature móvil Next.js: onboarding por voz ([detalles](frontend/README.md)) |
| `docs/` | Idea y contrato del perfil ([docs/proyecto/](docs/proyecto/README.md)), cómo lo implementa el código ([CONTRATOS.md](docs/CONTRATOS.md)), diseño y reparto |
| `gestion/` | Organización del hackathon: análisis del reto, pitch, demo y archivo |
