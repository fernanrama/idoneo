# Producto, ingeniería y repositorio

Preparación · 8 de noviembre de 2026 · Responsable: Producto

## Estado y uso
**Preparado:** procedimiento de MVP, integración y recuperación. Dirección confirma el repositorio privado [hack-finance-uc3m-2026](https://github.com/fernanrama/hack-finance-uc3m-2026), creado con autorización de Fernán. **Confirmado por Fernán:** entorno cloud `hack-finance-uc3m-2026` publicado, GitHub conectado con acceso al repositorio y chats 03 y 06 reanudados y completados sin error. Este checkout cloud tiene Git y parte de `de9728d`; no acredita el estado Git del espacio local original. Se verifican los 16 documentos del ZIP y se prepara su incorporación mediante commit/PR. **Pendiente:** integración en principal, prueba desde móvil, enunciado, rúbrica, competencias, accesos de ejecución de la futura app, stack y despliegue. No hay aplicación. Esta puesta a punto es documental. Ajustar los hitos al tiempo restante cuando llegue el reto.

## MVP y arquitectura
Completar con estrategia una ficha: usuario → problema → entrada disponible → acción principal → resultado verificable → criterio de rúbrica → aceptación → exclusiones. Elegir un recorrido completo antes de añadir funciones. Operaciones lo convierte en tareas con propietario y dependencias; evaluación define casos de referencia y tutoría valida significado financiero, fórmulas y supuestos.

Elegir arquitectura según restricciones, habilidades reales y dependencia más incierta. Registrar componentes, flujo de datos, persistencia necesaria, servicios externos y alternativa ante fallo. Separar cálculos deterministas de generación del modelo; conservar procedencia y supuestos cuando sean necesarios para explicar resultados. Justificar decisiones y elevar cambios comunes a dirección.

Antes de repartir código, acordar por interfaz: productor/consumidor, entrada/salida de ejemplo, tipos, unidades, moneda, fechas, campos opcionales, errores, tiempos de espera y responsable. Asignar rutas concretas con un escritor; cambios de contrato requieren coordinación previa. Datos simulados y sustitutos temporales deben estar identificados, con condición y responsable de reemplazo.

## Conectar el repositorio del equipo
Verificar y registrar, sin mostrar secretos:
1. Ubicación canónica y si existe Git en esta carpeta o en una carpeta superior; identidad del remoto y acceso autorizado del equipo.
2. Rama principal real, rama actual, versión de partida, cambios locales, archivos sin seguimiento y trabajo pendiente del equipo. Preservarlos; no reiniciar ni sobrescribir para facilitar la conexión.
3. Instrucciones del repositorio, estructura, licencias, restricciones del reto sobre código previo, dependencias y comandos de instalación, ejecución, pruebas y compilación.
4. Reglas de revisión, integración y automatización; responsables y permisos de publicación. Comprobar si documentación o datos privados quedarían incluidos al conectar esta carpeta.
5. Configuración ignorada, archivos ya rastreados e historial antes del primer envío: ignorar un secreto no lo elimina del historial. Si aparece uno, detener su difusión y coordinar su revocación.

El repositorio identificado ya está conectado y disponible en este checkout cloud; la incorporación documental se entrega para revisión mediante commit/PR. Acordar ubicación del código y documentación antes de mover archivos.

## Código, revisión e integración
Seguir [CLOUD_Y_LOCAL.md](../coordinacion/CLOUD_Y_LOCAL.md): priorizar cloud para implementación acotada, revisión y pruebas reproducibles, una vez verificado el entorno. Cada tarea parte de una versión integrada, lee contexto y trabaja en un espacio aislado con rutas y aceptación asignadas; entrega commits/PR, pruebas, limitaciones y siguiente paso. Un responsable revisa e integra antes de lanzar trabajo dependiente. No cambiar ramas concurrentemente en un checkout compartido; serializar o acordar checkouts/worktrees separados.

Local queda para pruebas interactivas/visuales, navegación autenticada, integración y demo cuando aporte valor. Confirmar la versión antes de probar y registrar evidencia vinculada a ella. Los cambios locales y mensajes de chat no se sincronizan automáticamente con cloud; la fuente de verdad será la versión integrada del repo. No presumir herramientas locales disponibles en cloud ni acceso móvil ya probado.

Antes de integrar: revisar diferencias, verificar contratos y ejecutar las comprobaciones pertinentes. Registrar versión, pruebas y limitaciones en evaluación. Resolver conflictos con sus propietarios y comprobar el recorrido completo tras integrar. Mantener una versión estable identificable; una tarea no está terminada solo porque su componente funciona aisladamente.

## Configuración privada, despliegue y recuperación
Documentar únicamente nombres de variables, propósito y estado de acceso. Guardar valores en configuración local excluida o en el almacén privado del proveedor; nunca en código, Markdown, registros, mensajes ni artefactos de demo. No exponer credenciales en el cliente.

Elegir destino y costes cuando se conozcan recursos. Preparar instrucciones reproducibles, configuración por entorno y comprobación de arranque. Antes de publicar, verificar autorización aplicable, versión, acceso del jurado, recorrido principal y ausencia de datos privados.

Hitos: **aceptación acordada → recorrido completo → diferencial probado → estabilización → entrega**. Para la demo, conservar versión estable y pasos de restauración; ensayar recuperación ante fallo de red/API. Preparar ejecución local si es viable y grabación o datos de respaldo claramente etiquetados con comunicación. Probar recuperación y registrar limitaciones, sin prometer funcionamiento sin conexión no comprobado.
