# Modo asesor de demostración

**Estado:** modo asesor IMPLEMENTADO en `main` (PR #25). Operador para clientes nuevos y credenciales MCP de demostración: rama `feat/mcp-pitch`, pendiente de revisión. Solo prototipo, DATOS SIMULADOS.

Recupera el paso «Validar perfil» del recorrido de Carmen sin reabrir la autovalidación que cerró la PR #21. Está **apagado por defecto**. Encendido, permite que la vista de la entidad lea el expediente persistido de un cliente ficticio, lo valide con la validación atómica de siempre y lo reinicie para repetir el ensayo.

## Cómo se activa para la presentación

**Atajo:** `python scripts/preparar_demo.py` (desde `backend/`) hace los pasos 1 a 3 y genera también `MCP_DEMO_TOKEN` y el resto de secretos locales, sin mostrarlos y sin cambiar los que ya existan. Los pasos manuales siguen siendo válidos.

1. Genera un token largo y aleatorio directamente en el `.env` de la raíz, **sin que aparezca en pantalla**. Tiene que ser distinto de `ADMIN_TOKEN`, de `CLIENT_ACCESS_SECRET` y de `VOICE_USER_ID_SECRET`. Hazlo solo si esa variable aún no está en el `.env`:
   ```bash
   printf 'DEMO_ADVISOR_TOKEN=%s\n' "$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env && chmod 600 .env
   ```
2. En el `.env` de la raíz (backend):
   ```
   DEMO_ADVISOR_MODE=1
   DEMO_ADVISOR_TOKEN=<generado en el paso 1>
   # Opcionales:
   # DEMO_ADVISOR_CLIENTS=carmen-68     (por defecto)
   # DEMO_ADVISOR_ID=asesor-demo        (aparece como validated_by)
   ```
3. En `frontend/.env.local` (servidor Next; **sin** prefijo `NEXT_PUBLIC_`). Copia el token sin mostrarlo con `grep '^DEMO_ADVISOR_TOKEN=' .env >> frontend/.env.local`:
   ```
   DEMO_ADVISOR_MODE=1
   DEMO_ADVISOR_TOKEN=<el mismo token>
   # API_URL_SERVIDOR=http://localhost:8000   (opcional; debe ser local)
   ```
4. Reinicia backend y front. El backend escribe en el log `MODO ASESOR DE DEMO ACTIVO` y la lista de clientes permitidos. Si algo está mal configurado, escribe el motivo y el modo queda inactivo.
5. Abre `http://localhost:3000/entidad/carmen-68` **en el mismo ordenador**. Verás la nota «Modo asesor de demostración» y el botón «Validar perfil» habilitado. Tras validar aparecen «Validado · vN», «Disponible por MCP» y, en la pestaña «Agente · MCP», «Usable · vN». «Reiniciar la demo» vuelve a cargar a Carmen como versión nueva, sin borrar el historial.

**Para desactivarlo:** borra las dos líneas, o pon `DEMO_ADVISOR_MODE=0`, en ambos `.env` y reinicia. El botón vuelve a quedar deshabilitado y las rutas responden como en la PR #21 (403 en Next, 404 en el backend).

## Qué protege

| Requisito | Cómo |
|---|---|
| Separación cliente/asesor | El backend solo mira `X-Demo-Advisor-Token`; no lee `Authorization`. El Bearer del cliente, su `client_id`, un `session_id` o `ADMIN_TOKEN` usados como token devuelven 401. El token de asesor tampoco abre las rutas del cliente, `/validate`, `/api/demo/reset` ni `/mcp` |
| Secretos fuera del navegador | El token vive en el entorno del servidor Next y solo se envía a un backend local. El navegador llama a `/api/entidad/...` sin credenciales, y ni la respuesta, ni el HTML, ni el bundle, ni el almacenamiento lo contienen (comprobado) |
| Botón habilitado solo con autorización comprobada | `GET /api/entidad/asesor` pregunta al backend con el token. Si el backend no lo acepta, el modo aparece apagado |
| Solo datos ficticios | `DEMO_ADVISOR_CLIENTS` solo admite fixtures de `backend/fixtures/` cuyo `reason` empieza por «DATOS SIMULADOS» y cuyo `client_id` coincide. Un cliente nuevo solo entra si el operador lo autoriza ([ver abajo](#autorizar-un-cliente-nuevo-operador)). Cualquier otro, aunque exista, responde 404 |
| No activarse en un despliegue público | Apagado salvo `DEMO_ADVISOR_MODE=1` exacto. Backend: conexión desde loopback, `Host` local y sin `Forwarded`, `X-Forwarded-*` ni `X-Real-IP`. Next: `Host` local, `X-Forwarded-*` solo con valores locales, `Origin` del mismo sitio en escrituras y backend local. Token de al menos 32 bytes y distinto de los demás secretos |
| Validación existente | `store.validar` (atómica, sin correcciones): mismo 409 si ya está activo o incompleto, sin versiones parciales |

## Rutas

**Backend.** Todas exigen `X-Demo-Advisor-Token`. Errores: 404 si el modo está apagado o el cliente no está en la lista; 403 si la petición no es local; 503 si la configuración es insegura; 401 sin token válido; 409 y 422 de la validación.

| Ruta | Respuesta |
|---|---|
| `GET /api/demo/asesor/estado` | `{enabled, simulated, clients, advisor_id}` |
| `GET /api/demo/asesor/clientes/{id}` | `{profile, constraints, versions}`. `constraints` es lo mismo que sirve el MCP |
| `POST /api/demo/asesor/clientes/{id}/validar` `{expected_version?}` | Perfil validado. Con `expected_version` (la versión que ve el asesor), 409 sin escribir nada si el perfil ha cambiado desde entonces; sin ella, valida la última versión (compatibilidad). Otros campos → 422 |
| `POST /api/demo/asesor/clientes/{id}/reiniciar` | Perfil recargado desde el fixture |
| `POST /api/demo/asesor/clientes/{id}/entrevista?channel=voice\|text` | Recarga el fixture, abre una sesión y devuelve `{session_id, client_id, access_token, …}` para la entrevista corta |

**Servidor Next.** Sin credenciales del navegador.

| Ruta | Qué hace |
|---|---|
| `GET /api/entidad/asesor` | Indica si el modo está activo |
| `GET /api/entidad/{id}/asesor` | Devuelve el expediente |
| `POST /api/entidad/{id}/validar` | Valida. Con el modo apagado responde 403, como en la PR #21 |
| `POST /api/entidad/reset` | Reinicia a Carmen. Con el modo apagado responde 403 |
| `POST /api/entidad/corta?channel=voice\|text` | Empieza la entrevista corta sobre `carmen-corta`. Con el modo apagado responde 403 |

## Entrevista corta del pitch

Una entrevista real completa dura unos ocho minutos y, si falta un dato obligatorio, «Validar» responde 409. Para enseñar la voz real en el pitch sin ese riesgo existe `carmen-corta` (`backend/fixtures/carmen-corta.json`, DATOS SIMULADOS). Es Carmen con casi todo el perfil hecho; **solo faltan** el conocimiento de renta variable y el escenario de caída. La sostenibilidad ya viene contada: una respuesta ambigua hacía que el asistente repreguntara y que el verificador dejara el dato pendiente. Es justo el momento «declarado ≠ demostrado».

1. Con el modo asesor activo, en `http://localhost:3000/onboarding/entrevista` («Pruébalo» en la portada) aparece la casilla **«Entrevista corta del pitch»**. Desde #64, `/escenario` solo reproduce la demo guiada. Márcala, marca las dos de consentimiento y pulsa **Hablar** o **Escribir**.
2. El asistente solo pregunta lo que falta: la lista de pendientes sale de `OBLIGATORIOS`. Respuesta sugerida: dice que conoce bien los fondos de renta variable y, ante la comprobación, «eso no puede pasar, el fondo es del banco»; ante una caída del 20 %, «lo saco todo».
3. Al terminar, «Mi perfil» enlaza al pie a «¿Eres del banco? Abre la vista del asesor», que abre `/admin?cliente=carmen-corta` (pide la clave del equipo, `ADMIN_LOGIN_CLAVE`). Con el modo asesor también se puede ir directo a `/entidad/carmen-corta` → **Validar perfil** (un solo clic).
4. Claude Code lee `carmen-corta` con `MCP_DEMO_TOKEN`: por defecto `MCP_DEMO_CLIENTS` incluye `carmen-68,carmen-corta`.

Cada nueva entrevista corta recarga el fixture como versión nueva (no borra el historial), así que se puede ensayar cuantas veces haga falta. Por defecto, `DEMO_ADVISOR_CLIENTS` y `MCP_DEMO_CLIENTS` son `carmen-68,carmen-corta`.

## Autorizar un cliente nuevo (operador)

Para que el asesor de demo valide, y el MCP sirva, a un cliente ficticio **creado en directo con una entrevista**, una persona de confianza lo autoriza desde el ordenador del backend:

```bash
cd backend
python scripts/demo_operador.py autorizar <client_id> --confirmo-ficticio     # stdout: solo el token MCP de ese cliente
python scripts/demo_operador.py listar                                        # vigentes (sin tokens)
python scripts/demo_operador.py revocar <client_id>                           # al terminar
python scripts/demo_operador.py revocar-todo
```

| Garantía | Cómo |
|---|---|
| Solo el operador | `POST /api/demo/operador/autorizaciones` exige `X-Admin-Token`, que lee el script del `.env` sin mostrarlo. No acepta el Bearer del cliente, su `client_id`, su `session_id`, el token del asesor ni los tokens MCP (401). Nada de esto pasa por el navegador ni por Next |
| Solo local y solo en modo demo | Con `DEMO_ADVISOR_MODE=1`, desde loopback, `Host` local y sin proxy. Si no, 404 o 403 |
| Explícita y por cliente | `"ficticio": true` obligatorio (el script exige `--confirmo-ficticio`). Una autorización = un `client_id`. Como mucho 10 a la vez |
| Caduca, se revoca y no se reutiliza | 2 h por defecto (60 s–8 h). Vive solo en la memoria del proceso: reiniciar el backend anula todas las autorizaciones y tokens, aunque el cliente siga en la base. Renovar invalida el token anterior. Solo se guarda la huella SHA-256 del token |
| Sin atajos MiFID | Autorizar no crea versiones ni cambia el estado. El asesor valida con `store.validar`: un perfil incompleto sigue dando 409. Revocar no toca el perfil: solo quita el acceso de demo |
| MCP de solo lectura y solo ese cliente | El token `idoneo-demo-…` vale en `/mcp`, por cabecera y desde local, para las 4 herramientas de lectura y solo para ese `client_id`. Otro cliente: 404. API REST: 401 |

La vista `/entidad/<client_id>` avisa si el modo asesor está activo pero el cliente no está autorizado, y muestra el comando exacto. «Reiniciar la demo» solo aparece con Carmen: un cliente nuevo no tiene fixture que recargar.

## Recorrido completo del pitch

Todo en el portátil, sin túneles. DATOS FICTICIOS. La entrevista real consume créditos de Claude (2 llamadas por turno); la voz, minutos de ElevenLabs.

**Preparación (una vez)**

1. En el `.env` de la raíz: `DEMO_ADVISOR_MODE=1`, `DEMO_ADVISOR_TOKEN`, `MCP_DEMO_TOKEN` y `ADMIN_TOKEN` (32+ bytes), con valores aleatorios distintos, más `ANTHROPIC_API_KEY` para la entrevista real. `PERFIL_ALMACEN=memoria`. Para añadir un secreto **sin que aparezca en pantalla** (solo si esa variable aún no está en el `.env`):
   ```bash
   printf 'MCP_DEMO_TOKEN=%s\n' "$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env && chmod 600 .env
   ```
2. En `frontend/.env.local`: `DEMO_ADVISOR_MODE=1` y el mismo `DEMO_ADVISOR_TOKEN`. Cópialo sin mostrarlo: `grep '^DEMO_ADVISOR_TOKEN=' .env >> frontend/.env.local`.
3. Dependencias: `pip install -r backend/requirements.txt` (incluye `anthropic`). Después, `next build` y arrancar backend y front. El log del backend debe decir `MODO ASESOR DE DEMO ACTIVO` y `CREDENCIAL MCP DE DEMO ACTIVA`.
4. Claude Code con MyInvestor: `claude mcp add --transport http myinvestor https://mcp.myinvestor.es/mcp`.

**En directo**

1. **Entrevista:** `http://localhost:3000/onboarding/entrevista` → responder por escrito o por voz con el cliente ficticio. Al terminar, «Mi perfil» (`/onboarding/perfil`) enlaza al pie a «¿Eres del banco? Abre la vista del asesor», que abre `/admin?cliente=<client_id>`; con el modo asesor también vale `/entidad/<client_id>` directamente.
2. **Perfil pendiente:** la vista muestra los datos con su frase y el aviso «este cliente aún no está autorizado», con el comando exacto.
3. **Autorización del operador**, en la terminal del backend. El token se captura en una variable y nunca se ve; el script se niega a escribirlo en la terminal:
   ```bash
   cd backend
   export IDONEO_MCP_TOKEN="$(python scripts/demo_operador.py autorizar <client_id> --confirmo-ficticio)"
   ```
4. **Validación del asesor:** recarga `/entidad/<client_id>` → «Validar perfil». Si faltan datos obligatorios, el backend lo rechaza (409) y hay que completar la entrevista.
5. **Conectar el MCP de ese cliente**, desde la misma carpeta en la que luego abrirás Claude Code (el servidor se guarda con alcance local, ligado a esa carpeta). Usa **comillas simples**: así la shell no sustituye la variable y Claude Code guarda la referencia `${IDONEO_MCP_TOKEN}`, no el token; la resuelve al conectar:
   ```bash
   claude mcp add --transport http idoneo http://localhost:8000/mcp -H 'Authorization: Bearer ${IDONEO_MCP_TOKEN}'
   claude mcp list        # «idoneo» y «myinvestor» conectados
   ```
   Para Carmen, carga antes su token sin mostrarlo: `export IDONEO_MCP_TOKEN="$(grep '^MCP_DEMO_TOKEN=' .env | cut -d= -f2-)"`.
   Abre Claude Code (`claude`) **en la misma terminal** en la que exportaste `IDONEO_MCP_TOKEN`: la variable se lee al conectar, no al añadir. Para cambiar de cliente basta con exportar el token nuevo y reiniciar Claude Code; el servidor no se vuelve a añadir.
   `~/.claude.json`, `claude mcp list` y `claude mcp get idoneo` solo muestran `Bearer ${IDONEO_MCP_TOKEN}`, nunca el token (comprobado en Claude Code 2.1.322 con un servidor local de prueba y un token ficticio). Con comillas dobles, la shell escribiría el token real en `~/.claude.json` y `claude mcp get` lo mostraría en claro.
6. **Claude + MyInvestor:** *«Usa el conector de Idóneo para leer las restricciones de <client_id> y busca en MyInvestor fondos compatibles; explica qué descartas y por qué, con la evidencia de la entrevista.»* Claude llama a `get_investment_constraints` (`usable: true`), busca en MyInvestor con `funds_query` (una búsqueda por `asset_type`), aplica `post_filters` y respeta `appropriateness`. La selección final es del agente de la entidad.
7. **Al terminar (revocación):**
   ```bash
   python scripts/demo_operador.py revocar-todo     # los tokens de operador dejan de valer al instante
   claude mcp remove idoneo                         # quita el servidor de ~/.claude.json (solo guardaba la referencia)
   unset IDONEO_MCP_TOKEN
   ```
   Reiniciar el backend también anula todas las autorizaciones. `MCP_DEMO_TOKEN` (la de Carmen) es configuración fija: para revocarla, quítala del `.env` o cámbiala y reinicia.

**Si algo falla:** el MCP responde 401 (token caducado, revocado o de antes de un reinicio: vuelve a autorizar) · 403 (la petición no viene de localhost) · 404 en una herramienta (el token no es de ese cliente). Si la validación da 409, el perfil está incompleto o ya validado.

## Límites fuera del prototipo

- **Operador y MCP de demostración:** el operador se autentica con `ADMIN_TOKEN` (servicio local), no con una identidad propia. Que el cliente sea ficticio lo declara el operador (`--confirmo-ficticio`); el sistema no puede comprobarlo. Las autorizaciones viven en la memoria de un único proceso: con varios workers de uvicorn no se compartirían. `MCP_DEMO_TOKEN` no caduca sola. Ninguna de estas credenciales sirve para producción, que necesitaría OAuth del conector, identidad del consumidor y permisos por propósito.

- **No es autenticación de asesores.** El token es un secreto compartido de la máquina de la demo: no identifica a una persona, no caduca y no tiene permisos por cliente. Todas las validaciones quedan firmadas como `advisor:<DEMO_ADVISOR_ID>`.
- Una entidad real necesita identidad del asesor (SSO), permisos por cliente y por función, registro de accesos, caducidad y revocación.
- Solo valida sin correcciones y no comprueba la versión que el asesor tenía en pantalla. Eso está previsto en la PR-2 (`expected_version`) del plan del perfil vivo.
- La comprobación de «local» confía en que nadie ponga un proxy que reescriba `Host` y quite las cabeceras `X-Forwarded-*`. Es una red de seguridad contra activarlo por error, no una garantía frente a un administrador que lo fuerce.
- Cualquier proceso del mismo ordenador que conozca el token puede validar a los clientes ficticios. No uses este modo en una máquina compartida.

## Pruebas

```bash
cd backend && python -m pytest -q tests/test_asesor_demo.py tests/test_demo_operador.py tests/test_mcp_demo.py
cd frontend && npm run test:contrato                          # incluye tests/asesor-demo.mjs
cd frontend && npx next build && IDONEO_PYTHON=../backend/.venv/bin/python npm run test:asesor-demo
# Opcional, con navegador: IDONEO_PLAYWRIGHT_MODULE=/ruta/a/playwright/index.mjs
```

`test:asesor-demo` arranca un backend y tres servidores Next en puertos efímeros: el modo activo, uno con un token que el backend no acepta y uno apagado. Recorre después el caso de Carmen: once intentos no autorizados, la validación, la comprobación por MCP y por REST y el reinicio. Con Playwright, además, pulsa el botón en Chromium. Nunca usa los puertos 3000 y 8000.
