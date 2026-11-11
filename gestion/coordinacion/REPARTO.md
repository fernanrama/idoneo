# Reparto de desarrollo — 4 roles, 5 personas en código

Versión del 8/11/2026. Hay cuatro módulos con dueño. Cada uno trabaja sobre los contratos de [CONTRATOS.md](../../docs/contratos.md) y puede empezar **ya**, porque el backend v0 arranca con un perfil simulado de Carmen.

| Rol | Persona | Módulo | Rutas que escribe |
|---|---|---|---|
| **A · Perfil y backend** | **Juan** | Perfil versionado, evidencias, cálculos, API | `backend/app/perfil/`, `backend/app/main.py`, `backend/fixtures/`, `backend/tests/` |
| **B1 · Entrevistador y extractor** | **Hammad** | Guion del entrevistador, extractor, cliente común de Claude, modo texto | `backend/app/agentes/prompts/`, `extractor.py`, `claude.py`, `chat.py` |
| **B2 · Verificador y medición** | **Pablo** | Verificador, resumen para agentes, medición con perfiles sintéticos | `backend/app/agentes/verificador.py`, `contexto.py`, `backend/eval/` |
| **C · Voz y móvil** | **Fernán** | App Next.js móvil, voz ElevenLabs, panel de perfil y validación | `frontend/` |
| **D · MCP, MyInvestor, despliegue e integración** | **Alejandro** | MCP de Idóneo, conexión con MyInvestor en Claude, URL pública, unión de todo, revisión de PR, README y ZIP de entrega | `backend/app/mcp/`, despliegue, `README.md` |
| **Fuera del código** | **Rodrigo** (propuesta) | Pitch, PowerPoint, PDF de una cara, guion de la demo, revisión financiera y normativa (artículos citados, supuestos de cálculo) | `gestion/comunicacion/`, `gestion/aprendizaje/` |

Si alguien necesita cambiar algo fuera de sus rutas, se lo pide al dueño o abre una PR pequeña y le avisa. Hammad y Pablo comparten `backend/app/agentes/`: el cliente de Claude (`claude.py`) lo crea Hammad primero y Pablo lo reutiliza.

---

## A · Perfil y backend

**Objetivo:** que el perfil sea lo que nos diferencia de un formulario. Cada dato lleva su fuente, su confianza y la prueba de audio, y queda versionado.

- **Hoy:**
  - Leer `modelos.py`, `store.py` y `calculos.py`, y arrancar la API.
  - Revisar con tutoría los supuestos de los cálculos (colchón, capacidad de pérdida, topes de riesgo).
  - Sustituir el volcado JSON por SQLite si lo ves necesario, sin cambiar las funciones de `store`.
- **Lunes:**
  - Endpoint SSE `/api/sessions/{sid}/events` (`profile_updated`, `alert_raised`) para que el panel se actualice en vivo sin sondeo.
  - Guardar el audio de la sesión y servir `/api/sessions/{sid}/audio`, según el resultado de la prueba de voz de C.
- **Martes:**
  - Exportar el expediente (JSON y, si da tiempo, PDF).
  - Escribir 8–10 perfiles sintéticos en `fixtures/` para la evaluación.
- **Terminado cuando:** las versiones no se pierden; un perfil validado y luego modificado pasa a `review_pending`; los tests cubren las reglas y los cálculos.

## B · Agentes IA (B1 Hammad · B2 Pablo)

**Objetivo:** el 15 % de "IA frontera". Un entrevistador que **comprueba** en vez de preguntar, y un verificador que detecta lo declarado frente a lo demostrado.

- **Hoy:**
  - **Hammad:**
    - Crear `claude.py`, el cliente común de Claude que lee el modelo de las variables de entorno.
    - Escribir `prompts/entrevistador.md`: el guion por bloques, las preguntas de comprobación, el aviso de IA y el consentimiento. Pásaselo a Fernán (C), que lo carga en el agente de ElevenLabs.
    - Implementar `extractor.extraer` con uso de herramientas, devolviendo `ActualizacionCampo` con cita y tiempos.
  - **Pablo:**
    - Escribir la transcripción completa de Carmen (`backend/eval/carmen.json`), con turnos y tiempos. Es la prueba común de los dos.
    - Empezar el verificador con Claude: incoherencias, falta de datos y declarado frente a demostrado.
- **Lunes:**
  - **Hammad:** `POST /api/sessions/{sid}/chat` para el modo texto; coordinar la ruta con Juan (A).
  - **Pablo:** cerrar el verificador y `contexto.resumen` con Claude.
- **Martes, sobre todo Pablo:**
  - Medir con los perfiles sintéticos: aciertos por campo, alertas correctas y falsas, latencia y coste por entrevista.
  - Apuntar los resultados en `gestion/evaluacion/PLAN_Y_EVIDENCIAS.md`.
- **Reglas:**
  - El modelo nunca pone números calculados.
  - Si la confianza es baja, el agente vuelve a preguntar en lugar de inventar.
  - Los modelos se eligen por variable de entorno (`MODEL_EXTRACTOR`, `MODEL_VERIFICADOR`).
- **Terminado cuando:** la entrevista de Carmen extraída de un texto da el perfil del fixture con al menos la alerta clave ("eso no puede pasar, el fondo es del banco").

## C · Voz y móvil

**Objetivo:** lo que ve el jurado. La entrevista en un móvil proyectado y un panel donde el perfil se rellena en vivo.

- **Hoy, prueba de riesgo (lo primero):**
  - Montar un agente de ElevenLabs en español que funcione en el navegador del móvil.
  - Averiguar cómo nos llega la transcripción con tiempos (eventos del SDK, websocket o webhook) y si podemos usar Claude como modelo del agente.
  - Averiguar cómo obtener el audio para reproducir las evidencias.
  - Apuntar el resultado en `frontend/README.md`.
- **Hoy, después:**
  - `npx create-next-app frontend` y una pantalla de entrevista con botón grande, subtítulos y barra de bloques.
  - Enviar cada turno a `POST /turns`.
- **Lunes:**
  - Panel `/perfil/[cid]` con campos, fuente, confianza y alertas. Al pulsar un dato suena su clip.
  - Botón de validación del asesor.
  - Modo texto equivalente para cada pregunta.
- **Martes:** accesibilidad (letra grande, contraste, subtítulos siempre visibles, voz más lenta), revisión en un móvil real y vídeo de respaldo.
- **Plan B de voz:** reconocimiento de voz del navegador + respuesta de B + voz de ElevenLabs.
- **Terminado cuando:** una entrevista hablada desde el móvil rellena el perfil en el panel sin tocar el ordenador.

## D · MCP, MyInvestor, despliegue e integración

**Objetivo:** el final de la demo. Claude lee las restricciones de Idóneo y filtra productos **reales** de MyInvestor. D también garantiza que todo arranca con el README.

- **Hoy, prueba de riesgo:**
  - Conectar `https://mcp.myinvestor.es/mcp` en Claude y anotar sus herramientas y campos: ¿nivel de riesgo, plazo, coste?
  - Montar `backend/app/mcp/` con las 4 herramientas, llamando a `store` y `calculos`.
  - Conectarlo en Claude mediante una URL pública temporal.
- **Lunes:**
  - Desplegar el backend con una URL estable. El servicio está por decidir y contratarlo requiere autorización.
  - Recorrido completo en Claude: "busca en MyInvestor productos que encajen con Carmen" → respeta el SRI máximo y las exclusiones.
  - Integrar A, B y C.
- **Martes:**
  - README de entrega con instalación, configuración, ejecución y pruebas.
  - Probar el ZIP descargado de GitHub en una carpeta limpia.
- **Miércoles:** congelar el código hacia las 18:00, probar el ZIP final y entregar con margen.
- **Terminado cuando:** desde una carpeta limpia, siguiendo solo el README, se reproduce la demo completa.

---

## Cómo trabajamos con Git

- `main` siempre arranca. Cada uno trabaja en su rama: `feat/a-sse`, `feat/b-extractor`, `feat/c-entrevista`, `feat/d-mcp`, etc.
- PR pequeñas y frecuentes, como mínimo una al día por persona. Revisa Alejandro (integración) u otra persona del equipo.
- Las ramas nuevas salen siempre del `main` actual. La rama `hammad-cobo-agente` se creó desde el `main` anterior a la reorganización: actualizarla con `git rebase origin/main`, o recrearla, antes de trabajar en ella.
- Antes de abrir la PR, `pytest` pasa en `backend/`, y el front compila si lo has tocado.
- Nunca subir `.env`, claves ni datos reales de personas. Lo simulado se marca como simulado.
- Si te bloqueas más de 30 minutos, avisa al grupo y trabaja contra el stub o el fixture.

## Hitos comunes

| Cuándo | Qué debe funcionar |
|---|---|
| Domingo noche | Las 3 pruebas de riesgo (voz, MCP de MyInvestor, MCP propio) con resultado escrito, y el extractor sobre texto |
| Lunes noche | Recorrido completo: hablar → perfil en el panel → validar → Claude filtra MyInvestor |
| Martes noche | Medición real, accesibilidad, vídeo de respaldo y primer ensayo de la demo |
| Miércoles 18:00 | Código congelado; ZIP probado en limpio; entrega antes de las 22:00 |

Las otras dos personas del equipo, fuera del desarrollo, pueden encargarse de:
- revisar la normativa y los cálculos (tutoría);
- el pitch, el PowerPoint, el PDF de una cara y el guion de la demo (comunicación).
