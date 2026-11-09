# Plan y evidencias de evaluación

Responsable documental: área 04 · Actualizado: 8 de noviembre de 2026.

## Estado y uso
**Preparado:** plantilla de criterios, ejecuciones, comparación y revisión final. **Pendiente:** enunciado, rúbrica, producto, datos, responsables humanos y umbrales. Primeras ejecuciones del extractor registradas abajo (E-00, E-01). Los criterios siguientes son propuestas; no constituyen requisitos oficiales ni financieros o regulatorios.

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
