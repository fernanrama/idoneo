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
| `/` | Inicio de la app (maqueta) con la entrada a la feature |
| `/onboarding` | Explicación, aviso de IA y consentimiento de grabación |
| `/onboarding/entrevista` | Entrevista: micrófono, subtítulos, barra de bloques, alerta, respuesta escrita y **demo guiada** |
| `/onboarding/perfil` | Resumen para el cliente y preferencias de memoria consentida/revocable |
| `/onboarding/productos` | Filtros del perfil. **No consulta el MCP de MyInvestor por código**: sus términos lo prohíben (ver `docs/proyecto/05_MCP_MYINVESTOR.md`) |
| `/entidad/[cid]` | Vista de la entidad: datos con fuente, confianza y evidencia, restricciones y validación |

## Validar el perfil con el backend protegido

Si el backend tiene `ADMIN_TOKEN` (obligatorio con URL pública), pon **el mismo valor** en `frontend/.env.local` como `ADMIN_TOKEN` (sin `NEXT_PUBLIC_`). El botón «Validar perfil» y el reinicio de la demo pasan por rutas del propio front (`src/app/api/entidad/`), que añaden la cabecera `X-Admin-Token` en el servidor: el token nunca llega al navegador. Esas rutas solo aceptan peticiones a `localhost`, así que aunque el front se exponga por un túnel nadie de fuera puede validar perfiles.

## Dónde está cada cosa

- `src/tema/tema.css`: **todo el aspecto visual**. Al recibir las pantallas de MyInvestor, cambiar aquí los tokens y, si hace falta, `src/components/ui.module.css`. El flujo no se toca.
- `src/lib/useEntrevista.ts`: lógica de la entrevista (voz de ElevenLabs o guion), envío de turnos, sondeo del perfil y paso de alertas al agente.
- `src/lib/guion.ts`: guion de Carmen (**simulado**). Se sustituirá por `backend/eval/carmen.json` de Pablo.
- `src/lib/api.ts` y `src/lib/tipos.ts`: cliente y tipos del contrato (`docs/CONTRATOS.md`).

## Demo guiada
"Ver demo guiada" reproduce el guion de Carmen turno a turno **contra el backend real**. Mientras el extractor (Hammad) sea un stub, el perfil no se rellenará solo: la vista de la entidad usa el perfil simulado `carmen-68`.

## Voz con ElevenLabs y memoria

Comprobado con tipos y tests locales del SDK instalado (`@elevenlabs/react` 1.21.1), todavía sin credenciales reales en este entorno:
- `useConversation` dentro de `ConversationProvider`; el front usa `startSession({ signedUrl|agentId, userId, dynamicVariables })`.
- `POST /api/voice/bootstrap` entrega URL temporal, ID seudónimo y una proyección mínima de preferencias; el fallback público obtiene el mismo contexto de `/api/voice/context/{sid}`.
- La memoria vive en el backend y la pantalla de perfil permite consentimiento, rectificación y borrado. `localStorage` solo conserva la referencia de sesión/cliente, no los datos de memoria.
- `onMessage` entrega `{ message, role: "user" | "agent" }` **sin tiempos**. Los marcamos en el cliente: el turno del cliente va desde que el agente pasa a `listening` hasta que llega su transcripción. Es una **aproximación**.
- Existen `sendUserMessage` (respuesta escrita dentro de la sesión de voz), `sendContextualUpdate` (las alertas del verificador se pasan al agente para que las explique) y `getId()` (id de conversación, útil para recuperar el audio después).

Pendiente con la cuenta real:
- [ ] Ejecutar `python scripts/sincronizar_voz.py --crear` o `--aplicar` y comprobar prompt/placeholders en el panel.
- [ ] Configurar el post-call webhook hacia `/api/webhooks/elevenlabs` y verificar un evento real.
- [ ] Probar en un móvil real (HTTPS).
- [ ] Decidir el audio de las evidencias: el que guarda ElevenLabs para cada conversación o una grabación propia en el navegador.
- [ ] Minutos disponibles del plan.
