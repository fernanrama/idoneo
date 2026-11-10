# Contrato v1: cómo lo implementa el código

**La especificación es [`docs/proyecto/04_CONTRATO_PERFIL.md`](proyecto/04_CONTRATO_PERFIL.md) (Alex).** Este documento no la repite: dice qué parte está implementada, dónde y en qué se desvía. El código de referencia es `backend/app/perfil/modelos.py` (esquema) y `calculos.py` (resultados). Cambiar el contrato = PR pequeña avisada al equipo.

Estado (8/11, `main`): contrato v1 (PR #9), MCP (PR #7) y persistencia, validación y versionado del backend (PR #8) integrados; frontend adaptado. Comportamiento del backend: sección [Backend integrado](#backend-integrado-persistencia-validación-y-versionado). Pendiente de revisión por **Alex** (especificación).

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
6. **La voz se inicia con `POST /api/voice/bootstrap` ligado a `session_id`**, separado de `POST /sessions` para que la sesión funcione también sin voz. La antigua ruta sin sesión queda desactivada por defecto.
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

**Propuesta local sobre #21, pendiente de revisión del equipo.** Las rutas de clientes, sesiones,
memoria, contexto y voz exigen `Authorization: Bearer <credencial del cliente>` o una credencial
de servicio explícita. Ni `client_id` ni `session_id` autorizan acceso. La posesión no acredita
identidad real. Sin credencial: 401; recurso de otro cliente: 404. Véase
[el contrato completo y las decisiones pendientes](MEMORIA_PERSONAL_SEGURIDAD.md).

| Ruta | Qué hace | Códigos |
|---|---|---|
| `GET /api/health` | Comprobación | 200 |
| `POST /api/sessions` `{client_id?, channel}` | Sin ID: alta exclusiva con ID aleatorio del servidor y credencial `access_token`. Con ID: exige permiso y abre sesión sin emitir otra credencial. `channel`: `voice` o `text`. Conserva la transición `review_due → draft` | 200 · 401 · 404 · 409 · 422 · 503 |
| `POST /api/sessions/{id}/turns` `{turn_id?, speaker, text, t_start, t_end}` | Guarda el turno → `{turn_id}`. Sin `turn_id` se asigna `t-001`, `t-002`…; reenviar el mismo `turn_id` no lo duplica. Con `speaker: "client"` lanza extractor y verificador en segundo plano (extractor aún stub) | 202 · 404 · 422 |
| `GET /api/sessions/{id}` | Sesión (`channel`, `started_at`, `ended_at`…), `turns[]` y `rejections[]` ([rechazos](#rechazos-visibles)) | 200 · 404 |
| `GET /api/sessions/{id}/pending` | Qué falta por preguntar → `{pending: [rutas], text}`. `text` va en frases para la herramienta de cliente `datos_pendientes` del agente de voz; si el último turno se está procesando, espera hasta 4 s | 200 · 404 |
| `GET /api/sessions/{id}/memory` | Memoria autorizada con `version` y ETag fuerte `"personal-N"`, incluso tras revocación | 200 · 401 · 404 |
| `PUT /api/sessions/{id}/memory` `{consent_given: true, updates, forget}` | Requiere If-Match vigente y consentimiento booleano explícito; mezcla bloques sin crear versión MiFID | 200 · 401 · 404 · 412 · 422 · 428 |
| `DELETE /api/sessions/{id}/memory` | Requiere If-Match; borra contenido e historial personal y conserva revisión técnica vacía creciente; no toca MiFID | 200 · 401 · 404 · 412 · 428 |
| `GET /api/clients/{id}/profile[?version=n]` | Última versión en cualquier estado (o la `n`), con la capa personal vigente unida | 200 · 404 |
| `GET /api/clients/{id}/versions` | `[{version, created_at, reason, author, status}]` | 200 · 404 |
| `POST /api/clients/{id}/validate` `{advisor_id, changes[]}` | La entidad corrige (opcional) y valida → perfil `active` ([reglas](#estados-y-validación-de-la-entidad)) | 200 · 401 · 404 · 409 · 422 |
| `GET /api/clients/{id}/constraints` | Restricciones del [perfil para consumidores](#versionado) | 200 · 404 |
| `GET /api/clients/{id}/evidence/{path}` | `{path, value, source, evidence}` del dato en la última versión | 200 · 404 (cliente, ruta inexistente o dato sin valor) |
| `GET /api/clients/{id}/context` | Resumen para otro agente, sobre el perfil para consumidores (plantilla; Pablo lo hará con Claude) | 200 · 404 |
| `GET /api/voice/signed-url` | Ruta legacy sin sesión, desactivada salvo `ALLOW_LEGACY_SIGNED_URL=1`; usar bootstrap | 200 · 410 · 502 · 503 |
| `POST /api/voice/bootstrap` `{session_id}` | URL firmada + `user_id` opaco + variables dinámicas mínimas de la sesión | 200 · 404 · 502 · 503 |
| `GET /api/voice/context/{session_id}` | Mismo contexto mínimo para el fallback de agente público; no devuelve `client_id` | 200 · 404 |
| `POST /api/webhooks/elevenlabs` | Verifica HMAC, deduplica por conversación y cierra/vincula la sesión post-llamada | 200 · 401 · 404 · 409 · 413 · 422 · 503 |
| `POST /api/demo/reset` | Recarga a Carmen (DATOS SIMULADOS) como versión nueva; no borra el historial | 200 · 401 · 404 (`DEMO_ENDPOINTS=0`) |
| `GET /api/demo/profile`, `GET /api/demo/constraints` | Ejemplo ficticio fijo, sin capa personal ni lectura del cliente mutable de Carmen. Desactivable con `DEMO_ENDPOINTS=0` | 200 · 404 |
| `GET /api/demo/asesor/estado` · `GET /api/demo/asesor/clientes/{id}` · `POST …/{id}/validar` · `POST …/{id}/reiniciar` | Modo asesor de demostración, apagado por defecto: `X-Demo-Advisor-Token`, solo local y solo clientes ficticios. Valida con `store.validar` ([detalle](MODO_ASESOR_DEMO.md)) | 200 · 401 · 403 · 404 · 409 · 422 · 503 |
| `/mcp` | MCP con las 4 herramientas de solo lectura (Alejandro), sobre el perfil para consumidores | ✔ |
| `GET /api/sessions/{id}/stream` (SSE) | Pendiente (Juan). El bus de eventos ya existe; el front sondea cada 1,5 s | — |
| `GET /api/clients/{id}/dossier.pdf`, clips `.mp3` | Pendiente (Juan) | — |

## Backend integrado: persistencia, validación y versionado

Rol A (Juan). Código en `backend/app/perfil/`: `store.py` es la única puerta de escritura (la usan la API, los agentes y el MCP); `validacion.py`, `personal.py`, `almacenes/` y `persistencia/` están por debajo. La lógica financiera sigue siendo la de `calculos.py`.

### Almacenes

| `PERFIL_ALMACEN` | Dónde se guarda | Para qué |
|---|---|---|
| `memoria` (por defecto) | En memoria. Si `DATA_PERSIST=1` (por defecto), versiones y capa personal se vuelcan a JSON en `DATA_DIR`. Las sesiones, turnos y rechazos no se vuelcan | Desarrollo, tests y demo sin base de datos |
| `bd` | `DATABASE_URL`: Postgres/Supabase, o vacío = SQLite en `backend/data/perfil.db` | Persistencia real. En Postgres exige las migraciones aplicadas ([procedimiento](../backend/migraciones/README.md)) |

Los dos almacenes se comportan igual (el algoritmo de escritura está una sola vez en `store.py`; `tests/test_paridad.py` lo comprueba). Al arrancar, el backend configura el almacén y falla con un mensaje claro si a la base le faltan las migraciones; con `LOAD_DEMO_FIXTURE=1` carga a Carmen **solo si no existe**, sin pisar datos guardados.

### Escritura y evidencias

Todo lo que se escribe pasa por `validacion.py`, con cualquier almacén:

| Regla | Si no se cumple |
|---|---|
| La ruta existe en `modelos.CAMPOS` y el valor tiene su tipo (niveles, opciones, números con rango, textos de hasta 1.000 caracteres, artículo SFDR 6/8/9) | 422 |
| Nadie escribe datos calculados (`financial.emergency_fund_months`, `financial.loss_capacity_eur`) ni `source: "calculated"` | 409 |
| Solo la entidad (`advisor:<id>`) escribe `source: "advisor"`; lo que corrige el asesor se guarda siempre como `advisor` | 422 |
| Un dato escrito por un agente (`agent:*`) lleva al menos una evidencia: `{session_id, turn_id?, t: [inicio, fin], quote, audio_url?}` (regla 4 del contrato 04) | 422 |
| `declared` solo se guarda si difiere de `value`; con `source: "demonstrated"` se marca `declared_vs_demonstrated` automáticamente | — |
| `low_confidence` lo marca el extractor según su rúbrica (no se deduce de `confidence`) | — |
| `client_id`: minúsculas, números, `-` y `_` (máx. 64). Autor: `agent:<x>`, `advisor:<id>`, `fn:<x>`, `fixture` o `system` | 422 |

Una escritura con varios parches es **todo o nada**. Excepción: lo que proponen los agentes en cada turno se acepta en parte ([rechazos visibles](#rechazos-visibles)).

### Versionado

- Cada cambio crea una versión nueva con `reason` y `author`; ninguna versión se modifica. Reescribir exactamente lo mismo no crea versión.
- En base de datos lo garantiza la propia base: `UPDATE`, `DELETE` y `TRUNCATE` bloqueados en `clients`, `profile_versions` y `turns` (también para el rol `postgres` y con `CASCADE`).
- Concurrencia optimista: si otra escritura (de este u otro proceso) se adelanta, se relee y reintenta; tras 5 intentos, 409.
- Las alertas no se duplican: se ignora una alerta con el mismo `flag` y `path` que otra abierta, o con un `id` ya existente. Una alerta solo puede apuntar a una ruta de `CAMPOS` (o a ninguna).
- **Perfil para consumidores** (restricciones, contexto y MCP): el último `active`; si no hay ninguno, la última versión (`usable: false`). `POST /api/demo/reset` abre una época nueva: añade una versión con `reason: "demo_reset: …"` y desde ese momento no se sirven activos anteriores.

### Estados y validación de la entidad

| De | A | Cuándo |
|---|---|---|
| `draft` | `pending_validation` | Tras cualquier escritura, si `suitability.complete` y no hay alertas `needs_advisor` abiertas |
| `pending_validation` | `draft` | Si deja de estar completo o aparece una alerta `needs_advisor` |
| `draft` o `pending_validation` | `active` | `POST /validate`, si el perfil está completo |
| `active` | `review_due` | Un agente cambia un dato (las correcciones del asesor no lo cambian de estado) |
| `review_due` | `draft` | Al abrir una sesión nueva (`POST /api/sessions`) |

`POST /validate` responde **409** si el perfil está en `active` o `review_due` (desde `review_due` hay que reentrevistar), si falta algún dato obligatorio o si un cambio intenta escribir un dato calculado; **422** si `advisor_id` o algún cambio no son válidos. Al validar se cierran **todas** las alertas abiertas (regla del contrato v1) y cada una registra `resolved_by` y `resolved_at`; `review.next_review` queda a un año (todavía no vence solo). Añadir alertas a un perfil `active` no cambia su estado.

### Capa personal

- Se guarda aparte de la capa MiFID (tabla `personal_versions` en base de datos) y con consentimiento propio: sin consentimiento no se admite ningún dato (422).
- Bloques admitidos: `life_stage`, `retirement`, `held_elsewhere`, `tax`, `exclusions` (lista de textos), `communication` y `concerns`. La proyección del agente solo usa `communication`, `exclusions` y `concerns`; tiene allowlist, 4 KB por capa, listas de hasta 20 elementos y textos de hasta 300 caracteres.
- Hacia fuera se ve en `Perfil.personal` con la forma del contrato 04: `{"consent": {"given": true, "at": "…"}, "exclusions": […], …}`. Sin consentimiento, `{}`. Las exclusiones llegan a `post_filters` (`top_sectors`).
- Se puede borrar entera sin tocar las versiones MiFID. Se purgan los snapshots personales con contenido y se conserva una revisión técnica vacía, sin consentimiento, para rechazar peticiones antiguas. Las versiones MiFID guardadas no la contienen: al leer cualquier versión se une la capa personal **vigente**. No implica borrar copias externas ni todos los metadatos.
- Se lee, rectifica y revoca mediante las rutas de memoria de la sesión. El frontend muestra consentimiento separado y permite borrarla. El extractor MiFID nunca recibe esta capa; el entrevistador recibe una proyección corta marcada como datos, no instrucciones.
- Todos los cambios personales comparan y escriben dentro de una transacción. Las ediciones conservan fecha e historial del consentimiento hasta la supresión; reactivar exige la revisión vigente y una aceptación nueva. Datos históricos admitidos por el contrato anterior se conservan, y solo se validan estrictamente los bloques modificados.
- Falta de If-Match: 428; revisión obsoleta o cabecera ambigua: 412. No se acepta `*`, ni se reintenta automáticamente adoptando otra revisión.

### Voz, correlación y cierre de sesión

- `POST /api/voice/bootstrap` pide la URL temporal a ElevenLabs y añade `userId` seudónimo, `session_id`, memoria consentida y siguiente foco. La API key permanece en el backend.
- `system__user_id` es solo correlación, no autenticación. `VOICE_USER_ID_SECRET` evita enviar el `client_id`; el fallback fijo solo es aceptable en desarrollo local.
- El prompt y los placeholders se versionan en el repo y se sincronizan con `python scripts/sincronizar_voz.py --aplicar`, preservando voz, herramientas y ajustes del panel.
- El webhook exige `ELEVENLABS_WEBHOOK_SECRET`, valida `ElevenLabs-Signature` con una ventana de 30 minutos y limita el cuerpo a 1 MB. Repetir el mismo evento es inocuo; otra conversación sobre la misma sesión devuelve 409.
- El webhook no convierte la transcripción en memoria personal. En esta iteración solo vincula `conversation_id` y rellena `ended_at`.
- `ELEVENLABS_SERVER_LOCATION` es opcional. Configurarlo no demuestra por sí solo residencia contractual ni Zero Retention Mode.

### Rechazos visibles

En cada turno del cliente, extractor y verificador se ejecutan por separado (si uno falla, el otro sigue). Cada parche y cada alerta se valida por separado con las reglas anteriores: los válidos se guardan (los parches, en una sola versión) y los inválidos se rechazan. Cada rechazo se ve en `GET /api/sessions/{id}`:

```json
"rejections": [
  {"session_id": "s-…", "client_id": "carmen-68", "origen": "extractor", "tipo": "parche",
   "path": "financial.debts_eur", "motivo": "financial.debts_eur: un dato sacado de la conversación necesita su evidencia",
   "created_at": "…"}
]
```

- `origen`: `extractor`, `verificador` o `backend` (no se pudo guardar). `tipo`: `parche`, `alerta` o `error` (el agente falló o no devolvió una lista).
- También se publican en el bus de eventos (`item.rejected`) y en el log del servidor.
- Se guardan en la memoria del proceso (los últimos 200 por sesión): **no sobreviven a un reinicio** del backend.

### Errores HTTP

| Código | Cuándo |
|---|---|
| 401 | `ADMIN_TOKEN` definido y falta o no coincide la cabecera `X-Admin-Token` (`POST /validate` y `POST /api/demo/reset`) |
| 404 | Cliente, versión, sesión, fixture o dato inexistente; `POST /api/demo/reset` con `DEMO_ENDPOINTS=0` |
| 409 | Transición no permitida, perfil incompleto al validar, escritura de un dato calculado o demasiadas escrituras simultáneas |
| 422 | Entrada que no cumple el esquema o las reglas de escritura (ruta, tipo, autoría, evidencia, `client_id`, canal, capa personal) |
| 502 · 503 | Voz: ElevenLabs respondió con error · el backend no tiene configurada la voz |

### Eventos internos

`store.bus` publica `profile.patch` (`path`, `fact`), `flag.raised` (`path`, `flag`, `message`, `alert_id`), `profile.status` (`status`, `complete`, `missing`) e `item.rejected`. Son la base del SSE pendiente; todavía no hay endpoint que los sirva.

### Seguridad y límites conocidos

- `CLIENT_ACCESS_SECRET` obligatorio (mínimo 32 bytes) firma una credencial de posesión al crear un cliente nuevo. Nunca se emite otra por presentar un ID existente. Caducidad propuesta: ocho horas (`CLIENT_ACCESS_TTL_S`). No demuestra identidad ni permite recuperar datos antiguos sin credencial.
- Lecturas y escrituras REST, contexto de agentes y las cuatro herramientas MCP comprueban el cliente autorizado. El transporte MCP también exige credencial. Los consumidores de servicio necesitan `ADMIN_TOKEN` explícito; no hay acceso implícito por localhost.
- `POST /api/clients/{id}/validate` exige **ambos**: Bearer del propietario y `X-Admin-Token` de servicio. Reset exige servicio. Sin servicio configurado, estas acciones fallan con 503.
- Las rutas Next de validación y reset devuelven 403 y no reenvían peticiones ni añaden credenciales de servicio, salvo con el [modo asesor de demostración](MODO_ASESOR_DEMO.md) activo: entonces el servidor Next usa su propio `DEMO_ADVISOR_TOKEN` (nunca `ADMIN_TOKEN` ni el Bearer del cliente) contra un backend local y solo para clientes ficticios. La validación web queda bloqueada hasta acordar un permiso independiente de asesor; el Bearer del cliente no sirve como ese permiso. La API directa sigue exigiendo propietario y servicio explícitos. La demo fija es de solo lectura.
- Las credenciales permanecen en `sessionStorage`, fuera de URLs, metadatos de React y `localStorage`. Respuestas privadas con `Cache-Control: no-store`. Host/CORS son restricciones adicionales, no autorización. Una XSS podría leer la credencial; revisar el transporte antes de usar datos reales.
- Pendiente: identidad real, comparar versiones, marcar un evento vital (`active → review_due`), que `next_review` venza solo, reconciliar tiempos/audio y coordinar el borrado con la retención configurada en ElevenLabs.

## Para revisar

- **Alex:** las 7 desviaciones y las propuestas de la tabla de decisiones abiertas.
- **Juan:** endpoint SSE, audio y expediente; persistir los rechazos si hace falta.
- **Hammad y Pablo:** el contrato de sus módulos está en la cabecera de `agentes/extractor.py` y `agentes/verificador.py` (devuelven `Parche` y `Alerta`). Los parches del extractor necesitan evidencia; los rechazos se ven en `GET /api/sessions/{id}`.
