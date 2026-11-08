# Idóneo

Onboarding por voz, pensado primero para móvil, que convierte el test MiFID en un **perfil de cliente verificado**: cada dato enlaza con el fragmento de la entrevista que lo justifica, y se detecta cuándo el cliente declara saber algo que luego no demuestra. El perfil se sirve por API y MCP a los agentes de la entidad (GPTadvisor, Claude…), que lo usan, por ejemplo, para filtrar el catálogo real de MyInvestor. Idóneo no recomienda productos.

Proyecto para Hack Finance UC3M 2026. **Estado: en desarrollo (v0).** Este README se completará como README de entrega.

## Estructura

| Ruta | Contenido |
|---|---|
| `backend/` | API FastAPI, perfil versionado, cálculos deterministas, agentes y MCP |
| `frontend/` | App móvil Next.js (pendiente) |
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

## Configuración

Copia `.env.example` a `.env` y rellena las claves en local. No subas nunca `.env`.
