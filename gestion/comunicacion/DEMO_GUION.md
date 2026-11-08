# Guion de la demo — 2:30

Borrador v0 · 8 nov 2026 · Responsable: Rodrigo · Complementa a [`PITCH_GUION.md`](PITCH_GUION.md)

> **Regla de oro.** La demo debe ser la **misma versión que se entrega** (ZIP de GitHub). Datos de Carmen **simulados**, y se dice en voz alta.
> Los pasos marcados `[PENDIENTE]` dependen de funciones que hoy no están terminadas (ver tabla de estado). Si el miércoles siguen así, se usa el plan B de esa fila.

## Estado de cada pieza (a 8/11, comprobado en local)

| Pieza | Estado | Si falla |
|---|---|---|
| Pantallas de la app (inicio, onboarding, entrevista, perfil, entidad) | ✔ Funcionan | — |
| **Demo guiada** (reproduce el guion de Carmen, simulado) | ✔ Funciona | Es el plan B de la voz |
| Vista de la entidad: idoneidad (CONSERVADOR, SRI máx. 3), conveniencia, restricciones | ✔ Funciona con el perfil de Carmen | — |
| Validar perfil (pasa a activo) | ✔ Funciona (probar antes de salir) | Perfil precargado ya activo |
| Voz real con ElevenLabs | ✘ **No probada** (sin cuenta/agente) | Demo guiada |
| El perfil se rellena en directo durante la entrevista | ✘ El extractor aún es un stub | Mostrar el perfil de Carmen ya cargado |
| Clip de audio al pinchar un dato | ✘ Pendiente | Mostrar la cita escrita |
| Claude + conectores Idóneo y MyInvestor | `[PENDIENTE]` (MCP hecho en local; falta URL pública y conector) | Vídeo grabado |

## Antes de salir (checklist, 10 min)

- [ ] Backend y front arrancados desde el ZIP final, en carpeta limpia.
- [ ] `POST /api/demo/reset` ejecutado: Carmen en estado inicial (`pending_validation`).
- [ ] Móvil real con HTTPS (túnel) **o** navegador en vista móvil proyectado.
- [ ] Auriculares con micrófono y un hotspot propio (el wifi del aula puede fallar). El móvil exige HTTPS para el micro.
- [ ] Minutos de ElevenLabs suficientes `[PENDIENTE: saldo]`.
- [ ] Vídeo de respaldo abierto en otra pestaña y probado con sonido.
- [ ] Letra de la app en tamaño grande si se proyecta (botón "Aa").
- [ ] Ningún `.env`, clave ni correo visibles en pantalla.

## Pasos (con el tiempo orientativo)

| Min | Qué se hace | Qué se ve | Qué se dice (resumen) |
|---|---|---|---|
| 0:00 | Abrir la app de Carmen y pulsar **Empezar** | Inicio con "Tu perfil inversor, hablando" | "Esto es el móvil de Carmen. Datos simulados." |
| 0:10 | Pantalla de **aviso de IA y consentimiento**; aceptar | Texto claro, botón grande | "Primero le dice que es una IA y pide permiso para grabar." |
| 0:25 | **Entrevista**. Voz real `[PENDIENTE]`, o **Ver demo guiada** | Subtítulos, barra de bloques, burbujas | "Carmen quiere un dinero extra para la pensión." |
| 0:55 | Momento clave: «*eso no puede pasar, el fondo es del banco*» | **Alerta**: "Algo que conviene aclarar" | "Declaró que conocía la renta variable; acaba de demostrar lo contrario." |
| 1:15 | Abrir **Vista de la entidad** (`/entidad/carmen-68`) | Idoneidad: CONSERVADOR, SRI máx. 3. Conveniencia: renta variable no conveniente | "Los números salen de funciones de cálculo, no del modelo. Manda el criterio más restrictivo." |
| 1:40 | Pulsar **Ver evidencia** de un dato | La cita literal (y el clip `[PENDIENTE]`) | "Cada dato lleva su prueba." |
| 1:55 | Pulsar **Validar perfil** | Estado pasa a "Activo"; restricciones "usables" | "Una persona de la entidad lo valida. Sin validación no es apto." |
| 2:10 | En Claude, con los conectores Idóneo y MyInvestor: «Busca productos que encajen con Carmen» `[PENDIENTE]` | Lista de productos reales filtrados por el riesgo máximo | "El agente de la entidad usa el perfil. Nosotros no recomendamos." |
| 2:30 | Fin de la demo (es lo último del pitch) | Vista de la entidad con el perfil activo | "Eso es Idóneo. Gracias, y encantados de responder a vuestras preguntas." |

## Datos de Carmen (simulada) que salen en pantalla

- 68 años, 80.000 € en depósitos, objetivo a 10 años.
- Renta variable: **declaró** nivel alto, **demostró** ninguno. Renta fija: nivel medio.
- Tolerancia por escenarios: **1 de 5** (declaró 3). Perfil de riesgo: **CONSERVADOR**. SRI máximo: **3**.
- Capacidad de pérdida: 74.600 € (calculada). El plazo daría AGRESIVO y la capacidad MUY_AGRESIVO; manda el más restrictivo.

Estos valores salen de `backend/fixtures/carmen-68.json` y de `calculos.py`. Si alguien cambia los umbrales, **revisar esta tabla**.

## Plan B (obligatorio)

1. **Falla la voz o la red:** pulsar **Ver demo guiada**. Se reproduce el guion de Carmen contra el backend real. Decir: "Esto es una ejecución guiada con datos simulados."
2. **Falla el backend:** vídeo de respaldo grabado de la misma versión. Decir que es una ejecución registrada, no en directo.
3. **Falla el conector de Claude/MyInvestor:** saltar el paso 2:10 y cerrar en la vista de la entidad (ya tiene el valor central).
4. **Frase de transición ante cualquier fallo:** "Esto es justo lo que pasa en directo; os enseño la ejecución que grabamos de esta misma versión."

El límite de espera es de **10 segundos**: si algo no responde, se pasa al plan B sin disculparse.

## Qué NO enseñar

- Pantallas con claves, `.env`, el panel de Supabase o correos.
- Un perfil real de una persona: solo Carmen (simulada).
- El MCP de MyInvestor llamado desde nuestro código: solo como conector dentro de Claude.

## Vídeo de respaldo

- Grabarlo **de la versión que se entrega**, con subtítulos y narración, de 2:30.
- Anotar fecha, hora y commit en el nombre del archivo (por ejemplo `demo_2026-11-10_<commit>.mp4`).
- `[PENDIENTE]`: depende de que el recorrido funcione de punta a punta. No grabarlo antes del martes por la noche.
