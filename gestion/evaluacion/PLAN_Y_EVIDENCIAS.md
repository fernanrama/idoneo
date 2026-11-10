# Plan y evidencias de evaluación

Responsable documental: área 04 · Actualizado: 8 de noviembre de 2026.

## Estado y uso
**Preparado:** plantilla de criterios, ejecuciones, comparación y revisión final. **Pendiente:** enunciado, rúbrica, producto, datos, responsables humanos y umbrales. Primeras ejecuciones del extractor registradas abajo (E-00 a E-05). Los criterios siguientes son propuestas; no constituyen requisitos oficiales ni financieros o regulatorios.

Trabajar por hitos desde la recepción del reto: acordar criterios → probar recorrido completo → comparar y corregir → verificar versión de entrega. Dirección ajustará el calendario al tiempo restante.

## 1. Criterios y casos
Tras recibir el enunciado, estrategia aporta requisitos con fuente; producto concreta comportamientos; tutoría revisa el significado financiero. Evaluación transforma cada promesa prioritaria en un resultado observable antes de ejecutar pruebas.

Duplicar esta fila por caso; los campos entre corchetes están vacíos de contenido real:

| Caso | Criterio y fuente | Entrada y procedencia | Resultado esperado / tolerancia | Prioridad y responsable | Estado |
| --- | --- | --- | --- | --- | --- |
| [ID] | [requisito, página o propuesta] | [referencia; real o simulada] | [comportamiento verificable] | [por acordar] | Pendiente |

Proponer cobertura mínima del recorrido principal, datos ausentes, entradas inválidas y dependencia no disponible. Añadir casos límite pertinentes al producto, sin fabricar escenarios por obligación. Contrastar cálculos deterministas con una referencia independiente, indicando unidades y redondeos. Para respuestas del modelo, definir criterios observables y tratamiento de información insuficiente; una respuesta convincente no demuestra corrección.

## 2. Ejecuciones y evidencias
Registrar cada ejecución con esta ficha:

- **Ejecución / casos / fecha / ejecutor:** [pendiente].
- **Versión exacta:** [commit y estado de cambios locales; si no hay Git, identificador del artefacto o instantánea].
- **Entorno y configuración:** [dependencias relevantes, modelo, parámetros, versión de datos y procedimiento reproducible].
- **Esperado y observado:** [por caso; aprobado, fallido o bloqueado, con motivo].
- **Evidencia:** [ruta o enlace a salida, captura o registro; limitaciones].
- **Mediciones pertinentes:** [muestra, repeticiones, latencia, coste o errores; método de medición].

No registrar secretos ni datos personales financieros. Usar ejemplos sintéticos o referencias seguras. Conservar fallos y repeticiones de salidas variables; no seleccionar solo resultados favorables. Distinguir coste medido de estimado. Una evidencia de otra versión no valida automáticamente la actual.

### Ejecución E-08 · Entrevista corta del pitch por escrito, con Claude real · 11 nov 2026

(E-06 y E-07 están reservadas para la PR #26, del verificador.)

- **Ejecución / casos / fecha / ejecutor:** entrevista corta sobre `carmen-corta` (fixture **simulado**: faltan el conocimiento de renta variable, el escenario de caída y la sostenibilidad), en modo texto. Las respuestas del cliente son un guion fijo escrito por el equipo. Lanzada por Claude Code desde el portátil de Fernán, a través de la ruta de Next `POST /api/entidad/corta` y de `POST /api/sessions/{id}/chat`.
- **Versión exacta:** rama `feat/demo-entrevista-corta` (PR #29), commits `ab333ae` (antes) y `34f2ba3` (después); entrevistador y extractor con los modelos por defecto del `.env`.
- **Antes (`ab333ae`):** el perfil llegó a `pending_validation` con la alerta declarado ≠ demostrado. Pero el entrevistador siguió el guion desde el principio y repitió «¿para qué le gustaría invertir?», que ya constaba. En el cierre dijo que la clienta «conoce» la renta variable.
- **Después (`34f2ba3`):** dice que solo quedan unas preguntas y va directo a conocimiento → comprobación → caída → sostenibilidad. Explica el error con calma y en el cierre no afirma conocimiento. **`pending_validation`, 0 datos que falten, alerta declarado ≠ demostrado abierta**, en unos 43 s (7 turnos).
- **Limitaciones:** una repetición por versión, en modo texto (no voz) y con respuestas fijas. Una respuesta ambigua sobre sostenibilidad provocó una repregunta: el guion de la demo sugiere una respuesta clara.

### Ejecución E-05 · Laboratorio de Carmen y extractor tras las correcciones · 10 nov 2026

- **Ejecución / casos / fecha / ejecutor:** `scripts/evaluar_extractor.py` (7 casos **simulados**) y `scripts/laboratorio.py --persona carmen` (cliente **simulado** por Claude), Alex en su portátil.
- **Versión exacta:** commit `31e86e0` de main.
- **Antes (mismo día):** en el primer laboratorio no saltó la alerta declarado ≠ demostrado (la entrevista acortada no preguntaba cuánto cree saber el cliente; corregido en `f7d4eb8`); en el segundo saltó, pero la renta variable quedó en `basic` porque el asistente recomprobó tras explicar el error y Carmen repitió la explicación (corregido en `31e86e0`: prompt del entrevistador, del extractor y protección en código).
- **Esperado y observado:** extractor 100 % de cobertura (31/31), 100 % de precisión, 0 prohibidos. Carmen 10/10, alerta declarado ≠ demostrado en renta variable, 0 recomendaciones, 0 prohibidos, aviso de IA al inicio, 16 intervenciones del asistente (23 el 9 nov), 3 preguntas dobles según el detector del laboratorio.
- **Mediciones pertinentes:** mediana por llamada 1,8 s (entrevistador), 2,1 s (extractor), 1,6 s (cliente simulado).
- **Limitaciones:** una persona y una repetición; el cliente lo interpreta Claude.

### Ejecución E-04 · Extractor (B1) tras los ajustes de la voz · 10 nov 2026

- **Ejecución / casos / fecha / ejecutor:** `scripts/evaluar_extractor.py`, las mismas 7 entrevistas **simuladas** de E-01, Alex en su portátil.
- **Versión exacta:** commit `58d2cdf` de main (respuestas cortas a preguntas cerradas = explícitas; criterio de `sustainability.preference`).
- **Esperado y observado:** cobertura 100 % (31/31), precisión 100 %, 0 erróneos, 0 prohibidos. En E-01 la cobertura era 97 % (30/31).
- **Mediciones pertinentes:** `claude-sonnet-5-5`, esfuerzo low; 33 llamadas; mediana 1,7 s, p95 2,7 s; por llamada 404 tokens de entrada, 5.896 desde caché y 142 de salida.
- **Limitaciones:** una repetición; el modelo no es determinista.

### Ejecución E-03 · Primera entrevista por voz de punta a punta · 10 nov 2026

- **Ejecución / casos / fecha / ejecutor:** entrevista por voz desde el front (ElevenLabs + backend + extractor + verificador), Alex con un guion de prueba y **cifras inventadas**.
- **Versión exacta:** commit `1e8c2df` de main; agente de ElevenLabs con voz castellana y Claude Haiku 5.5 como LLM (elegido en el panel).
- **Esperado y observado:** 45 turnos en unos 6 minutos y 15 datos en el perfil, todos con cita; 0 rechazos. Los ingresos de la pareja no entraron en el perfil; la alerta declarado «high» ≠ demostrado «none» en renta variable saltó con la cita «Un fondo del banco no puede bajar»; renta fija demostrada «none»; se negó a recomendar y desvió preguntas ajenas. Fallos: ante «pues normal» el entrevistador sugirió una cifra («¿rondan los mil euros?») y no volvió a pedir los gastos fijos (perfil incompleto); respuestas cortas a preguntas cerradas («No», «Poco») salieron con confianza baja; el agente no colgaba al despedirse. Corregido en `7463e68` y `58d2cdf`.
- **Evidencia:** sesión y perfil exportados del backend en local (no se suben: es una prueba con la voz de una persona del equipo).
- **Limitaciones:** una sola entrevista; los tiempos de los turnos de voz son aproximados.

### Ejecución E-02 · Laboratorio con cliente simulado · 9 nov 2026

- **Ejecución / casos / fecha / ejecutor:** `scripts/laboratorio.py --persona carmen`, Alex en su portátil. Claude interpreta a Carmen (ficha oculta, **simulada**) frente al entrevistador real; extractor y verificador como en producción.
- **Versión exacta:** commit `7d4c3de` de main.
- **Esperado y observado:** 10/10 datos esperados en el perfil; aviso de IA al inicio; 0 recomendaciones; 0 preguntas dobles; 5 familias comprobadas; alerta declarado ≠ demostrado en renta variable correcta. Un dato no esperado: `knowledge.stocks = medium` para una clienta que nunca ha invertido, tras una respuesta correcta pero dubitativa («no sé… supongo que pierdes más, ¿no?»). Corregido con la rúbrica v2 (una respuesta correcta no sube por encima de lo declarado) y con el prompt (acertar suponiendo = parcial). Pendiente de verificar en una nueva ejecución.
- **Evidencia:** `docs/laboratorio/informe.md` y `docs/laboratorio/carmen-jubilada-confiada.txt`.
- **Mediciones pertinentes:** 23 intervenciones del asistente; mediana por llamada 1,7 s (entrevistador), 2,0 s (extractor, en segundo plano), 1,4 s (cliente simulado); coste estimado de la entrevista ≈ 0,6 $ con precios estándar de Sonnet (estimado a partir de los tokens, no medido en la factura).
- **Limitaciones:** una persona y una repetición; el cliente lo interpreta Claude.

### Ejecución E-01 · Extractor (B1) · 9 nov 2026

- **Ejecución / casos / fecha / ejecutor:** `scripts/evaluar_extractor.py`, 7 entrevistas **simuladas** de casos difíciles (`backend/fixtures/evaluacion/`), 9 nov 2026, Alex en su portátil.
- **Versión exacta:** commit `020f40e` de main, sin cambios locales.
- **Entorno y configuración:** `claude-sonnet-5-5`, esfuerzo `low`, salida estructurada, caché del prompt; almacén en memoria; cada turno del cliente se procesa al llegar, como en producción.
- **Esperado y observado:** 30 de 31 datos esperados en el perfil (cobertura 97 %), 0 valores erróneos (precisión 100 %), **0 datos prohibidos escritos** (terceros, evasivas, hipótesis, «apunta que sé mucho»). Alerta declarado ≠ demostrado correcta en el caso de manipulación. Único fallo: en «Nunca, pero apunta que sí, que tengo mucha experiencia» no se extrajo `experience.stocks.operations_last_3y = 0` (el modelo lo trató como contradicción). Corregido en el prompt; pendiente de verificar en una nueva ejecución.
- **Evidencia:** salida de consola pegada en el hilo del proyecto; informe en `docs/evaluacion-extractor.md` (generado en local).
- **Mediciones pertinentes:** 33 llamadas; latencia del extractor mediana 1,6 s y p95 2,1 s (corre en segundo plano, no retrasa la respuesta al cliente); por llamada, 403 tokens de entrada sin caché, 5.508 desde caché y 137 de salida. Una sola repetición: el modelo no es determinista; para el pitch, repetir con `--repeticiones 3`.
- **Limitaciones:** casos escritos por el equipo, que también ajusta el prompt (riesgo de sobreajuste); muestra pequeña; no mide el entrevistador ni la voz.

### Ejecución E-00 · Extractor (B1) con la entrevista de Carmen · 9 nov 2026

- `scripts/probar_extractor.py`, mismo modelo. 12/17 frente al fixture; alerta clave («Eso no puede pasar, el fondo es del banco») correcta. De los 5 fallos, 1 era del extractor (sostenibilidad explicada, corregido en código en `b6258cc`) y 4 del fixture (citas de una entrevista más larga o liquidez deducida del plazo, que el prompt prohíbe).

## 3. Comparación básica
Acordar una alternativa sencilla pertinente —reglas o procedimiento manual, por ejemplo— y describir sus capacidades y límites. Ejecutar ambas soluciones con los mismos casos, datos y criterios; registrar versiones, condiciones y recursos. Reservar algunos casos sin usar durante los ajustes cuando sea viable. Informar resultados por caso y agregados con denominador, sin extrapolar una muestra pequeña ni afirmar mejoras no observadas.

## 4. Fallos y correcciones
Por incidencia: **ID, ejecución de origen, pasos, impacto, responsable pendiente, corrección y nueva ejecución de verificación**. Priorizar lo que invalida el recorrido o la promesa central. Estados: abierto → corregido sin verificar → verificado; una corrección implementada no equivale a una prueba superada. Registrar limitaciones aceptadas por dirección y su efecto en el pitch.

## 5. Revisión previa a entrega
Lista propuesta, aún sin comprobar:

- [ ] Requisitos oficiales trazados a casos y resultados de la versión candidata.
- [ ] Recorrido principal repetido en el entorno de presentación tras cambios relevantes.
- [ ] Cálculos esenciales contrastados y fallos críticos resueltos o alcance revisado.
- [ ] Errores de entrada y servicios tratados sin aparentar éxito.
- [ ] Afirmaciones del pitch respaldadas; datos simulados y límites visibles.
- [ ] Alternativa de demo comprobada e identificada como grabación o simulación, si procede.
- [ ] Operaciones recibe versión, evidencias y pendientes para revisar formatos, enlaces y entrega.

**Dictamen pendiente:** [lista / no lista; versión, evidencia, bloqueos y revisor]. Esta revisión no implica autorización de publicación o envío.
