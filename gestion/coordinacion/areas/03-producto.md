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
[Plan de producto y repositorio](../../producto/PLAN_Y_REPOSITORIO.md): MVP, contratos, revisión, configuración privada, despliegue y recuperación. Actualizado con CONTEXTO.md y [CLOUD_Y_LOCAL.md](../CLOUD_Y_LOCAL.md): dirección confirma el [repositorio privado](https://github.com/fernanrama/hack-finance-uc3m-2026). Prioridad cloud mediante tareas aisladas y commits/PR; local para pruebas interactivas, integración y demo. Fernán confirma que el entorno `hack-finance-uc3m-2026` está publicado, GitHub conectado con acceso al repositorio y el chat 03 se reanudó y completó sin error. En esta sesión cloud se contrastan los 16 documentos del ZIP y se prepara su commit/PR; integración en principal y prueba móvil pendientes. No hay aplicación ni stack elegido.

## Dependencias y decisiones pendientes
- **Estrategia:** prioridad del problema, rúbrica y alcance aceptado.
- **Tutoría:** significado financiero de entradas, fórmulas, supuestos y salidas.
- **Evaluación:** casos de referencia, fallos esperados y evidencia de aceptación.
- **Comunicación:** duración, relato y secuencia de demostración.
- **Operaciones:** habilidades, disponibilidad, accesos y responsable de integración.

La elección de stack, alojamiento, servicios y reparto queda pendiente de esas entradas; esta nota no constituye una decisión del equipo.

## Siguiente paso
Cuando llegue el enunciado, extraer restricciones y criterios de éxito; proponer a dirección un MVP con exclusiones, recorrido y riesgos. Tras acordar alcance y propiedad, decidir arquitectura y comenzar la primera integración.

## Evidencia local · 10/11/2026 · propuesta de memoria sobre #21

Por autorización explícita del usuario, se preparó una solución de perfiles, autorización/API y
adaptación del frontend en el worktree `/private/tmp/idoneo-pr21-perfil-propuesta`, rama
`fix/perfil-memoria-atomicidad-propuesta`, basada en #21 `b1b182e`. No se publicó ni integró.
Contrato, archivos, alternativas y límites en [MEMORIA_PERSONAL_SEGURIDAD.md](../../../docs/MEMORIA_PERSONAL_SEGURIDAD.md).

Evidencia: 474 tests backend correctos, 28 omitidos y 1 deseleccionado para evitar invocar migraciones;
18 tests del cliente, lint y build correctos. Se comprobó también una copia de main `8b698b7`
(#22/#23) con adaptaciones mínimas explícitas, sin fusionar ramas ni cambiar su diseño.
No se verificó PostgreSQL real, navegador interactivo ni voz real. Solo datos ficticios y servicios
locales; no Supabase, APIs de pago ni cambios en los servidores de la demo.

Siguiente acción: revisión por Juan, Pablo y Alejandro del contrato de posesión, revisión/borrado,
transporte, recuperación y permisos de entidad. Hay conflictos previos de #21 con main; la prueba
por copia no los resuelve. Commit, push y PR siguen sin autorización; las alternativas documentadas
no constituyen decisiones del equipo.

Actualización local posterior, por autorización del usuario y de Pablo para preparar correcciones
sobre #21: se integró main 8b698b7 en la copia aislada y se resolvieron los conflictos, sin commit
ni publicación. Se retiró el puente de privilegios del proxy de validación: web 403 hasta acordar
permiso independiente de asesor. Suite backend 474 correctos, 18 de cliente, lint/build y prueba HTTP
Next/API correctos. #19 35 correctos/5 omitidos; #20 56 correctos. La demo conserva sus procesos.
Siguiente acción: revisar el resultado y aprobar el cierre del merge local/publicación a #21;
confirmar permisos de asesor, transporte/recuperación de credenciales y política de borrado.

Publicación autorizada tras revisión del usuario: integrar mediante push normal en la rama de #21,
sin merge a main. Commit de integración `1149da4`, árbol idéntico al probado. El usuario acepta
provisionalmente posesión para clientes ficticios, validación web bloqueada, recuperación/revocación
individual pendientes, ADMIN_TOKEN solo de servicio y borrado local con revisión técnica.
Estas condiciones no habilitan producción; faltan permisos reales de entidad, identidad/transporte,
recuperación/revocación individual y política de retención externa. La evidencia de publicación
se dejará en la conversación de la PR; no se contacta al equipo por otros canales.
