# 04 · Evaluación y fiabilidad

Nota de arranque · 8 de noviembre de 2026

## Base operativa preparada
[Plan y evidencias](../../evaluacion/PLAN_Y_EVIDENCIAS.md): plantilla de criterios, casos, ejecuciones ligadas a versión, comparación básica, incidencias y revisión previa a entrega. Comprobada la estructura documental y el enlace; no se han ejecutado pruebas del producto ni obtenido métricas. Dirección revisará esta propuesta. El enunciado llegará en la siguiente sesión; los hitos se cuentan desde su recepción, sin presuponer que ya está disponible.

## Misión y hechos
Convertir las promesas del MVP en evidencia reproducible y comprensible para el equipo y el jurado. Fernán está inscrito; el evento transcurre del 8 al 12 de noviembre. Faltan enunciado, rúbrica, datos, APIs y reglas de IA. No hay producto elegido ni pruebas ejecutadas. Todo lo siguiente es provisional, pendiente de acuerdo con dirección.

## Entregables propuestos
- Matriz breve: criterio de la rúbrica → comportamiento esperado → caso de prueba → evidencia → estado y limitación.
- Conjunto pequeño de ejemplos: recorrido principal, datos incompletos, entrada inválida y fallo de una dependencia. Etiquetar los datos simulados y registrar la procedencia de los reales.
- Comparación con una solución básica pertinente al reto, por ejemplo reglas simples o un procedimiento manual, usando las mismas entradas y criterios.
- Registro de ejecución: versión, configuración, entrada, resultado esperado y observado, fecha, aprobado/fallido y evidencia. Para respuestas variables, conservar varias ejecuciones sin seleccionar solo las favorables.
- Resumen para el pitch: qué funciona, bajo qué condiciones, qué falla y qué no se ha comprobado.

## Esquema de evidencia
Separar cálculos deterministas y respuestas del modelo. Los primeros se contrastarán con resultados calculados de forma independiente, incluyendo unidades y redondeos acordados. Las segundas se evaluarán con criterios observables definidos antes de probar: cumplimiento de la tarea, respaldo de afirmaciones y reconocimiento de información insuficiente, según corresponda.

Si el reto lo justifica, medir éxito por caso, errores, latencia y coste por recorrido. Informar tamaño de muestra, condiciones y repeticiones; una muestra pequeña solo describe esos casos. No fijar umbrales ni afirmar mejoras sin resultados. Reservar algunos casos para comprobar cambios sin ajustar continuamente a todos los ejemplos.

## Criterios provisionales de listo para demo
- El recorrido principal se completa en el entorno de presentación y se repite tras el último cambio relevante.
- Los resultados esenciales coinciden con lo esperado; no quedan fallos conocidos que invaliden la promesa central.
- Entradas incompletas y fallos de servicios producen una salida comprensible, sin inventar resultados ni presentar un intento fallido como éxito.
- Datos simulados, límites y funcionalidades realmente disponibles están identificados.
- Las afirmaciones del pitch tienen evidencia accesible; existe una alternativa de demostración identificada como grabación o simulación si se necesita.

## Dependencias y decisiones pendientes
Estrategia: rúbrica y promesa prioritaria. Tutoría: significado financiero y validación de ejemplos. Producto: contratos de entrada/salida, versión y manejo de errores. Comunicación: guion y afirmaciones demostrables. Operaciones: entorno, responsables y tiempo de verificación. Dirección debe acordar alcance, comparación básica, umbrales y responsables; no se asignan personas aquí.

## Siguiente paso
Al recibir el enunciado, convertir sus criterios en una primera matriz, acordar el recorrido principal y seleccionar ejemplos con resultados esperados antes de implementar. Proponer después a dirección el mínimo de evidencia necesario para la primera demo completa.
