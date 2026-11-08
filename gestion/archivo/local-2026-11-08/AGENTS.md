# Hack Finance UC3M — reglas compartidas

## Propósito
Ayudar al equipo a maximizar sus posibilidades de ganar Hack Finance UC3M, construyendo una solución útil, demostrable y ajustada al enunciado y a la rúbrica. No garantizar premios ni inventar resultados.

## Contexto confirmado por Fernán (8 noviembre 2026)
- Fernán está inscrito. El evento empieza el domingo 8 por la mañana, cuando entregan el enunciado, y termina el jueves 12.
- Equipo, segmentación provisional de los nombres recibidos: Juan Fernández; Hammad Bellachhab; Fernán Rama Hombreiro; Rodrigo Manchado Cano; Pablo Cobo; Alejandro Serrano. No inferir identidades de LinkedIn ni competencias a partir de nombres.
- Fernán prevé centrarse en desarrollo de aplicación y necesita apoyo en finanzas. No hay reparto definitivo de tareas.
- Recibido el PDF local `Completo hack finance.pdf`: rúbrica y entregables en dos páginas. Consultar CONTEXTO.md y estrategia/ANALISIS_INICIAL.md. No inferir que contiene todas las bases ni inventar requisitos.
- Contexto público consultado: agente financiero; BEST UC3M; colaboradores Anthropic/Claude, MyInvestor, ElevenLabs y GPTAdvisor. Fuentes: https://mew.bestuc3m.es/hackathon-2026/ y https://eventos.uc3m.es/agenda/show_event/159783/hack-finance.html . La cabecera de la segunda discrepa en el mes; el usuario confirma noviembre.

## Coordinación
- El chat original es dirección general e integración de decisiones. Los seis chats especializados son espacios de trabajo del usuario, no seis miembros humanos del equipo.
- No asumir que los chats comparten historial. Leer este archivo y CONTEXTO.md al empezar; consultar las notas de las otras áreas cuando sean relevantes.
- Cada área mantiene su nota en coordinacion/areas/ y los documentos asignados en coordinacion/FLUJO.md. No modificar archivos de otra área sin traspaso explícito. Proponer cambios comunes a dirección.
- Solo dirección mantiene CONTEXTO.md y coordinacion/CHATS.md. Las instrucciones explícitas del usuario prevalecen.
- Anotar hechos, propuestas, decisiones pendientes, dependencias y siguiente paso. Una propuesta no es una decisión del equipo.
- Antes de editar código compartido, acordar propiedad de archivos y contratos. No crear stacks, apps ni instalaciones paralelas por iniciativa de cada área.
- Fernán autoriza la delegación entre estos chats y el uso de subagentes para gestionar todo el hackathon. No crear más chats permanentes sin necesidad acordada. Cada delegación tendrá objetivo, archivos asignados, criterio de terminado y destinatario de revisión; evitar delegación recursiva y tareas duplicadas.
- Toda investigación web debe hacerse con el navegador integrado, por preferencia explícita del usuario. No usar búsquedas web por API, HTTP o conectores como sustituto.
- No contactar a terceros, enviar mensajes, publicar o contratar servicios sin autorización aplicable. No investigar perfiles homónimos sin identidad suficiente.

## Método
- Elegir alcance según rúbrica, necesidad y tiempo. Una demostración completa temprana antes de ampliar funciones.
- Distinguir cálculos deterministas de resultados del modelo. Medir precisión, coste, latencia y fallos cuando el reto lo requiera; no inventar métricas.
- Enseñar a Fernán lo necesario para comprender y defender decisiones. Explicaciones cortas, ejemplos y comprobaciones de comprensión; no confundir exposición con dominio.
- Preparar pitch y pruebas desde el principio. Identificar datos simulados y límites reales del MVP.
- El enunciado ya se recibió. Analizar y comparar alternativas; la recomendación inicial es provisional y no sustituye la decisión del equipo. No fabricar requisitos ni elegir stack prematuramente.
- Leer coordinacion/FLUJO.md y README.md para el mapa de documentos y protocolo de trabajo. Actualizar evidencia y siguiente acción al cerrar cada sesión significativa.
- Nunca guardar claves API, tokens, contraseñas o datos personales financieros en Markdown, código, commits o mensajes de coordinación. Registrar solo nombres de variables y estado de acceso.
- Priorizar Codex Cloud para tareas de repositorio acotadas que puedan ejecutarse sin el PC encendido. Usar local para verificación interactiva o herramientas locales cuando convenga. Consultar coordinacion/CLOUD_Y_LOCAL.md; los seis roles pueden ejecutarse en cualquiera de los entornos con contexto actualizado.
- En cloud los espacios de trabajo están aislados: archivos locales sin commit/push no se sincronizan automáticamente. Compartir decisiones mediante commits/PR y releer la versión integrada antes de comenzar trabajo dependiente. No afirmar que esta conversación local sigue ejecutándose al apagar el PC.

## Áreas y propiedad inicial
1. Estrategia y reto: coordinacion/areas/01-estrategia.md
2. Tutoría y finanzas: coordinacion/areas/02-tutoria.md
3. Producto y desarrollo: coordinacion/areas/03-producto.md
4. Evaluación y fiabilidad: coordinacion/areas/04-evaluacion.md
5. Pitch y demo: coordinacion/areas/05-comunicacion.md
6. Operaciones del equipo: coordinacion/areas/06-operaciones.md
