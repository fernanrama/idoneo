# Contrato v1: cómo lo implementa el código

**La especificación es [`docs/proyecto/04_CONTRATO_PERFIL.md`](proyecto/04_CONTRATO_PERFIL.md) (Alex).** Este documento no la repite: dice qué parte está implementada, dónde y en qué se desvía. El código de referencia es `backend/app/perfil/modelos.py` (esquema) y `calculos.py` (resultados). Cambiar el contrato = PR pequeña avisada al equipo.

Estado (8/11, rama `feat/contrato-unificado`): backend v1 con 11 tests en verde; frontend adaptado (tipos, lint y compilación en verde). Pendiente de revisión por **Alex** (especificación) y **Juan** (backend).

## Qué se ha unificado

| Tema | Antes (v0, código) | Ahora (v1) | Origen |
|---|---|---|---|
| Alcance | Solo idoneidad | **Idoneidad y conveniencia** (`assessments.suitability` y `assessments.appropriateness`) | Alex (D2) |
| Dato | `Campo` con `t_start/t_end` | `Fact` con `confidence_basis`, evidencia con `turn_id`, `t: [inicio, fin]` y `audio_url` | Alex |
| Autor | Enum (`extractor`, `asesor`…) | Texto: `agent:extractor`, `agent:verifier`, `fn:<nombre>`, `advisor:<id>` | Alex |
| Flags | Libres | `declared_vs_demonstrated`, `inconsistent`, `low_confidence`, `needs_advisor` | Alex |
| Estados | `draft/validated/active/review_pending` | `draft → pending_validation → active → review_due` (transiciones en `store.py`) | Alex |
| Campos | Lista propia | Rutas de Alex: `knowledge.<familia>` (7 familias), `financial.*`, `objectives.o1.*`, `risk_tolerance.*`, `sustainability.*`, `disclosures.*` | Alex |
| Restricciones | SRI máximo propio | Formato de MyInvestor: `funds_query`, `portfolios_query`, `post_filters`, `appropriateness`, `usable` | Alex + hallazgos del MCP |
| Lectura para consumidores | Último perfil | Último **activo**; si nunca hubo uno, el último con `usable: false` | Alex |
| Números | Python | Python, igual. Ahora también el perfil de riesgo y la conveniencia | Ambos |
| Prefijo de rutas | `/api` | Se mantiene `/api` (ver desviaciones) | Código |

## Desviaciones conscientes (a confirmar)

1. **`mifid` es un mapa plano de rutas** (`"knowledge.equity_funds": Fact`) en lugar del JSON anidado. Es equivalente, facilita los parches (`profile.patch` ya usa `path`) y el extractor solo tiene que devolver `path` + valor.
2. **Rutas REST con prefijo `/api`** (`/api/clients/{id}/validate`…), para poder servir front y API desde el mismo dominio. Los nombres son los de Alex.
3. **`GET /api/clients/{id}/profile` devuelve la última versión en cualquier estado**, porque el front la necesita durante la entrevista. El "solo activo" se aplica en `constraints`, `context` y el MCP.
4. **Se añade `alerts[]` a nivel de perfil** con el texto legible de cada flag (lo que el evento `flag.raised` lleva como `message`). El flag sigue también en el `Fact`.
5. **Se añade `rationale[]`** (texto) junto a `rationale_ids` en idoneidad y restricciones, para la vista de la entidad y para explicarlo al jurado.
6. **La URL firmada de ElevenLabs va en `GET /api/voice/signed-url`**, no en la respuesta de `POST /sessions`, para que la sesión funcione también sin voz (modo texto y demo guiada).
7. **`emergency_fund_months` es calculado**: meses de gastos fijos que cubre el ahorro líquido.

## Decisiones abiertas del contrato: propuesta implementada

Están en el código como **supuestos v1**, marcados con `[ABIERTO]` en `calculos.py`. Se pueden cambiar sin tocar nada más.

| Decisión abierta | Propuesta implementada |
|---|---|
| Familias de producto | Las 7 de Alex. Las 4 de fondos se traducen a `asset_type` de `search_funds` (Monetario, Renta Fija, Mixto, Renta Variable) |
| Campos obligatorios | Avisos (2), conocimiento de renta fija y variable, ingresos, gastos fijos, ahorro, deudas, objetivo, plazo, tolerancia por escenarios y preferencia ESG. Un dato con `low_confidence` cuenta como pendiente |
| Perfil de riesgo | Manda el más restrictivo de tres: tolerancia (escenarios 1–5 → los 5 perfiles), capacidad de pérdida (fracción del ahorro que se puede perder) y plazo (<2, <5, <8, <12 años) |
| Perfil → SRI | CONSERVADOR 3 · MODERADO 4 · DINAMICO 5 · AGRESIVO 6 · MUY_AGRESIVO 7 |
| Perfil → `risk_max` de carteras | 1 · 2 · 3 · 4 · 5. **Verificar con `list_facets` de MyInvestor** |
| Capacidad de pérdida | max(0, ahorro − 6 meses de gastos fijos − deudas) |
| Conveniencia | Conveniente si el conocimiento es al menos `medium` (`high` en productos complejos) o hay 5 o más operaciones en 3 años; depósitos, conveniente con cualquier conocimiento distinto de `none`; sin dato, `not_assessed` |
| Divisa | `EUR` por defecto (supuesto: cliente minorista en euros) |
| Liquidez | `high` → reembolso en 3 días o menos; `medium` → 7 días o menos |
| Rúbrica de confianza | **Sin implementar**: la define Hammad en el extractor y se indica en `confidence_basis` |

Comprobación con Carmen (datos simulados), que cubren los tests:
- Tolerancia 1/5 → CONSERVADOR, que manda sobre plazo (AGRESIVO) y capacidad (MUY_AGRESIVO) → SRI máximo 3, `risk_max` 1.
- Renta variable **no conveniente** (declaró alto, demostró nulo); renta fija y monetarios convenientes → `asset_type: [Monetario, Renta Fija]`.
- Completa y sin `needs_advisor` → `pending_validation`. Al validarla, `active` y las restricciones pasan a `usable: true`.

## API REST implementada (`backend/app/main.py`, docs en `/docs`)

| Ruta | Estado |
|---|---|
| `POST /api/sessions` `{client_id?, channel}` | ✔ |
| `POST /api/sessions/{id}/turns` `{turn_id?, speaker, text, t_start, t_end}` → `{turn_id}` | ✔ (extractor stub) |
| `GET /api/sessions/{id}` | ✔ |
| `GET /api/clients/{id}/profile[?version=]` | ✔ |
| `GET /api/clients/{id}/versions` | ✔ (con `reason` y `author`) |
| `POST /api/clients/{id}/validate` `{advisor_id, changes[]}` | ✔ (409 si falta un dato obligatorio o se intenta escribir un campo calculado) |
| `GET /api/clients/{id}/constraints` | ✔ |
| `GET /api/clients/{id}/evidence/{path}` | ✔ |
| `GET /api/clients/{id}/context` | ✔ (plantilla; Pablo lo hará con Claude) |
| `GET /api/voice/signed-url` | ✔ (sin probar con cuenta real) |
| `POST /api/demo/reset` | ✔ |
| `GET /api/sessions/{id}/stream` (SSE) | Pendiente (Juan). El front sondea cada 1,5 s |
| `POST /api/webhooks/elevenlabs` | Pendiente (Juan y Fernán, según la prueba de voz) |
| `GET /api/clients/{id}/dossier.pdf`, clips `.mp3` | Pendiente (Juan) |
| MCP con las 4 herramientas | Pendiente (Alejandro) |

## Para revisar

- **Alex:** las 7 desviaciones y las propuestas de la tabla de decisiones abiertas.
- **Juan:** `store.py` (transiciones de estado) y `calculos.py`, antes de pasar a SQLite.
- **Hammad y Pablo:** el contrato de sus módulos está en la cabecera de `agentes/extractor.py` y `agentes/verificador.py` (devuelven `Parche` y `Alerta`).
