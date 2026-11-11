# Guion de la demo — 2:15

Borrador v1 · 10 nov 2026 · Responsable: Rodrigo (lleva la demo) · Complementa a [`PITCH_GUION.md`](PITCH_GUION.md)

> **Regla de oro.** La demo es la **misma versión que se entrega** (ZIP de GitHub). Carmen y sus datos son **simulados**, y se dice en voz alta.
> **Idea.** La demo guiada repite una conversación grabada en el guion (`frontend/src/lib/guion-carmen.json`). No es la voz en directo: se dice «ejecución guiada». La voz real se enseña solo si hay tiempo (versión de 7 min).

## Estado de cada pieza (a 10/11, comprobado en local)

| Pieza | Estado | Si falla |
|---|---|---|
| `/escenario`: cliente a la izquierda, entidad a la derecha | ✔ Funciona | Vídeo de respaldo |
| **Demo guiada** (19 pasos, ~55 s a 1×) | ✔ Funciona, sin claves. **No escribe en el backend** | Vídeo de respaldo |
| Panel de la entidad se rellena durante la demo guiada | ✔ Los datos salen a partir del paso 8-9 (antes son avisos y objetivo) | — |
| Vista de la entidad (`/entidad/carmen-68`): aviso, idoneidad, conveniencia | ✔ Funciona con el perfil precargado | — |
| Validar perfil (pasa a activo) | ✔ Funciona con el **modo asesor de demostración** (PR 25, apagado por defecto): `DEMO_ADVISOR_MODE=1` y el mismo `DEMO_ADVISOR_TOKEN` en `.env` y `frontend/.env.local`. Solo desde el propio portátil. **Un solo clic**: un segundo clic seguido puede dar error 409. **Reiniciar antes de salir** | Perfil ya activo: se explica sin pulsar |
| Pestaña **Agente · MCP** (lo que recibe el agente) | ✔ Funciona | Es el plan B del paso de Claude |
| Voz real con ElevenLabs | ✔ Probada **una vez** de punta a punta (E-03). Necesita claves y saldo | Demo guiada |
| **Entrevista corta** sobre `carmen-corta` (versión de 7 min) | ✔ Probada por escrito con Claude real (E-08): unos 45 s, va directo a lo que falta y llega a «Pendiente de validar» con el aviso. Falta ensayarla **por voz**. Casilla «Entrevista corta del pitch» en `/escenario` (modo asesor) | Demo guiada |
| Claude + conectores Idóneo y MyInvestor | ⚠ Probado el 9/11 por **túnel temporal**, antes de la PR 21. Desde la PR 21 `/mcp` exige credencial (sin ella responde 401). `[PENDIENTE: Juan está comprobando cómo conectar Claude.ai con la autenticación nueva]` | Pestaña Agente · MCP |
| Clip de audio al pinchar un dato | ✘ Pendiente | Se enseña la frase escrita |
| Sonido de la demo guiada | Voz del navegador (no hay audios grabados) | Quitar el sonido y leer los subtítulos |

## Pestañas preparadas (en este orden)

```
[1] PowerPoint (presentación)     [2] /escenario          [3] /entidad/carmen-68     [4] Claude con el prompt escrito
     diapositivas 1-8      ->  demo guiada (0:05)  ->  validar (1:05)        ->  conectores (1:45)
```

## Antes de salir (checklist, 15 min)

- [ ] Backend y front arrancados **desde el ZIP final**, en carpeta limpia. Front con `npm run build` y `npm start -- -H 127.0.0.1` (sin la insignia «N» del modo desarrollo y escuchando solo en el portátil: con el modo asesor activo no debe quedar expuesto a la wifi del aula).
- [ ] Modo asesor de demostración activo: en el registro del backend sale «MODO ASESOR DE DEMO ACTIVO». **Después del pitch, apagarlo** (`DEMO_ADVISOR_MODE=0` en los dos archivos).
- [ ] Carmen en estado inicial (`pending_validation`): botón **«Reiniciar la demo»** de la vista de la entidad. Alternativa por terminal: `POST /api/demo/reset` con la cabecera `X-Admin-Token` (obligatoria: sin `ADMIN_TOKEN` configurado responde 503). **No abrir `/docs` en el proyector.**
- [ ] Recargar la pestaña 3 y comprobar que pone **«Pendiente de validar»**.
- [ ] Túnel levantado y URL nueva puesta en el conector de Idóneo en Claude. Probar el prompt una vez.
- [ ] Navegador a pantalla completa (F11) y zoom 110-125 % para que se lea desde el fondo.
- [ ] Sonido: decidido en el ensayo (voz del navegador o silencio con subtítulos).
- [ ] Hotspot propio por si falla el wifi del aula (Claude y el túnel necesitan red; la demo guiada no).
- [ ] Vídeo de respaldo abierto en otra ventana y probado con sonido.
- [ ] Ningún `.env`, clave, correo ni notificación visible en pantalla. Modo «no molestar» activado.

## Pasos

| Min | Qué se hace | Qué se ve | Qué se dice (resumen) |
|---|---|---|---|
| 0:00 | Salir del PowerPoint a la pestaña 2 (`/escenario`) | Pantalla partida: aura a la izquierda, «Perfil inversor, esperando datos» a la derecha | «Izquierda, lo que vive Carmen. Derecha, lo que recibe la entidad. Datos simulados.» |
| 0:05 | Pulsar **Ver la demo guiada** | Aviso de IA, objetivo, situación | «Avisa de que es una IA y pide permiso. Carmen quiere un extra para la pensión.» |
| 0:25 | Señalar el panel derecho | Los datos aparecen con su frase | «Cada dato aparece con la frase exacta que lo justifica.» |
| 0:40 | Momento clave (paso 14 de 19) | «Eso no puede pasar, el fondo es del banco» y el aviso | «Había declarado que conocía ese producto. **Declarado no es igual a demostrado.**» |
| 1:00 | Fin de la demo guiada; ir a la pestaña 3 (`/entidad/carmen-68`) | «carmen-68, perfil por validar», aviso ámbar, Conservador, SRI 3 de 7 | «Conservador, riesgo máximo 3 de 7, renta variable no conveniente. Reglas fijas, no el modelo.» |
| 1:20 | Pulsar **Ver la frase** en el aviso | La cita de Carmen | «Cada dato lleva su prueba.» |
| 1:30 | Pulsar **Validar perfil** (una sola vez) | Pasa a validado; aviso «el agente ya puede usarlo por MCP» | «Una persona lo valida. Sin eso, el agente no puede usarlo.» |
| 1:45 | Pestaña 4: Claude con los conectores. Enviar el prompt preparado | Lista de fondos de MyInvestor con riesgo ≤ 3, sin renta variable | «El agente de la entidad usa el perfil. Nosotros no recomendamos.» |
| 2:10 | Cierre | Respuesta de Claude en pantalla | «Eso es Idóneo. Gracias, y encantados de responder a vuestras preguntas.» |

Prompt preparado para Claude Code (pestaña 4, abierto en la carpeta `gcx/demo-claude` con los conectores `idoneo` y `myinvestor`; antes, `export IDONEO_MCP_TOKEN=...` según `docs/modo-asesor-demo.md`): *«Usa Idóneo para leer las restricciones de carmen-68 y busca en MyInvestor fondos de menor riesgo que las cumplan. Responde en 6 líneas como máximo: las restricciones con su evidencia y 3 fondos compatibles.»* Probado el 11/11 (E-09): unos 16 s y 6 líneas, con las frases de Carmen como evidencia. Sin «en 6 líneas» la respuesta es demasiado larga para la demo.

## Datos de Carmen (simulada) que salen en pantalla

- 68 años, 80.000 € en depósitos, objetivo a 10 años.
- Renta variable: **declaró** nivel alto, **demostró** ninguno.
- Tolerancia por escenarios: **1 de 5** (declaró 3). Perfil: **CONSERVADOR**. SRI máximo: **3**.
- Capacidad de pérdida: 74.600 € (calculada). El plazo daría AGRESIVO y la capacidad MUY_AGRESIVO; manda el más restrictivo.
- Lo que recibe el agente por MCP: `max_risk: 3`, `asset_type: ["Monetario", "Renta Fija"]`, `equity_funds: not_appropriate`.

Salen de `backend/fixtures/carmen-68.json` y `calculos.py`. Si alguien cambia los umbrales, **revisar esta lista y la diapositiva 5**.

## Plan B (obligatorio)

| Falla | Qué hacer | Qué decir |
|---|---|---|
| El conector de Claude o el túnel | Pestaña 3 → **Agente · MCP**: enseñar lo que recibe el agente | «Esto es exactamente lo que recibe el agente.» |
| El backend (la entidad no carga) | Vídeo de respaldo desde el minuto de la entidad | «Os enseño la ejecución que grabamos de esta misma versión.» |
| El front entero | Vídeo de respaldo completo | La misma frase |
| La voz real o la entrevista corta (solo versión de 7 min) | Volver a la demo guiada | «Seguimos con la ejecución guiada.» |

El límite de espera es de **10 segundos**: si algo no responde, se pasa al plan B sin disculparse.

## Preguntas que pueden salir al ver la demo

- **«¿Qué son esos porcentajes junto a cada dato?»** Confianza calculada con supuestos del equipo (rúbrica v2), no una medida. Por debajo de 0,65 se marca para revisar.
- **«¿Por qué desaparece el aviso al validar?»** Al validar, la persona da el aviso por revisado. Es intencionado: las alertas abiertas pasan a «resuelta» y queda quién lo validó (`backend/app/perfil/store.py`).
- **«¿Esto es en directo?»** La demo guiada repite una conversación de ejemplo. La voz real funciona y la hemos probado de punta a punta; no la usamos en el pitch para no depender de la red.

## Qué NO enseñar

- Pantallas con claves, `.env`, `/docs` del backend, el panel de ElevenLabs o correos.
- Un perfil real de una persona: solo Carmen (simulada).
- El MCP de MyInvestor llamado desde nuestro código: solo como conector dentro de Claude.

## Vídeo de respaldo

- Grabarlo **de la versión que se entrega**, siguiendo esta tabla, de unos 2:15 (Windows: `Win + Alt + R` con la barra de juegos, u OBS).
- Nombre con fecha y commit: `demo_2026-11-11_<commit>.mp4`. No subirlo al repo si pesa mucho; guardarlo en dos portátiles y en un USB.
- `[PENDIENTE]`: grabarlo el miércoles tras congelar el código (18:00).
