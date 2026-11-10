# Modo asesor de demostración

**Estado:** IMPLEMENTADO en la rama `feat/demo-modo-asesor` (sin fusionar). Solo prototipo, DATOS SIMULADOS.

Recupera el paso «Validar perfil» del recorrido de Carmen sin reabrir la autovalidación que cerró la PR #21. Está **apagado por defecto**. Encendido, permite que la vista de la entidad lea el expediente persistido de un cliente ficticio, lo valide con la validación atómica de siempre y lo reinicie para repetir el ensayo.

## Cómo se activa para la presentación

1. Genera un token largo y aleatorio. Tiene que ser distinto de `ADMIN_TOKEN`, de `CLIENT_ACCESS_SECRET` y de `VOICE_USER_ID_SECRET`:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. En el `.env` de la raíz (backend):
   ```
   DEMO_ADVISOR_MODE=1
   DEMO_ADVISOR_TOKEN=<el token>
   # Opcionales:
   # DEMO_ADVISOR_CLIENTS=carmen-68     (por defecto)
   # DEMO_ADVISOR_ID=asesor-demo        (aparece como validated_by)
   ```
3. En `frontend/.env.local` (servidor Next; **sin** prefijo `NEXT_PUBLIC_`):
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
| Solo datos ficticios | `DEMO_ADVISOR_CLIENTS` solo admite fixtures de `backend/fixtures/` cuyo `reason` empieza por «DATOS SIMULADOS» y cuyo `client_id` coincide. Cualquier otro cliente, aunque exista, responde 404 |
| No activarse en un despliegue público | Apagado salvo `DEMO_ADVISOR_MODE=1` exacto. Backend: conexión desde loopback, `Host` local y sin `Forwarded`, `X-Forwarded-*` ni `X-Real-IP`. Next: `Host` local, `X-Forwarded-*` solo con valores locales, `Origin` del mismo sitio en escrituras y backend local. Token de al menos 32 bytes y distinto de los demás secretos |
| Validación existente | `store.validar` (atómica, sin correcciones): mismo 409 si ya está activo o incompleto, sin versiones parciales |

## Rutas

**Backend.** Todas exigen `X-Demo-Advisor-Token`. Errores: 404 si el modo está apagado o el cliente no está en la lista; 403 si la petición no es local; 503 si la configuración es insegura; 401 sin token válido; 409 y 422 de la validación.

| Ruta | Respuesta |
|---|---|
| `GET /api/demo/asesor/estado` | `{enabled, simulated, clients, advisor_id}` |
| `GET /api/demo/asesor/clientes/{id}` | `{profile, constraints, versions}`. `constraints` es lo mismo que sirve el MCP |
| `POST /api/demo/asesor/clientes/{id}/validar` | Perfil validado |
| `POST /api/demo/asesor/clientes/{id}/reiniciar` | Perfil recargado desde el fixture |

**Servidor Next.** Sin credenciales del navegador.

| Ruta | Qué hace |
|---|---|
| `GET /api/entidad/asesor` | Indica si el modo está activo |
| `GET /api/entidad/{id}/asesor` | Devuelve el expediente |
| `POST /api/entidad/{id}/validar` | Valida. Con el modo apagado responde 403, como en la PR #21 |
| `POST /api/entidad/reset` | Reinicia a Carmen. Con el modo apagado responde 403 |

## Límites fuera del prototipo

- **No es autenticación de asesores.** El token es un secreto compartido de la máquina de la demo: no identifica a una persona, no caduca y no tiene permisos por cliente. Todas las validaciones quedan firmadas como `advisor:<DEMO_ADVISOR_ID>`.
- Una entidad real necesita identidad del asesor (SSO), permisos por cliente y por función, registro de accesos, caducidad y revocación.
- Solo valida sin correcciones y no comprueba la versión que el asesor tenía en pantalla. Eso está previsto en la PR-2 (`expected_version`) del plan del perfil vivo.
- La comprobación de «local» confía en que nadie ponga un proxy que reescriba `Host` y quite las cabeceras `X-Forwarded-*`. Es una red de seguridad contra activarlo por error, no una garantía frente a un administrador que lo fuerce.
- Cualquier proceso del mismo ordenador que conozca el token puede validar a los clientes ficticios. No uses este modo en una máquina compartida.

## Pruebas

```bash
cd backend && python -m pytest -q tests/test_asesor_demo.py   # 31 casos × memoria y SQLite
cd frontend && npm run test:contrato                          # incluye tests/asesor-demo.mjs
cd frontend && npx next build && IDONEO_PYTHON=../backend/.venv/bin/python npm run test:asesor-demo
# Opcional, con navegador: IDONEO_PLAYWRIGHT_MODULE=/ruta/a/playwright/index.mjs
```

`test:asesor-demo` arranca un backend y tres servidores Next en puertos efímeros: el modo activo, uno con un token que el backend no acepta y uno apagado. Recorre después el caso de Carmen: once intentos no autorizados, la validación, la comprobación por MCP y por REST y el reinicio. Con Playwright, además, pulsa el botón en Chromium. Nunca usa los puertos 3000 y 8000.
