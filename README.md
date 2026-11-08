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

## Configuración

Copia `.env.example` a `.env` y rellena las claves en local. No subas nunca `.env`.
