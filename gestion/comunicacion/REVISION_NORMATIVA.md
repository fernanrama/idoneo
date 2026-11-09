# Revisión normativa del pitch

9 nov 2026 · Responsable: Rodrigo (revisión financiera y normativa, según `docs/REPARTO.md`)

> **Qué es esto.** Contraste de las citas legales de `docs/DISENO.md` y `docs/proyecto/02_AUDITORIA_Y_DECISIONES.md` con el **texto oficial** (EUR-Lex y BOE), leído en el navegador el 9/11/2026. El diseño las citaba "de memoria" y la auditoría la hizo una IA.
> **Qué NO es.** No es asesoramiento jurídico. Es una comprobación de que lo que decimos coincide con lo que dicen los textos. Lo que depende de una decisión legal de la entidad (base jurídica, grabación) se marca como tal.
> **Cómo leerlo.** ✔ confirmado en el texto oficial · ⚠ matiz o corrección · ✖ no se puede decir así · ❓ no pude verificarlo.

## Resumen en cinco líneas

1. **Casi todo lo que decía el diseño es correcto**: MiFID II 25.2, 25.6, Reglamento Delegado 2017/565 arts. 54.12 y 55, Reglamento 2021/1253, Ley 6/2023 y RGPD.
2. **Hay una cita mejor que la del diseño**: el **art. 54.7 del Reglamento Delegado 2017/565** (ley) obliga a asegurar que la información del cliente sea **fiable** (herramientas bien diseñadas, preguntas comprensibles, comprobar la coherencia). Es el respaldo directo de lo que hace Idóneo, junto a las directrices de ESMA 2023 (recomendaciones).
3. **Una afirmación no se sostiene**: "Registro de toda la evaluación: arts. 72 a 76". Los artículos 73-76 no exigen eso (ver la fila 8).
4. **ESMA 2023 verificado** (ESMA35-43-3172, leído en el PDF oficial): la **directriz general 4** pide fiabilidad "sin depender indebidamente de la autoevaluación del cliente", el **párrafo 46** pide contrastarla con criterios objetivos y el **párrafo 52** advierte de que el riesgo de sobrevaloración es **mayor en sistemas automatizados con poca interacción humana**.
5. **Ley de IA**: el aviso de IA (art. 50.1) **se aplica desde el 2 de agosto de 2026** y el aplazamiento de 2026 solo afectó al alto riesgo.

## Tabla de comprobaciones

| # | Lo que decía el diseño | Qué dice el texto oficial | Veredicto |
|---|---|---|---|
| 1 | MiFID II, **art. 25.2**: conocimientos y experiencia, situación financiera (incl. capacidad de soportar pérdidas) y objetivos (incl. tolerancia al riesgo) | Coincide. Se aplica al asesoramiento y a la gestión de carteras | ✔ |
| 2 | **Conveniencia** para servicios distintos del asesoramiento | **Art. 25.3** MiFID II: se pide información sobre conocimientos y experiencia para evaluar si el producto es conveniente | ✔ (el diseño no citaba el artículo) |
| 3 | MiFID II **art. 25.6**: informe de idoneidad antes de la operación | Declaración de idoneidad en soporte duradero antes de la operación, al asesorar | ✔ |
| 4 | MiFID II **art. 25.5** como base del "registro del expediente" (auditoría) | El 25.5 es el registro del **acuerdo** con el cliente (derechos y obligaciones). Lo desarrolla el art. 73 del Reglamento Delegado | ⚠ No es la base del registro de la evaluación |
| 5 | Reglamento Delegado **2017/565, arts. 54 y 55** | Art. 54: evaluación e informes de idoneidad. Art. 55: disposiciones comunes para idoneidad y conveniencia (tipos de servicios conocidos, naturaleza, volumen y frecuencia de operaciones, formación y profesión) | ✔ |
| 5a | **Art. 54.12**: informe de idoneidad | Al asesorar a un minorista, informe con resumen del asesoramiento y por qué es idóneo | ✔ |
| 5b | "Sin información suficiente, no se recomienda" (art. 54) | **Art. 54.8**: si no se obtiene la información requerida, la entidad no recomendará | ✔ (es el 54.8) |
| 6 | "No fiarse solo de la autoevaluación" (atribuido a ESMA 2023) | **Art. 54.7** (Reglamento Delegado): medidas razonables para que la información sea fiable: (a) concienciar al cliente, (b) herramientas bien diseñadas, (c) preguntas comprensibles, (d) comprobar la coherencia. Con relación continua, políticas para mantener la información actualizada. **ESMA 2023, directriz general 4 (párr. 44):** la información debe ser fiable y consistente «sin depender indebidamente de la autoevaluación del cliente»; **párr. 46:** la autoevaluación debe contrapesarse con criterios objetivos | ✔ El diseño tenía razón. Se citan **las dos fuentes** |
| 7 | **Art. 56** (no citado) | Conveniencia y obligaciones de registro: 56.2 pide registrar el resultado y las advertencias hechas al cliente | ➕ Añadir para la conveniencia |
| 8 | "Registro de toda la evaluación: **arts. 72 a 76**" | **72**: conservar registros de forma que se puedan reconstruir y verificar correcciones (✔ apoya el versionado). **73**: derechos y obligaciones. **74-75**: órdenes y operaciones. **76**: política de grabación de conversaciones, que remite al art. 16.7 de MiFID II, cuyo régimen se refiere, según el considerando, a conversaciones **ligadas a órdenes de clientes** | ✖ 73-76 no exigen registrar toda la evaluación. **Grabar la entrevista es una decisión de diseño** (con consentimiento), no una exigencia de esos artículos |
| 9 | Reglamento Delegado **2021/1253** (preferencias de sostenibilidad) | De 21/4/2021, DOUE 2.8.2021. Modifica el art. 54.2.a para incluir las preferencias de sostenibilidad. Aplicable desde el **2/8/2022** | ✔ |
| 10 | **Ley 6/2023** de los Mercados de Valores y de los Servicios de Inversión | De 17 de marzo (BOE-A-2023-7053). Sección 5.ª "Evaluación de la idoneidad y la conveniencia": **art. 203** (conocer al cliente), **204** (idoneidad, igual que el 25.2 de MiFID II), **205** (conveniencia), **206** (registro de la conveniencia) | ✔. ❓ "Traspone MiFID II": no lo comprobé; decir "regula" |
| 11 | **Directrices de ESMA 2023** (ESMA35-43-3172, fechadas el 23/9/2022 y publicadas el 3/4/2023) | Leído el PDF oficial (33 páginas). **Párr. 52:** las entidades deben adoptar mecanismos contra la tendencia a **sobrevalorar** conocimientos y experiencia (por ejemplo, preguntas que midan la comprensión real), y esto es **especialmente importante en el robo-advice**, porque el riesgo es mayor cuando el cliente da la información mediante un sistema automatizado o semiautomatizado con poca o ninguna interacción humana | ✔ **Argumento fuerte para Idóneo**: es justo ese mecanismo |
| 12 | **RGPD**: obligación legal para la capa MiFID, consentimiento para la personal | **Art. 6.1**: (a) consentimiento, (b) contrato, (c) obligación legal. **Art. 9**: biométricos solo si identifican de forma unívoca (por eso "la voz no se usa para identificar" es una buena salvaguarda). **Art. 22**: derecho a no ser objeto de decisiones solo automatizadas (por eso valida una persona) | ✔. ⚠ La base jurídica la decide la entidad (responsable del tratamiento) |
| 13 | **Ley de IA, art. 50**: aviso de IA | **Art. 50.1** (Reglamento 2024/1689): las personas deben saber que interactúan con una IA. **Art. 113**: aplicable desde el **2/8/2026**. El **Reglamento 2026/1744** (Digital Omnibus, verificado en EUR-Lex) aplaza el alto riesgo del Anexo III al 2/12/2027 y da 4 meses de transición solo al **marcado de contenido generado (art. 50.2)** | ✔ El aviso de IA es obligatorio desde agosto de 2026 |
| 14 | El perfilado para invertir **no** es alto riesgo (Anexo III) | El punto 5 del Anexo III (texto original) lista: prestaciones públicas, **solvencia crediticia** y **seguros de vida y de salud**. No aparece el perfilado de inversión | ✔ con cautela: es lo que dice el texto; no es una opinión jurídica de que nunca pueda serlo |

## Frases seguras para decirlo en el pitch

- ✔ «El Reglamento Delegado 2017/565 obliga a las entidades a tomar medidas para que la información del cliente sea fiable, y ESMA añade que no se debe depender indebidamente de la autoevaluación: hay que contrastarla con criterios objetivos.»
- ✔ «ESMA advierte de que el riesgo de sobrevaloración es mayor en sistemas automatizados con poca interacción humana. Idóneo es el mecanismo que lo compensa: comprueba hablando.»
- ✔ «Idóneo ayuda a **recoger y documentar** esa evaluación; la responsabilidad sigue siendo de la entidad y un asesor valida el perfil.»
- ✔ «Cubre los dos test: idoneidad (art. 25.2) y conveniencia (art. 25.3).»
- ✔ «El aviso de que es una IA es obligatorio desde agosto de 2026 (art. 50 de la Ley de IA) y lo damos al empezar.»
- ✖ No decir: «cumple MiFID», «la ley exige grabar la entrevista», «la Ley 6/2023 traspone MiFID II». Las directrices de ESMA no son ley: son recomendaciones que las autoridades nacionales aplican («ESMA recomienda», no «la ley obliga»).

## Qué cambia en los entregables

| Dónde | Cambio |
|---|---|
| Diapositiva 2 y PDF de una cara | Sustituir la etiqueta «verificar ESMA 2023» por la cita **Reg. Delegado 2017/565 (art. 54.7) y directrices de ESMA de 2023** (hecho) |
| `PITCH_GUION.md` (diapositiva 2) | Idem: quitar `[VERIFICAR: ESMA 2023]` (hecho) |
| `docs/DISENO.md` (dueño: Alex) | **Propuesta, no la toco yo:** corregir la fila "Registro" (arts. 72-76), añadir 54.7, 54.8 y 56, y quitar "traspone" de la Ley 6/2023 |
| `PREGUNTAS_JURADO.md` | Usar las frases seguras de arriba |

## Pendiente de verificar (lo puedes hacer tú en 10 minutos)

1. **Art. 16.7 de MiFID II**: leer su alcance exacto (yo solo vi el considerando que lo liga a órdenes de clientes).
2. **Texto articulado del Reglamento 2026/1744**: solo leí sus considerandos en EUR-Lex.
3. **¿Es Idóneo un "proveedor" o un "responsable del despliegue" en la Ley de IA?** El art. 50.1 obliga al proveedor; cambia quién debe cumplirlo. Es una cuestión legal que no resuelvo aquí.

## Fuentes (todas leídas el 9/11/2026)

- MiFID II, Directiva 2014/65/UE: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32014L0065
- Reglamento Delegado (UE) 2017/565: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32017R0565
- Reglamento Delegado (UE) 2021/1253: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32021R1253
- Ley 6/2023 (BOE-A-2023-7053): https://www.boe.es/buscar/act.php?id=BOE-A-2023-7053
- RGPD, Reglamento (UE) 2016/679: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32016R0679
- Ley de IA, Reglamento (UE) 2024/1689: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:32024R1689
- Reglamento (UE) 2026/1744 (Digital Omnibus de IA): https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:32026R1744
- Directrices de ESMA sobre idoneidad (ESMA35-43-3172, 23/9/2022), PDF oficial: https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf (el PDF descargado está en la raíz del repo y **no se sube a git**)
- Fechas de la Ley de IA tras el aplazamiento: varias consultoras coinciden (fuentes secundarias); lo primario es el Reglamento 2026/1744.
