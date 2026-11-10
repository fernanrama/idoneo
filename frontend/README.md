# Frontend — Idóneo (rol C, Fernán)

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
| `/` | Portada oscura del producto: el aura lanza preguntas de ejemplo; enlaces a la entrevista, la demo guiada y la vista de la entidad |
| `/onboarding` | Redirige a la entrevista (el aviso de IA y el consentimiento están ahora en su pantalla de inicio) |
| `/onboarding/entrevista` | Entrevista con el aura: solo la pregunta actual, por voz o **por escrito** (modo texto, necesita la clave de Claude en el backend) y **demo guiada** |
| `/onboarding/perfil` | Perfil para el cliente, en claro: medidor de riesgo, lo que hemos entendido con la frase de cada dato, avisos y siguiente paso |
| `/onboarding/productos` | Filtros del perfil. **No consulta el MCP de MyInvestor por código**: sus términos lo prohíben (ver `docs/proyecto/05_MCP_MYINVESTOR.md`) |
| `/escenario` | Pantalla partida para el pitch: entrevista a la izquierda y lo que recibe la entidad, en directo, a la derecha. `?cliente=<id>` muestra un perfil ya existente |
| `/entidad/[cid]` | Vista de la entidad con pestañas: resumen, evidencias (frase y audio), historial de versiones y lo que ve su agente por MCP; validación |

## Validar el perfil con el backend protegido

Si el backend tiene `ADMIN_TOKEN` (obligatorio con URL pública), pon **el mismo valor** en `frontend/.env.local` como `ADMIN_TOKEN` (sin `NEXT_PUBLIC_`). El botón «Validar perfil» y el reinicio de la demo pasan por rutas del propio front (`src/app/api/entidad/`), que añaden la cabecera `X-Admin-Token` en el servidor: el token nunca llega al navegador. Esas rutas solo aceptan peticiones a `localhost`, así que aunque el front se exponga por un túnel nadie de fuera puede validar perfiles.

## Dónde está cada cosa

- `src/tema/visual.css`: tokens del tema oscuro (`.tema-noche`), clases `.mono`, `.vidrio` y todas las animaciones (`v-*`). Con «reducir movimiento» activado se apagan.
- `src/components/visual.tsx`: piezas del tema oscuro (`Noche`, `Aura`, botones, iconos). `Entrevista.tsx` y `PanelVivo.tsx` son la entrevista y el panel en directo; `BarraCliente.tsx` y `cliente.module.css`, las pantallas claras del cliente.
- `public/visual/`: imágenes 3D (aura, cápsula, cinta) en WebP.
- `src/tema/tema.css` y `src/components/ui.*`: estilo anterior; ninguna pantalla lo usa ya, se mantiene hasta que Fernán decida si se borra.
- `src/lib/useEntrevista.ts`: lógica de la entrevista (voz de ElevenLabs o guion), envío de turnos, sondeo del perfil y paso de alertas al agente.
- `src/lib/guion.ts`: guion de Carmen (**simulado**). Se sustituirá por `backend/eval/carmen.json` de Pablo.
- `src/lib/api.ts` y `src/lib/tipos.ts`: cliente y tipos del contrato (`docs/CONTRATOS.md`).

## Demo guiada
"Ver demo guiada" reproduce el guion de Carmen turno a turno **contra el backend real**. Mientras el extractor (Hammad) sea un stub, el perfil no se rellenará solo: la vista de la entidad usa el perfil simulado `carmen-68`.

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
