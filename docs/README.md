# Documentación de Idóneo

Orden de lectura recomendado: primero la arquitectura, después el diseño y, al final, los detalles de implementación.

## Producto y arquitectura

| Documento | Contenido |
|---|---|
| [arquitectura.md](arquitectura.md) | Flujo del producto y arquitectura de agentes: entrevista, extractor, verificador, perfil versionado, validación humana y MCP |
| [configuracion.md](configuracion.md) | Variables de entorno del backend y del frontend, y persistencia del perfil (memoria, SQLite o Postgres) |
| [contratos.md](contratos.md) | Cómo implementa el código el contrato del perfil: API REST, persistencia, versionado y desviaciones conscientes |
| [pruebas-de-audio.md](pruebas-de-audio.md) | Pruebas de audio: cómo cada dato suena con el fragmento de la llamada que lo justifica |
| [modo-asesor-demo.md](modo-asesor-demo.md) | Modo asesor de demostración (validar en local con clientes ficticios), entrevista corta del pitch y MCP de demo |
| [memoria-personal-seguridad.md](memoria-personal-seguridad.md) | Memoria personal por usuario: contrato, garantías de seguridad y límites |
| [marca/README.md](marca/README.md) | Identidad de marca: logo, sello «Powered by idóneo», colores y tipografía |
| [pitch.md](pitch.md) | Pitch: de dónde sale cada cifra nueva de la presentación, respuestas a las preguntas del jurado, lista del día de la demo y prueba con cinco personas |

## Diseño (8–9 nov 2026)

| Documento | Contenido |
|---|---|
| [diseno/01-diseno.md](diseno/01-diseno.md) | Diseño original del producto: marco MiFID, onboarding, perfil, salidas, integración y demo |
| [diseno/02-auditoria-y-decisiones.md](diseno/02-auditoria-y-decisiones.md) | Auditoría del diseño y decisiones del equipo. Si contradicen el diseño, mandan las decisiones |
| [diseno/03-contrato-perfil.md](diseno/03-contrato-perfil.md) | Especificación del perfil: modelo de un dato, esquema, estados, restricciones y herramientas MCP |
| [diseno/04-mcp-myinvestor.md](diseno/04-mcp-myinvestor.md) | Uso del MCP público de MyInvestor y sus límites |
| [diseno/05-perfil-continuo.md](diseno/05-perfil-continuo.md) | Visión: del perfil inicial a un perfil continuo con microentrevistas |

## Evaluación

| Documento | Contenido |
|---|---|
| [evaluacion/extractor.md](evaluacion/extractor.md) | Evaluación del extractor con la API real (generada por `backend/scripts/evaluar_extractor.py`) |
| [evaluacion/verificador.md](evaluacion/verificador.md) | Evaluación del verificador (generada por `backend/scripts/evaluar_verificador.py`) |
| [evaluacion/laboratorio/](evaluacion/laboratorio/) | Entrevistas con clientes simulados y sus informes (generadas por `backend/scripts/laboratorio.py`) |

El resumen de resultados, método y límites está en [evaluacion/README.md](evaluacion/README.md). El marco legal, contrastado con el texto oficial, en [normativa.md](normativa.md).

## Investigación

| Documento | Contenido |
|---|---|
| [investigacion/memoria-agente-elevenlabs.md](investigacion/memoria-agente-elevenlabs.md) | Memoria por usuario con ElevenLabs: decisión de arquitectura |
| [investigacion/claude-extractor.md](investigacion/claude-extractor.md) | Papel de Claude y del extractor en cada turno de la entrevista |

Las imágenes y los diagramas están en [img/](img/).
