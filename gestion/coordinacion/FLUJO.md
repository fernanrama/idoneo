# Protocolo de trabajo

## Fuente de verdad y propietarios
AGENTS.md define reglas; CONTEXTO.md el estado vigente; DECISIONES.md conserva decisiones y revisiones; TABLERO.md refleja ejecución. Cada documento del mapa de README.md tiene un único escritor responsable. Los demás lo leen y envían propuestas. Una orden directa de Fernán prevalece y debe reflejarse en el estado antes de trabajo dependiente.

## Delegar sin fricción
Dirección o un área puede asignar trabajo a los chats existentes del directorio. La autorización del usuario para delegar se dio en este chat original el 8 de noviembre de 2026. El mensaje debe incluir: objetivo; contexto y fuentes; resultado esperado; archivos que puede editar; límites; dependencias; criterio de aceptación; quién revisa. El destinatario revisa el tablero para evitar duplicidades. Los subagentes son temporales y entregan al área que los inició; no sustituyen los chats del usuario.

No iniciar varias tareas sobre un mismo archivo. Si hace falta cambiar de propietario, registrar el traspaso antes de editar. Para código, producto define las rutas y contratos concretos antes de delegar. No usar ramas simultáneas dentro de un mismo checkout compartido: coordinar escrituras o proponer aislamiento adecuado cuando exista repositorio.

## Ciclo de ejecución
1. Leer estado común y nota del área; comprobar si hay nueva instrucción.
2. Operaciones mantiene tareas con ID, propietario, estado, dependencia, criterio de aceptación y enlace a evidencia. Durante esta preparación, cada chat tiene una asignación exclusiva conocida.
3. Ejecutar dentro del alcance. Separar hechos, propuestas, supuestos y bloqueos.
4. Verificar el resultado. No marcar terminado un intento ni una prueba pendiente.
5. Actualizar documento y nota del área con cambios, comprobación y siguiente paso. Informar al coordinador mediante una respuesta o mensaje acotado, sin generar ciclos de mensajes.
6. Dirección integra decisiones comunes; operaciones actualiza tablero. Ante conflicto, detener solo la parte dependiente y continuar lo independiente.

## Decisiones y repositorio
Decisiones reversibles de implementación dentro de un alcance delegado no necesitan aprobación repetida. Cambios de producto, alcance o contratos se coordinan antes de afectar a otras áreas. Antes de gestionar Git, identificar ubicación, remoto, rama, cambios existentes y trabajo del equipo; preservar cambios ajenos. No inventar un remoto ni crear un repositorio competidor. Producto propone el flujo de commits, revisión, integración y despliegue.

## Cierre y entrega
Una entrega está lista cuando cumple requisitos oficiales aplicables, está probada en su versión identificada y tiene instrucciones, enlaces y limitaciones. Comunicación prepara materiales; evaluación comprueba afirmaciones; operaciones verifica formatos, plazos, accesibilidad de enlaces y comprobante. Preparar todo antes de cualquier publicación o envío que necesite autorización específica.

## Antes del enunciado
Completar únicamente bases y plantillas útiles. Ningún chat debe pedir ahora datos al usuario, iniciar un curso, elegir stack ni implementar una aplicación. Al terminar queda listo para la siguiente sesión; no hay monitorización ni actividad autónoma continua implícita.
