# MCP del perfil (rol D)

Servidor MCP remoto con transporte HTTP ("streamable"), montado en la propia API en **`/mcp`**. Código: [`servidor.py`](servidor.py). Especificación: [`docs/diseno/03-contrato-perfil.md`](../../../docs/diseno/03-contrato-perfil.md), sección "Herramientas MCP y API REST".

| Herramienta | Entrada | Devuelve |
|---|---|---|
| `get_client_profile` | `client_id`, `version?` | Perfil completo (cada dato con fuente, confianza, evidencias y flags), idoneidad, conveniencia, alertas y `usable` |
| `get_investment_constraints` | `client_id` | `funds_query`, `portfolios_query`, `post_filters`, `appropriateness`, `rationale`, `usable` |
| `get_evidence` | `client_id`, `field` | Cita, segundos y clip del dato; si el campo no existe, la lista de campos válidos |
| `get_client_context` | `client_id` | Resumen de ≤150 palabras para otro agente |

Reglas: solo lectura; leen el perfil `active` más reciente y, si no hay, el último con `usable: false`; los errores vuelven como JSON legible (`not_found`, `unknown_field`), no como excepción. Las instrucciones del servidor le dicen al agente que no recomiende nada si `usable` es false, y que no se apoye en las rutas de `pending_review` (datos cambiados en una versión posterior aún sin validar; ver `docs/contratos.md`). Lo incluyen `get_investment_constraints`, `get_client_profile` sin `version` y `get_client_context`.

## Probarlo en local

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
# otra terminal: inspector oficial de MCP (requiere Node)
npx @modelcontextprotocol/inspector   # URL: http://localhost:8000/mcp · transporte: Streamable HTTP
#   cabecera: Authorization: Bearer <MCP_DEMO_TOKEN>  (sin credencial responde 401)
```

Tests: `pytest tests/test_mcp.py tests/test_mcp_demo.py`. Probado el 8/11 con el cliente MCP de Python contra uvicorn: inicializa, lista las 4 herramientas y devuelve las restricciones de Carmen (`usable: false` hasta que el asesor valida). Un `Host` no permitido recibe 421.

## Prueba completa en Claude (9/11)

Hecha con un túnel de cloudflared desde un portátil del equipo, el conector añadido en Claude y Carmen validada (`active`, `usable: true`):

- Claude llamó a `get_investment_constraints` por la URL pública y recibió `max_risk: 3`, `asset_type: ["Monetario", "Renta Fija"]` y la renta variable `not_appropriate`.
- Con esos límites, en MyInvestor: 450 fondos de renta fija y 28 monetarios en EUR con SRRI ≤ 3; ninguno de renta variable.
- Detectado: el buscador de MyInvestor solo admite un `asset_type` por búsqueda. Las instrucciones del servidor piden ahora una búsqueda por valor.
- Recordatorio para el pitch: el orden y la elección de fondos es del agente de la entidad (que asesora); nosotros solo damos los límites del perfil.

## Conectarlo en Claude (pitch)

Desde la PR #21, `/mcp` exige credencial: sin ella responde 401. **Nunca se usa `ADMIN_TOKEN` en un conector**: lee a todos los clientes y abre rutas REST de escritura. Para el pitch hay dos credenciales de demostración ([`demo.py`](demo.py)), ambas de solo lectura, **solo por cabecera `Authorization: Bearer`** (nunca en la URL) y **solo desde esta máquina** (loopback, `Host` local y sin proxy; si no, 403):

| Credencial | Para | Cómo se obtiene | Vida |
|---|---|---|---|
| `MCP_DEMO_TOKEN` | Fixtures ficticios de `MCP_DEMO_CLIENTS` (por defecto `carmen-68`) | Valor aleatorio en el `.env` | Hasta que se quite del `.env` |
| Token de operador (`idoneo-demo-…`) | Un cliente ficticio nuevo concreto | `scripts/demo_operador.py autorizar <client_id> --confirmo-ficticio` | Caduca (2 h por defecto, máx. 8 h), se revoca y no sobrevive a un reinicio |

La API REST no reconoce ninguna de las dos. Las cuatro herramientas se declaran `readOnlyHint`. Si `MCP_DEMO_TOKEN` es insegura (corta, con caracteres no válidos o igual a otro secreto), queda desactivada y el log lo avisa.

**Cliente:** Claude Code en el mismo portátil. Admite cabeceras (`claude mcp add -H`; comprobado en Claude Code 2.1.322) y conecta con `localhost` sin túnel. La cabecera se registra como referencia, `-H 'Authorization: Bearer ${IDONEO_MCP_TOKEN}'` con comillas simples: `~/.claude.json` guarda la referencia y Claude Code la resuelve al conectar, así que el token no queda escrito en disco. No usamos el conector de claude.ai ni el de Claude Desktop: necesitan una URL pública y, sin cabeceras propias, el token tendría que ir en la URL.

El recorrido completo, con Carmen o con un cliente nuevo entrevistado en directo, está en [docs/modo-asesor-demo.md](../../../docs/modo-asesor-demo.md#recorrido-completo-del-pitch).

### Test de contrato

`pytest tests/test_mcp_demo.py tests/test_demo_operador.py`: configuración, rechazos, solo local, el protocolo completo contra un uvicorn local en un puerto efímero (con el cliente MCP oficial) y el recorrido «cliente nuevo → entrevista → operador → asesor → MCP», incluidos caducidad, revocación y reinicio. Sin servicios externos y con las claves de proveedores vacías.

## MyInvestor: lo que se ha comprobado

Detalle en [`docs/diseno/04-mcp-myinvestor.md`](../../../docs/diseno/04-mcp-myinvestor.md). Resumen:

- 12 herramientas. `search_funds` filtra por `max_risk` (SRRI 1-7), `asset_type`, `esg_only` (art. 8 y 9), `max_ter` y `currency`; máximo 10 resultados sin paginación. Horizonte, liquidez, mínimos y exclusiones solo se pueden comprobar después, sobre la ficha (`post_filters`).
- Los ETF no tienen SRRI.
- **Sus términos prohíben llamarlo desde código** (backend, scripts, cachés) sin permiso de MyInvestor. Por eso este backend **nunca** lo llama: es el agente (Claude con los dos conectores) quien pasa `funds_query` a MyInvestor en la conversación.
