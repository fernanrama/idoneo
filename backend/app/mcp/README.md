# MCP del perfil (rol D)

Servidor MCP remoto con transporte HTTP ("streamable"), montado en la propia API en **`/mcp`**. Código: [`servidor.py`](servidor.py). Especificación: [`docs/proyecto/04_CONTRATO_PERFIL.md`](../../../docs/proyecto/04_CONTRATO_PERFIL.md), sección "Herramientas MCP y API REST".

| Herramienta | Entrada | Devuelve |
|---|---|---|
| `get_client_profile` | `client_id`, `version?` | Perfil completo (cada dato con fuente, confianza, evidencias y flags), idoneidad, conveniencia, alertas y `usable` |
| `get_investment_constraints` | `client_id` | `funds_query`, `portfolios_query`, `post_filters`, `appropriateness`, `rationale`, `usable` |
| `get_evidence` | `client_id`, `field` | Cita, segundos y clip del dato; si el campo no existe, la lista de campos válidos |
| `get_client_context` | `client_id` | Resumen de ≤150 palabras para otro agente |

Reglas: solo lectura; leen el perfil `active` más reciente y, si no hay, el último con `usable: false`; los errores vuelven como JSON legible (`not_found`, `unknown_field`), no como excepción. Las instrucciones del servidor le dicen al agente que no recomiende nada si `usable` es false.

## Probarlo en local

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
# otra terminal: inspector oficial de MCP (requiere Node)
npx @modelcontextprotocol/inspector   # URL: http://localhost:8000/mcp · transporte: Streamable HTTP
```

Tests: `pytest tests/test_mcp.py`. Probado el 8/11 con el cliente MCP de Python contra uvicorn: inicializa, lista las 4 herramientas y devuelve las restricciones de Carmen (`usable: false` hasta que el asesor valida). Un `Host` no permitido recibe 421.

## Conectarlo en Claude (demo)

Claude necesita una URL pública HTTPS. Para pruebas, un túnel temporal desde el portátil:

```bash
cloudflared tunnel --url http://localhost:8000      # da https://<algo>.trycloudflare.com
# en .env:  MCP_ALLOWED_HOSTS=<algo>.trycloudflare.com   y reiniciar uvicorn
```

En Claude: Ajustes → Conectores → Añadir conector personalizado → `https://<algo>.trycloudflare.com/mcp`. Activar también el conector de MyInvestor (`https://mcp.myinvestor.es/mcp`).

La URL estable (despliegue) está pendiente: contratar o usar un servicio requiere la autorización del equipo.

**Ojo:** la URL del túnel es pública. Solo con datos simulados (Carmen). Antes de exponer perfiles reales hace falta autenticación (OAuth del conector), que no está hecha.

## MyInvestor: lo que se ha comprobado

Detalle en [`docs/proyecto/05_MCP_MYINVESTOR.md`](../../../docs/proyecto/05_MCP_MYINVESTOR.md). Resumen:

- 12 herramientas. `search_funds` filtra por `max_risk` (SRRI 1-7), `asset_type`, `esg_only` (art. 8 y 9), `max_ter` y `currency`; máximo 10 resultados sin paginación. Horizonte, liquidez, mínimos y exclusiones solo se pueden comprobar después, sobre la ficha (`post_filters`).
- Los ETF no tienen SRRI.
- **Sus términos prohíben llamarlo desde código** (backend, scripts, cachés) sin permiso de MyInvestor. Por eso este backend **nunca** lo llama: es el agente (Claude con los dos conectores) quien pasa `funds_query` a MyInvestor en la conversación.
