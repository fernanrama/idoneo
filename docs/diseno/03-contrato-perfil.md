# Contrato del perfil de cliente

8 nov 2026 · Alejandro (Alex)

> Copia en el repo del documento vivo [Contrato del perfil de cliente](https://claude.ai/artifact/7LmxGm3ECZUbKU1BZMWAHj). Si cambia allí, hay que actualizar esta copia (o al revés). Versión 0.1: borrador para revisar con las piezas de front, agentes y backend.

## Alcance y principios

El producto solo crea perfiles: recoge, comprueba y versiona la información MiFID del cliente y la sirve a otros agentes. No recomienda, no filtra catálogos y no genera informes para banqueros ni clientes.

| Consumidor | Qué hace con el perfil | Test MiFID que usa |
| --- | --- | --- |
| Agente de GPTadvisor (asesoramiento) | Propone productos que cumplen las restricciones y justifica la recomendación | Idoneidad |
| Carteras automatizadas de MyInvestor (gestión discrecional) | Asigna la cartera según el perfil de riesgo | Idoneidad |
| Compra sin asesoramiento en MyInvestor | Avisa si un producto no es conveniente para el cliente | Conveniencia |
| Cumplimiento de la entidad | Revisa el expediente en una inspección | Registro (arts. 72–73 Reg. Delegado 2017/565) |

Cinco reglas que todo el equipo respeta:

1. El perfil es la única fuente de verdad. Los agentes escriben en él y todas las salidas leen de él.
2. Ningún número lo pone el modelo. La pérdida asumible, el horizonte y las puntuaciones salen de funciones deterministas.
3. Nada se sobrescribe. Cada cambio crea una versión nueva con su motivo.
4. Cada dato lleva su fuente y, si sale de la conversación, su prueba de audio.
5. La capa MiFID y la capa personal se guardan por separado, con base legal distinta.

## Modelo de un dato

Cada campo del perfil es un objeto `Fact` con el mismo formato. Eso es lo que lo diferencia de un formulario.

```json
{
  "value": "low",
  "declared": "high",
  "source": "demonstrated",
  "confidence": 0.86,
  "confidence_basis": "rubric:knowledge.equity_funds:v1",
  "evidence": [
    {"session_id": "s-0142", "turn_id": "t-031", "t": [212.4, 219.8],
     "quote": "eso no puede pasar, el fondo es del banco",
     "audio_url": "/api/evidence/s-0142/t-031.mp3"}
  ],
  "flags": ["declared_vs_demonstrated"],
  "updated_at": "2026-11-08T10:12:00Z",
  "updated_by": "agent:extractor"
}
```

| Campo | Tipo | Regla |
| --- | --- | --- |
| `value` | según el campo | Valor vigente; `null` si aún no se sabe |
| `declared` | opcional | Lo que dijo el cliente, solo si difiere de `value` |
| `source` | `declared` \| `demonstrated` \| `calculated` \| `advisor` | `calculated` solo desde funciones deterministas; `advisor` cuando lo corrige alguien de la entidad |
| `confidence` | 0–1 | Sale de una rúbrica fija (respuestas correctas sobre preguntas de comprobación), nunca de la opinión del modelo |
| `confidence_basis` | texto | Qué rúbrica y versión la produjo, para poder explicarla |
| `evidence` | lista | Turno de conversación, segundos en la grabación, cita literal y clip |
| `flags` | lista | Alertas abiertas sobre este dato (ver abajo) |
| `updated_by` | texto | `agent:extractor`, `agent:verifier`, `fn:<nombre>` o `advisor:<id>` |

Alertas posibles en `flags`:

- `declared_vs_demonstrated`: lo declarado no coincide con lo demostrado.
- `inconsistent`: choca con otro dato (por ejemplo, objetivo a 1 año y tolerancia alta).
- `low_confidence`: la rúbrica no llega al mínimo y hace falta repreguntar.
- `needs_advisor`: el verificador pide revisión humana.

## Esquema completo del perfil

El perfil tiene cuatro bloques: la capa MiFID (datos de entrada), los resultados de los dos tests (calculados), la capa personal (opcional) y la revisión. Cada hoja marcada como `Fact` sigue el modelo de la sección anterior.

```json
{
  "client_id": "carmen-68",
  "version": 3,
  "status": "active",
  "created_at": "2026-11-08T10:00:00Z",
  "mifid": {
    "disclosures": {"ai_notice_ack": "Fact", "purpose_ack": "Fact"},
    "knowledge": {
      "deposits_money_market": "Fact", "fixed_income_funds": "Fact",
      "mixed_funds": "Fact", "equity_funds": "Fact",
      "etfs": "Fact", "stocks": "Fact", "complex_products": "Fact"
    },
    "experience": {
      "by_family": {"equity_funds": {"years": "Fact", "operations_last_3y": "Fact"}},
      "education": "Fact", "profession": "Fact"
    },
    "financial": {
      "net_monthly_income_eur": "Fact", "income_stability": "Fact",
      "fixed_monthly_costs_eur": "Fact", "liquid_savings_eur": "Fact",
      "other_assets_eur": "Fact", "debts_eur": "Fact",  // debts_eur: sin la hipoteca de la vivienda
      "mortgage_eur": "Fact",  // opcional: hipoteca pendiente; no resta en loss_capacity_eur
      "emergency_fund_months": "Fact", "loss_capacity_eur": "Fact"
    },
    "objectives": [
      {"id": "o1", "goal": "Fact", "amount_eur": "Fact", "horizon_years": "Fact",
       "liquidity_need": "Fact", "priority": 1}
    ],
    "risk_tolerance": {"scenario_score": "Fact", "max_drawdown_accepted_pct": "Fact", "past_behaviour": "Fact"},
    "sustainability": {"preference": "Fact", "min_sfdr_article": "Fact", "explained": "Fact"}
  },
  "assessments": {
    "suitability": {
      "complete": true, "missing": [],
      "risk_profile": "CONSERVADOR", "max_sri": 3,
      "rationale_ids": ["knowledge.equity_funds", "financial.loss_capacity_eur"]
    },
    "appropriateness": {
      "equity_funds": "not_appropriate", "fixed_income_funds": "appropriate",
      "complex_products": "not_appropriate"
    }
  },
  "personal": {
    "consent": {"given": true, "at": "2026-11-08T10:01:00Z"},
    "life_stage": {}, "retirement": {}, "held_elsewhere": [], "tax": {},
    "exclusions": ["armas", "tabaco"],
    "communication": {"channel": "whatsapp", "format": "audio", "detail": "low", "language": "es"},
    "concerns": []
  },
  "review": {"validated_by": "asesor-07", "validated_at": "2026-11-08T10:20:00Z", "next_review": "2027-11-08", "open_flags": 0}
}
```

Cómo se calculan los dos resultados:

| Resultado | De qué sale | Quién lo calcula |
| --- | --- | --- |
| `suitability.complete` | Todos los campos obligatorios con valor y sin `low_confidence` | Función determinista |
| `suitability.risk_profile` | Tolerancia por escenarios, capacidad de pérdida y horizonte; manda el más restrictivo | Función determinista |
| `suitability.max_sri` | Tabla fija de `risk_profile` a SRI 1–7 | Función determinista |
| `appropriateness.<familia>` | Conocimiento demostrado y experiencia de esa familia de productos | Función determinista |

El verificador (Opus) no calcula estos resultados: solo marca alertas y propone repreguntas. Así cualquier resultado se puede explicar sin abrir el modelo.

## Estados y versiones

Solo un perfil en estado `active` se sirve como apto para recomendar. Los demás estados se pueden leer, pero las restricciones vuelven con `usable: false`.

| Estado | Significa | Pasa a | Lo dispara |
| --- | --- | --- | --- |
| `draft` | Entrevista en curso o incompleta | `pending_validation` | `suitability.complete` = true y sin alertas `needs_advisor` |
| `pending_validation` | Completo, falta la revisión humana | `active` o `draft` | El asesor valida, o corrige y pide repreguntar |
| `active` | Validado y vigente | `review_due` | Llega `next_review` o se registra un evento vital |
| `review_due` | Hay que actualizar algo | `draft` | Empieza una entrevista corta solo sobre lo que cambió |

Reglas de versiones:

- Tabla de solo añadir `profile_versions(client_id, version, snapshot_json, reason, author, created_at)`. Nada se actualiza ni se borra.
- Cada cambio de estado o de un `Fact` crea versión nueva con `reason` (por ejemplo `advisor_correction`, `life_event:herencia`).
- La capa `personal` vive en otra tabla con su propia versión, para poder borrarla por el RGPD sin tocar el registro MiFID.
- La grabación y la transcripción de cada sesión se guardan aparte y se enlazan por `session_id`.

## Restricciones para consumidores

`get_investment_constraints` devuelve las reglas en el idioma del consumidor: parámetros que se pasan tal cual al MCP de MyInvestor y una lista de filtros posteriores sobre la ficha. Nosotros no filtramos nada; el agente de la entidad sí.

```json
{
  "client_id": "carmen-68", "profile_version": 3, "usable": true,
  "funds_query": {"max_risk": 3, "esg_only": true, "currency": "EUR",
                  "asset_type": ["Renta Fija", "Monetario"]},
  "portfolios_query": {"risk_max": 1, "profile": "CONSERVADOR"},
  "post_filters": [
    {"field": "redemption_lag_days", "op": "<=", "value": 3, "why": "liquidity_need"},
    {"field": "fixed_income_term", "op": "in", "value": ["Corto plazo"], "why": "horizon_years"},
    {"field": "sustainability_article", "op": ">=", "value": 8, "why": "sustainability"},
    {"field": "top_sectors", "op": "not_contains", "value": ["Defensa", "Tabaco"], "why": "exclusions"},
    {"field": "min_initial", "op": "<=", "value": 20000, "why": "objectives.o1.amount_eur"}
  ],
  "appropriateness": {"equity_funds": "not_appropriate", "etfs": "not_appropriate", "stocks": "not_appropriate"},
  "evidence_refs": ["knowledge.equity_funds", "financial.loss_capacity_eur"]
}
```

| Restricción del perfil | Parámetro en MyInvestor | Cómo |
| --- | --- | --- |
| Riesgo máximo (`max_sri`) | `search_funds.max_risk` (SRRI 1–7) | Directo |
| Perfil de riesgo | `search_portfolios.profile` y `risk_max` (0–5) | Directo, con una tabla fija de equivalencias |
| Preferencia ESG | `esg_only` (artículo 8 o 9) | Directo; si pide artículo 9, filtro posterior por `sustainability_article` |
| Divisa | `currency` | Directo |
| Familias no convenientes | `asset_type` (se quitan) | Directo para fondos; en ETF y acciones el agente avisa en vez de filtrar |
| Liquidez | `redemption_lag_days`, `cutoff_time` | Solo filtro posterior |
| Horizonte | No existe | Aproximado con SRRI, tipo Monetario y `fixed_income_term` |
| Exclusiones sectoriales | `top_sectors` | Solo filtro posterior y solo sector principal: no hay posiciones |
| Importe mínimo | Mínimos de la ficha | Solo filtro posterior |

Límites del MCP de MyInvestor que el consumidor debe conocer: 10 resultados como máximo, sin paginación, y sus términos solo permiten uso conversacional (como conector en Claude) salvo permiso expreso. Los ETF no tienen SRI, solo volatilidad.

## Eventos entre front, voz y backend

El móvil habla con ElevenLabs por su SDK y reenvía cada frase al backend. El backend contesta al móvil por SSE con los cambios del perfil. ElevenLabs habla con el backend por herramientas de servidor y por el webhook de fin de llamada.

| Evento | De → a | Payload mínimo | Para qué |
| --- | --- | --- | --- |
| `session.start` | Front → API (`POST /sessions`) | `client_id`, `channel` (voz o texto) | Crea `session_id` y devuelve la URL firmada de ElevenLabs |
| `turn.user` | Front → API (`POST /sessions/{id}/turns`) | `turn_id`, `text`, `ts_client` (del `user_transcript` del SDK) | Lanza el extractor |
| `turn.agent` | Front → API | `turn_id`, `text` (del `agent_response`) | Contexto para el extractor |
| `profile.patch` | API → Front (SSE `/sessions/{id}/stream`) | `path`, `fact`, `version` | Rellenar el panel en directo |
| `flag.raised` | API → Front (SSE) | `path`, `flag`, `message` | Mostrar la alerta de declarado frente a demostrado |
| `agent.hint` | API → ElevenLabs (herramienta de servidor `get_next_focus`) | `next_block`, `reask` | Que el agente de voz sepa qué falta y qué repreguntar |
| `session.ended` | ElevenLabs → API (webhook de fin de llamada) | `conversation_id`, transcripción con segundos por turno | Enlazar cada `turn_id` con sus segundos y recortar los clips |
| `profile.status` | API → Front (SSE) | `status`, `missing` | Barra de bloques completados y paso a validación |

Pendiente de probar el día 1: que los turnos del SDK y los del webhook se puedan casar por orden o por texto. Si no, las pruebas de audio se enlazan al terminar la llamada y en directo solo se muestra la cita.

## Herramientas MCP y API REST

El MCP y la API leen lo mismo: el perfil `active` más reciente. Si no hay perfil activo, responden con el estado y `usable: false` en vez de un error.

| Herramienta MCP | Entrada | Devuelve |
| --- | --- | --- |
| `get_client_profile` | `client_id`, `version?` | El perfil completo con fuente, confianza y alertas de cada dato |
| `get_investment_constraints` | `client_id` | El objeto de la sección de restricciones |
| `get_evidence` | `client_id`, `field` | Citas, segundos y URL del clip que justifican ese dato |
| `get_client_context` | `client_id` | Resumen de 150 palabras como máximo, escrito para otro agente |

| Endpoint REST | Uso |
| --- | --- |
| `POST /sessions` | Empezar entrevista |
| `POST /sessions/{id}/turns` | Reenviar un turno |
| `GET /sessions/{id}/stream` | SSE con los cambios del perfil |
| `POST /webhooks/elevenlabs` | Fin de llamada |
| `GET /clients/{id}/profile` | Perfil activo; `?version=` para uno anterior |
| `GET /clients/{id}/versions` | Historial con motivo y autor |
| `POST /clients/{id}/validate` | El asesor valida o corrige (`changes[]`) |
| `GET /clients/{id}/dossier.pdf` | Expediente de idoneidad para cumplimiento |
| `GET /api/evidence/{session}/{turn}.mp3` | Clip de audio de una prueba |

El MCP se publica en una URL pública con transporte HTTP, igual que el de MyInvestor, para conectarlo como conector personalizado en Claude.

## Decisiones abiertas para el equipo

- [ ] Lista de familias de producto para conocimiento y conveniencia: ¿bastan las 7 propuestas?
- [ ] Tabla de equivalencias de perfil a SRI y a `risk_max` de carteras. Hay que leer los valores exactos de `profile` con `list_facets` en MyInvestor.
- [ ] Rúbrica de confianza: preguntas de comprobación por familia y aciertos mínimos para `demonstrated`.
- [ ] Campos obligatorios para que `suitability.complete` sea true.
- [ ] Base de datos: SQLite o Postgres/Supabase, y dónde se guarda el audio.
- [ ] Pedir permiso al jurado de MyInvestor para llamar a su MCP desde código.
- [ ] Nombre del producto, para el prefijo de las herramientas MCP.
