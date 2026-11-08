# Trabajo híbrido: móvil, cloud y local

## Objetivo y estado
Trabajar sin depender del PC encendido. Repositorio privado: https://github.com/fernanrama/hack-finance-uc3m-2026 . Los seis chats iniciales son locales; son roles reutilizables, no una infraestructura cloud ya activada. Fernán confirma el entorno cloud `hack-finance-uc3m-2026` publicado y GitHub conectado con acceso al repositorio. Esta sesión accede al checkout Git cloud; la integración de esta documentación se realizará por commit/PR. Prueba desde móvil pendiente.

Antecedente: se observó un aviso de cuota agotada al intentar crear el entorno; ya no describe el estado actual confirmado. No consta reinicio de cuota ni cambio de plan. Los chats 03 y 06 se reanudaron y completaron sin error, según Fernán. En esta puesta a punto se verificaron las 16 entradas del ZIP frente a las seis carpetas del checkout y se retiró el paquete; el commit/PR documenta la entrega para revisión. No hay aplicación ni stack elegido; el enunciado sigue pendiente.

Fuente oficial consultada mediante navegador integrado el 8 de noviembre de 2026: https://learn.chatgpt.com/docs/cloud . Describe entornos cloud publicados con repositorios, tareas en espacios aislados, continuidad con el ordenador dormido y acceso web/móvil/escritorio. Esto describe la capacidad del producto, no confirma el estado de esta cuenta.

## Dónde hacer cada trabajo
| Trabajo | Opción preferida | Resultado persistente |
| --- | --- | --- |
| Conversación, decisiones, tutoría y pitch | Chat disponible en el dispositivo del usuario | Síntesis en documentos del repo |
| Implementación acotada, revisión, pruebas reproducibles | Codex Cloud con entorno del repo | Commit/PR, pruebas y limitaciones |
| Navegación autenticada, pruebas visuales locales, grabación | Local cuando requiera esas herramientas | Evidencia y material final subidos al destino acordado |
| Validación de app desplegada | Entorno con navegador disponible | Resultado vinculado a versión/URL |

La disponibilidad del navegador y herramientas locales no se presume en cloud. Respetar siempre la preferencia de navegador integrado para investigación web; si el entorno no lo tiene, devolver esa parte al entorno que sí lo tenga.

## Puesta en marcha

Estado actual: publicación y conexión a GitHub confirmadas por Fernán; checkout accesible en esta sesión. Los pasos siguientes conservan el procedimiento de referencia, no son tareas todas pendientes. Falta la comprobación móvil del paso 6; no se ha realizado en esta sesión.
1. Subir documentación revisada al repositorio privado y verificar archivos y versión.
2. En web/escritorio, seleccionar trabajo en Cloud y crear/seleccionar entorno con este repositorio. Revisar acceso de GitHub antes de conceder permisos nuevos; limitar al repositorio necesario.
3. Configurar herramientas y comprobaciones mínimas; ahora solo documentación, después instalación/build/tests del stack elegido. Configurar credenciales en el almacén del entorno, nunca en Markdown.
4. Revisar la preparación y publicar el entorno. Verificar la confirmación de publicación.
5. Ejecutar una tarea pequeña de lectura del repo: identificar estado y siguiente paso, sin elegir producto ni implementar. Comprobar resultado en cloud.
6. El usuario abre Codex en móvil con la misma cuenta, selecciona el entorno y comprueba que ve/continúa la tarea. No afirmar esta prueba hasta que ocurra.

## Contexto entre dispositivos
Fuente de verdad: versión integrada del repositorio. Al comenzar: leer AGENTS.md, CONTEXTO.md y el documento del área. Al terminar: registrar resultado, evidencia, pendientes y siguiente paso en su archivo; entregar cambios mediante commit/PR. Una modificación local o una respuesta de chat no actualiza otra tarea cloud automáticamente.

Dirección reparte solo trabajo independiente con límites claros. Una tarea cloud por resultado concreto; no seis agentes activos por defecto. Integrar cambios de contexto antes de lanzar tareas dependientes. Evitar mover ramas en un checkout compartido. Mantener disponibles las instrucciones de reproducción y una versión estable para demo.

## Prompt de entrada reutilizable
Lee AGENTS.md, CONTEXTO.md y coordinacion/FLUJO.md en la versión actual del repositorio. Asume el rol indicado y consulta su documento en README.md. Objetivo: [resultado concreto]. Puedes modificar: [rutas]. Criterio de aceptación: [evidencia]. No dupliques trabajo asignado ni supongas historial de otros chats. Entrega cambios, comprobaciones y siguiente paso; registra cualquier limitación real del entorno.
