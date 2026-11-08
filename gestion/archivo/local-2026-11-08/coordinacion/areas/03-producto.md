# 03 · Producto y desarrollo

Nota de arranque · 8 de noviembre de 2026 · Provisional

## Misión y hechos
Convertir el reto en una experiencia útil y demostrable, con una primera versión completa temprana y una integración sostenible hasta la entrega del 12 de noviembre. Fernán prevé centrarse en desarrollo; el reparto no está decidido. Faltan enunciado, rúbrica, recursos y competencias confirmadas. No hay producto ni stack elegidos.

## Entregables del área
- Ficha de MVP: usuario, problema, resultado útil, criterio de éxito y exclusiones explícitas, vinculados a la rúbrica.
- Recorrido de demo y criterios de aceptación observables.
- Propuesta de arquitectura mínima, una vez conocidos recursos y restricciones; separar cálculos deterministas de generación del modelo.
- Contratos de entrada/salida, errores y propiedad de archivos acordados antes de implementar.
- Primera versión integrada, instrucciones para reproducirla y registro de limitaciones y dependencias.

## Plantilla de recorrido de demo
1. **Situación:** [usuario] necesita [resultado] y hoy encuentra [problema].
2. **Entrada:** aporta [datos mínimos]; indicar procedencia y si son simulados.
3. **Acción:** realiza [una acción principal] con un estado de progreso comprensible.
4. **Resultado:** recibe [salida útil], con cálculos, fuentes y aportación del modelo distinguibles cuando corresponda.
5. **Comprobación:** contrastar [resultado esperado] con [evidencia verificable].
6. **Fallo controlado:** mostrar qué ocurre ante [dato inválido, insuficiente o servicio no disponible], sin presentar una simulación como ejecución real.
7. **Cierre:** explicar [valor obtenido] y [límite actual].

## Propuesta para entregar pronto
- **Al recibir el reto:** elegir con dirección un único recorrido prioritario; acordar aceptación, contratos y responsables. Probar primero la dependencia técnica más incierta y recalcular tiempos según el plazo oficial.
- **Primera integración:** recorrido completo ejecutable, desde entrada hasta resultado, y desplegado si las reglas y recursos lo permiten. Identificar sustitutos temporales y responsables de reemplazo.
- **Tras validar el recorrido:** ampliar solo con un diferencial respaldado por la rúbrica y pruebas; resolver antes sus fallos.
- **Estabilización:** cerrar alcance y ensayar la demo con comunicación; probar recuperación y respaldo claramente etiquetado.
- **Entrega:** verificar desde un entorno limpio y cumplir el horario oficial, todavía pendiente.

## Base operativa preparada
[Plan de producto y repositorio](../../producto/PLAN_Y_REPOSITORIO.md): MVP, contratos, revisión, configuración privada, despliegue y recuperación. La documentación está integrada en el [repositorio privado](https://github.com/fernanrama/hack-finance-uc3m-2026) mediante PR #1 y el entorno cloud está publicado y ha ejecutado una tarea. Acceso móvil y reconciliación de la carpeta local con main pendientes. Cloud para tareas aisladas; local para pruebas y demo. Stack pendiente.

## Dependencias y decisiones pendientes
- **Estrategia:** prioridad del problema, rúbrica y alcance aceptado.
- **Tutoría:** significado financiero de entradas, fórmulas, supuestos y salidas.
- **Evaluación:** casos de referencia, fallos esperados y evidencia de aceptación.
- **Comunicación:** duración, relato y secuencia de demostración.
- **Operaciones:** habilidades, disponibilidad, accesos y responsable de integración.

La elección de stack, alojamiento, servicios y reparto queda pendiente de esas entradas; esta nota no constituye una decisión del equipo.

## Siguiente paso
Cuando llegue el enunciado, extraer restricciones y criterios de éxito; proponer a dirección un MVP con exclusiones, recorrido y riesgos. Tras acordar alcance y propiedad, decidir arquitectura y comenzar la primera integración.
