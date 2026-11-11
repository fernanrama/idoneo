# Frontend — Idóneo

Prototipo de **feature para la app móvil de MyInvestor**: onboarding del perfil inversor por voz. Next.js 16 (App Router), pensado primero para móvil. **No es un producto oficial; los datos son simulados.**

## Arrancar

```bash
cd frontend
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_URL y, si aplica, NEXT_PUBLIC_ELEVENLABS_AGENT_ID
npm run dev                     # http://localhost:3000
```
El backend tiene que estar en marcha (ver README raíz). Para probar en el móvil en la misma wifi: `npm run dev -- -H 0.0.0.0` y abrir `http://<IP-del-PC>:3000`. El micrófono en el móvil exige HTTPS fuera de localhost: usar un túnel HTTPS para la prueba de voz.

## Pantallas

| Ruta | Pantalla |
|---|---|
| `/` | Portada del producto: barra fija, el problema, «cómo funciona» contado con el scroll, qué recibe la entidad y accesos para probarlo |
| `/onboarding` | Redirige a la entrevista (el aviso de IA y el consentimiento están ahora en su pantalla de inicio) |
| `/onboarding/entrevista` | Entrevista con el aura: solo la pregunta actual, por voz o **por escrito** (modo texto, necesita la clave de Claude en el backend). Si el cliente tiene una revisión abierta, es la **microentrevista**: sus motivos, sus preguntas y una barra de progreso. Para mirar sin hacer la entrevista, enlaza a la demo guiada del escenario |
| `/onboarding/cambio` | «¿Ha cambiado algo en tu vida?»: el cliente elige qué ha pasado y ve, antes de empezar, qué se le va a preguntar (lo calcula el backend). En el móvil, una barra fija resume cuántas preguntas son y lleva al plan |
| `/onboarding/perfil` | Perfil para el cliente, en claro: medidor de riesgo, lo que hemos entendido con la frase de cada dato, avisos, «¿Ha cambiado algo?» (o la revisión a medias), «Lo que ha cambiado» y siguiente paso |
| `/onboarding/productos` | Filtros del perfil en lenguaje claro, qué se busca y qué no (y por qué), la hipoteca y el aviso de datos en revisión. **No consulta el MCP de MyInvestor por código**: sus términos lo prohíben (ver `docs/diseno/04-mcp-myinvestor.md`) |
| `/escenario` | La demo guiada (y el pitch): entrevista a la izquierda y lo que recibe la entidad, en directo, a la derecha. En el móvil, por pestañas. `?cliente=<id>` muestra un perfil ya existente |
| `/entidad/[cid]` | Vista de la entidad con pestañas: resumen, evidencias (cada cita suena con su fragmento de audio, ver `docs/pruebas-de-audio.md`), historial y restricciones. Con cambios sin validar: datos en revisión, progreso de la microentrevista y antes/después. Validación web bloqueada hasta contar con permiso de asesor |

## Validar el perfil con el backend protegido

La validación desde el navegador está bloqueada con 403 hasta acordar un permiso independiente
para asesores. Next no añade `ADMIN_TOKEN` a las peticiones de clientes. El botón de la vista
conserva su lugar, deshabilitado y con una explicación. Tener la credencial del cliente no permite
validarlo como asesor. El reset del navegador también permanece bloqueado.

La API de revisión sigue requiriendo ambos permisos explícitos (propietario y servicio); no se
presenta este mecanismo como identidad autenticada de un asesor. `ADMIN_TOKEN` queda solo en el
backend y en consumidores de servicio autorizados, sin copiarlo al entorno del frontend.

## Dónde está cada cosa

- `src/tema/visual.css`: tokens del tema oscuro (`.tema-noche`), clases `.mono`, `.vidrio` y todas las animaciones (`v-*`). Con «reducir movimiento» activado se apagan.
- `src/components/visual.tsx`: piezas del tema oscuro (`Noche`, `Aura`, botones, iconos). `Entrevista.tsx` y `PanelVivo.tsx` son la entrevista y el panel en directo; `BarraCliente.tsx` y `cliente.module.css`, las pantallas claras del cliente.
- `src/components/Esfera3D.tsx`: la esfera de plasma en 3D (un shader de WebGL, sin librerías ni imágenes). Es el aura del entrevistador y, con otros colores, la esfera del perfil del cliente y la de la entidad (`Formas.tsx`). Si no hay WebGL se ve un respaldo en CSS. `Revela.tsx` hace aparecer los bloques al hacer scroll.
- `src/tema/tema.css`: tokens y utilidades globales que importa `globals.css` (`.pila`, `.fila`, `.oculto-visual`…).
- `src/lib/useEntrevista.ts`: lógica de la entrevista (voz de ElevenLabs o guion), envío de turnos, sondeo del perfil y paso de alertas al agente.
- `src/lib/guion.ts`: guion de Carmen (**simulado**). Se sustituirá por `backend/eval/carmen.json` de Pablo.
- `src/lib/api.ts` y `src/lib/tipos.ts`: cliente y tipos del contrato (`docs/contratos.md`).

## Demo guiada
Está en `/escenario` («Ver la demo guiada»); la entrevista del cliente solo enlaza a ella, para que haya un único sitio donde verla. Repite la entrevista **simulada** de Carmen (`src/lib/guion.ts`) en un minuto aproximadamente. Las voces son audios grabados una sola vez con ElevenLabs (`public/demo/carmen/`), así que en la demo no se gasta ningún crédito. Si falta el audio de un turno, se usa la voz del navegador como respaldo. Para grabarlos o regrabarlos, desde `backend/`: `python scripts/generar_audios_demo.py --voz-carmen <ID> --aplicar`. La clave necesita el permiso «Text to Speech»; sin `--aplicar` solo cuenta los caracteres. Se ve la pregunta del asistente y la respuesta de Carmen, y su perfil de ejemplo (`carmen-68`, calculado por el backend) se va reconstruyendo dato a dato a medida que se oye la frase que justifica cada uno (`src/lib/demo.ts`). Tiene pausa, salto al siguiente turno, velocidad (1×, 1,5× y 2×) y botón para quitar el sonido. No escribe nada en el backend.

## Voz con ElevenLabs: lo comprobado y lo pendiente

Comprobado leyendo los tipos del SDK instalado (`@elevenlabs/react` 1.21.1), sin cuenta todavía:
- `useConversation` dentro de `ConversationProvider`; `startSession({ signedUrl })` para un agente privado o `startSession({ agentId })` para uno público.
- `onMessage` entrega `{ message, role: "user" | "agent" }` **sin tiempos**. Los marcamos en el cliente: el turno del cliente va desde que el agente pasa a `listening` hasta que llega su transcripción. Es una **aproximación**.
- Existen `sendUserMessage` (respuesta escrita dentro de la sesión de voz), `sendContextualUpdate` (las alertas del verificador se pasan al agente para que las explique) y `getId()` (id de conversación, útil para recuperar el audio después).

Pendiente con la cuenta Creator:
- [ ] Crear el agente en español con Claude como modelo y el prompt de Hammad.
- [ ] Probar `GET /api/voice/signed-url` del backend con la clave real.
- [ ] Probar en un móvil real (HTTPS).
- [ ] Decidir el audio de las evidencias: el que guarda ElevenLabs para cada conversación o una grabación propia en el navegador.
- [ ] Minutos disponibles del plan.


## Propuesta de memoria y permisos integrada localmente

El cliente usa credenciales de posesión por cliente (no identidad real), separadas de los metadatos. La memoria exige consentimiento explícito y ETag/If-Match; un 412 exige revisar y decidir. El bootstrap sustituye la antigua URL de voz sin sesión. La demo usa una fixture fija ficticia, separada del Carmen persistido.

La validación en el navegador está bloqueada hasta acordar un permiso independiente de asesor. El servidor de Next no añade credenciales privilegiadas a las peticiones del cliente.

Contrato, evidencia y límites: [memoria-personal-seguridad.md](../docs/memoria-personal-seguridad.md).
Pruebas de contrato sin proveedores: `npm run test:contrato`.

La demo anónima usa `/api/demo/profile` y `/api/demo/constraints`, sin capa personal y sin depender
del estado guardado de Carmen. `sessionStorage` conserva la credencial de posesión; `localStorage`
solo metadatos. No hay recuperación por ID, renovación ni revocación individual.

Después del build, `IDONEO_PYTHON=/ruta/al/python-instalado npm run test:integracion` inicia
Next y uvicorn propios en puertos efímeros, solo con datos y claves ficticios. Comprueba render de
servidor y contrato HTTP, sin navegador ni proveedores. No utiliza ni detiene la demo en 3000/8000.

La prueba `npm run test:navegador` utiliza Chromium/Playwright existentes contra frontend/backend
aislados, con `IDONEO_FRONT_URL`, `IDONEO_API_URL` y, si es necesario, las rutas
`IDONEO_PLAYWRIGHT_MODULE` e `IDONEO_BROWSER_EXECUTABLE`. Incluye navegación real en escritorio y
móvil emulado, demo, memoria, conflictos y permisos. Requisitos, defectos reproducidos y límites:
la PR #21 (informe de validación en el historial de Git).
