# Contratos v0 — Idóneo

Lo que comparten los cuatro módulos. **El código manda:** `backend/app/perfil/modelos.py` es la fuente de verdad del esquema; este documento lo explica. Cambiar un contrato = PR pequeña que avisa a los demás antes de fusionar.

Estado: v0 del 8/11, probado con `pytest` (5 tests) y arrancando la API en local. Agentes con stub, MCP y front pendientes.

## 1. Flujo completo

```
[móvil: voz/texto]──turnos──▶ POST /api/sessions/{sid}/turns
                                     │ (en segundo plano)
                                     ▼
                         extractor ──▶ store.aplicar()  ──▶ nueva versión del perfil
                         verificador ─▶ store.anadir_alertas()
                                     │
       panel de perfil ◀── GET /api/clients/{cid}/profile (sondeo cada 1–2 s en v0)
       asesor ──────────▶ POST /api/clients/{cid}/profile/validate  → status=active
                                     │
       Claude (conector MCP Idóneo + conector MCP MyInvestor)
         get_investment_constraints ──▶ filtra el catálogo de MyInvestor
```

## 2. Perfil

Cada dato es un **Campo**:

| Atributo | Significado |
|---|---|
| `value` | Valor vigente (si hay contradicción, el **demostrado**) |
| `source` | `declared` (lo dijo) · `demonstrated` (lo probó al responder) · `calculated` (función Python) · `advisor` (corrección humana) |
| `declared` | Lo que dijo, si difiere de `value` |
| `confidence` | 0–1, solo para declared/demonstrated |
| `evidence[]` | `{session_id, t_start, t_end, quote}`: segundos desde el inicio de la sesión y cita literal |
| `inputs[]` | Campos de los que sale un valor calculado |
| `flags[]` | p. ej. `declared_vs_demonstrated` |
| `updated_by` | `extractor` · `verificador` · `calculo` · `asesor` · `fixture` |

**Perfil:** `client_id`, `version`, `status` (`draft` → `validated` → `active` → `review_pending`), `reason` (motivo de la versión), `mifid{campo: Campo}`, `personal{}` (fuera del MVP), `alerts[]`, `review{validated_by, validated_at, next_review}`.

Reglas: nunca se sobrescribe (cada escritura crea versión); solo `active` es apto para recomendar; un cambio no hecho por el asesor sobre un perfil validado lo pasa a `review_pending`.

### Campos MiFID del MVP (lista cerrada)

| Campo | Tipo | Oblig. | Cómo se obtiene |
|---|---|:-:|---|
| `consent.recording` | bool | ✔ | Pregunta inicial |
| `consent.ai_notice` | bool | ✔ | Aviso de IA al empezar |
| `knowledge.investment_funds` | none/basic/medium/high | ✔ | Declarado + pregunta de comprobación |
| `knowledge.equity_risk` | none/basic/medium/high | ✔ | Declarado + "¿qué pasa si cae un 20 %?" |
| `experience.past_investments` | texto | | Declarado |
| `financial.monthly_income_eur` | número | ✔ | Declarado |
| `financial.monthly_fixed_costs_eur` | número | ✔ | Declarado |
| `financial.liquid_savings_eur` | número | ✔ | Declarado |
| `financial.debts_eur` | número | ✔ | Declarado |
| `financial.emergency_fund_eur` | número | | **Calculado**: 6 × gastos fijos |
| `financial.loss_capacity_eur` | número | | **Calculado**: max(0, ahorro − colchón − deudas) |
| `objective.goal` | texto | ✔ | Declarado |
| `objective.amount_eur` | número | | Declarado |
| `objective.horizon_years` | número | ✔ | Declarado |
| `risk.reaction_to_drop` | texto | | Escenario |
| `risk.tolerance` | low/medium/high | ✔ | Demostrado por escenario |
| `sustainability.preference` | none/some/strong | ✔ | Tras explicarlo con ejemplos |
| `sustainability.explained` | bool | | |
| `exclusions.sectors` | lista | | Declarado |

Las fórmulas y topes son **supuestos del equipo v0**, no fórmulas regulatorias: revisarlos con tutoría y decirlo así en el pitch.

## 3. Restricciones (`get_investment_constraints`)

`{client_id, profile_version, eligible, missing_fields[], max_risk_indicator (SRI 1–7), horizon_years, loss_capacity_eur, liquidity_need, esg_required, exclusions[], rationale[]}`

`max_risk_indicator` = mínimo de tres topes (`backend/app/perfil/calculos.py`):
- tolerancia: low 3 · medium 5 · high 7
- plazo: <2 años 2 · <5 4 · <8 6 · resto 7
- conocimiento demostrado más bajo: none 2 · basic 3 · medium 5 · high 7

SRI = indicador de riesgo 1–7 del documento KID de cada producto (normativa PRIIPs). **Pendiente (Dev D):** comprobar qué campo equivalente expone el MCP de MyInvestor.

## 4. API REST (`backend/app/main.py`, docs en `/docs`)

| Método y ruta | Uso | Estado |
|---|---|---|
| `GET /api/health` | Comprobación | ✔ |
| `POST /api/sessions` `{client_id?}` | Empieza entrevista → `{session_id, client_id, started_at}` | ✔ |
| `POST /api/sessions/{sid}/turns` `{speaker: agent\|client, text, t_start, t_end}` | El front envía cada turno de la transcripción; dispara extractor y verificador | ✔ (agentes stub) |
| `GET /api/sessions/{sid}` | Sesión y turnos | ✔ |
| `GET /api/clients/{cid}/profile[?version=n]` | Perfil vigente o una versión | ✔ |
| `GET /api/clients/{cid}/profile/versions` | Historial | ✔ |
| `POST /api/clients/{cid}/profile/validate` `{advisor_id, corrections[]}` | El asesor corrige y activa | ✔ |
| `GET /api/clients/{cid}/constraints` | Restricciones | ✔ |
| `GET /api/clients/{cid}/evidence/{field}` | Cita y tiempos de un dato | ✔ |
| `GET /api/clients/{cid}/context` | Resumen para otro agente | ✔ (plantilla) |
| `POST /api/demo/reset` | Recarga a Carmen (datos simulados) | ✔ |
| `GET /api/voice/signed-url` | URL firmada de ElevenLabs; la clave no sale del backend. 503 si no está configurada | ✔ (sin probar con cuenta real) |
| `GET /api/sessions/{sid}/events` (SSE) | Avisos en vivo al front | Pendiente, Dev A; v0 = sondeo |
| `GET /api/sessions/{sid}/audio` | Audio de la sesión para reproducir evidencias | Pendiente, Dev A + C según prueba de voz |
| `POST /api/sessions/{sid}/chat` `{text}` | Modo texto sin ElevenLabs | Pendiente, Dev B |

## 5. Agentes (`backend/app/agentes/`, Dev B)

```python
async def extraer(turnos: list[Turno], perfil: Perfil, session_id: str) -> list[ActualizacionCampo]
async def verificar(perfil: Perfil, turnos: list[Turno]) -> list[Alerta]
async def resumen(perfil: Perfil) -> str
```
- El extractor **no escribe campos calculados**; el store los recalcula.
- Toda actualización lleva evidencia del turno del cliente.
- El prompt del entrevistador (el que usa ElevenLabs) se versiona en `backend/app/agentes/prompts/entrevistador.md`.

## 6. MCP de Idóneo (`backend/app/mcp/`, Dev D)

Servidor remoto HTTP, montado en el mismo backend en `/mcp`. Llama directamente a `store` y `calculos`, no a la API.

| Herramienta | Devuelve |
|---|---|
| `get_client_profile(client_id)` | Perfil vigente |
| `get_investment_constraints(client_id)` | Restricciones (§3) |
| `get_evidence(client_id, field)` | Cita y tiempos |
| `get_client_context(client_id)` | Resumen para el modelo |

## 7. Variables de entorno

Ver `.env.example`. Nunca subir `.env`. Solo nombres en documentos.
