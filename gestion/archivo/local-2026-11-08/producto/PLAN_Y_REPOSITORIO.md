# Producto, ingeniería y repositorio

Preparación · 8 de noviembre de 2026 · Responsable: Producto

## Estado y uso
**Preparado:** procedimiento de MVP, integración y recuperación; [repositorio privado](https://github.com/fernanrama/hack-finance-uc3m-2026) con documentación integrada en main y entorno cloud publicado con una tarea ejecutada. **Pendiente:** prueba móvil con el PC apagado, reconciliar la carpeta local con main y conocer reto, competencias, accesos de ejecución, stack y despliegue. Esta carpeta local no es un checkout Git. Ajustar hitos cuando llegue el reto.

## MVP y arquitectura
Completar con estrategia una ficha: usuario → problema → entrada disponible → acción principal → resultado verificable → criterio de rúbrica → aceptación → exclusiones. Elegir un recorrido completo antes de añadir funciones. Operaciones lo convierte en tareas con propietario y dependencias; evaluación define casos de referencia y tutoría valida significado financiero, fórmulas y supuestos.

Elegir arquitectura según restricciones y habilidades. Registrar componentes, datos, persistencia, servicios y alternativa ante fallo. Separar cálculos deterministas de generación del modelo; conservar procedencia y supuestos. Justificar decisiones y elevar cambios comunes a dirección.

Antes de repartir código, acordar por interfaz: productor/consumidor, entrada/salida de ejemplo, tipos, unidades, moneda, fechas, campos opcionales, errores, tiempos de espera y responsable. Asignar rutas concretas con un escritor; cambios de contrato requieren coordinación previa. Datos simulados y sustitutos temporales deben estar identificados, con condición y responsable de reemplazo.

## Conectar el repositorio del equipo
Verificar y registrar, sin mostrar secretos:
1. Ubicación canónica y si existe Git en esta carpeta o en una carpeta superior; identidad del remoto y acceso autorizado del equipo.
2. Rama principal real, rama actual, versión de partida, cambios locales, archivos sin seguimiento y trabajo pendiente del equipo. Preservarlos; no reiniciar ni sobrescribir para facilitar la conexión.
3. Instrucciones del repositorio, estructura, licencias, restricciones del reto sobre código previo, dependencias y comandos de instalación, ejecución, pruebas y compilación.
4. Reglas de revisión, integración y automatización; responsables y permisos de publicación. Comprobar si documentación o datos privados quedarían incluidos al conectar esta carpeta.
5. Configuración ignorada, archivos ya rastreados e historial antes del primer envío: ignorar un secreto no lo elimina del historial. Si aparece uno, detener su difusión y coordinar su revocación.

El ZIP se extrajo, contrastó y retiró del repositorio mediante la PR #1 integrada. La carpeta local no se sincroniza automáticamente: comparar y reconciliar diferencias con main antes de editar en paralelo; preservar las modificaciones locales.

## Código, revisión e integración
Seguir [CLOUD_Y_LOCAL.md](../coordinacion/CLOUD_Y_LOCAL.md): priorizar cloud para implementación acotada, revisión y pruebas reproducibles, una vez verificado el entorno. Cada tarea parte de una versión integrada, lee contexto y trabaja en un espacio aislado con rutas y aceptación asignadas; entrega commits/PR, pruebas, limitaciones y siguiente paso. Un responsable revisa e integra antes de lanzar trabajo dependiente. No cambiar ramas concurrentemente en un checkout compartido; serializar o acordar checkouts/worktrees separados.

Local queda para pruebas interactivas/visuales, navegación autenticada, integración y demo cuando aporte valor. Confirmar la versión antes de probar y registrar evidencia vinculada a ella. Los cambios locales y mensajes de chat no se sincronizan automáticamente con cloud; la fuente de verdad será la versión integrada del repo. No presumir herramientas locales disponibles en cloud ni acceso móvil ya probado.

Antes de integrar: revisar diferencias, contratos y pruebas. Registrar versión, evidencia y limitaciones en evaluación. Resolver conflictos con sus propietarios, comprobar el recorrido completo y mantener una versión estable identificable.

## Configuración privada, despliegue y recuperación
Documentar únicamente nombres de variables, propósito y estado de acceso. Guardar valores en configuración local excluida o en el almacén privado del proveedor; nunca en código, Markdown, registros, mensajes ni artefactos de demo. No exponer credenciales en el cliente.

Elegir destino y costes cuando se conozcan recursos. Preparar instrucciones reproducibles, configuración por entorno y comprobación de arranque. Antes de publicar, verificar autorización aplicable, versión, acceso del jurado, recorrido principal y ausencia de datos privados.

Hitos: **aceptación acordada → recorrido completo → diferencial probado → estabilización → entrega**. Para la demo, conservar versión estable y pasos de restauración; ensayar recuperación ante fallo de red/API. Preparar ejecución local si es viable y grabación o datos de respaldo claramente etiquetados con comunicación. Probar recuperación y registrar limitaciones, sin prometer funcionamiento sin conexión no comprobado.
