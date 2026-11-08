# Reparto del trabajo y plan de 5 días

8 nov 2026. Propuesta para un equipo de 6. Los nombres están por asignar salvo donde el diseño ya lo indica. El centro de todo es el perfil versionado definido en [04_CONTRATO_PERFIL.md](04_CONTRATO_PERFIL.md): el primer día se cierra ese contrato (esquema JSON y eventos entre front y backend) para que cada pieza trabaje sin esperar a las demás.

> Nota: el repo tiene un `docs/REPARTO.md` anterior pensado para 4 personas. Este documento es la propuesta para 6; el equipo decide cuál vale.

## Las 6 piezas

| # | Pieza | Persona | Qué incluye |
| --- | --- | --- | --- |
| 1 | **Voz (ElevenLabs)** | por asignar | Configurar el agente y el guion de la entrevista. Probar el SDK en el móvil. Descargar audio y transcripción al acabar y recortar los clips de las pruebas. Defiende ante el jurado de ElevenLabs. |
| 2 | **Front móvil** | por asignar | Next.js como PWA: pantalla de la entrevista, subtítulos, panel donde se llena el perfil, accesibilidad y pantalla de validación del asesor. |
| 3 | **Agentes** | por asignar | Extractor en tiempo real y verificador en segundo plano, con prompts y pruebas. Funciones deterministas: pérdida asumible, brecha de jubilación, reglas de coherencia, rúbrica de confianza. |
| 4 | **Perfil y backend** | Pablo (según el diseño) | Modelo de datos, versiones, estados, API REST, almacenamiento del audio y expediente exportable en JSON y PDF. |
| 5 | **MCP e integración** | por asignar | Nuestro servidor MCP con las 4 herramientas y su URL pública. Conexión con el MCP de MyInvestor como conector en Claude. Resultados de idoneidad y conveniencia expresados en los parámetros de MyInvestor. |
| 6 | **Normativa, producto y pitch** | por asignar | La tabla MiFID convertida en controles del verificador, texto del aviso de IA y del RGPD. Entregables: PDF de una cara, PPT, README y diapositiva de valor. También tester con usuarios reales y métrica de impacto. |

Las piezas 2, 3 y 4 son las que más se pisan: que se junten el día 1 para cerrar el esquema.

## Calendario

| Día | Objetivo |
| --- | --- |
| 1 | Contrato del perfil cerrado, repositorio y despliegue con URL pública. Cada pieza con un "hola mundo" conectado. Prueba de riesgo del SDK de ElevenLabs en móvil. |
| 2 | Cadena completa funcionando, aunque sea fea: hablo en el móvil, se llena el perfil, lo valido y el MCP devuelve perfil y restricciones. |
| 3 | Calidad: el verificador detecta declarado frente a demostrado, salen los clips de audio, resultados de idoneidad y conveniencia, consumo desde Claude con el MCP de MyInvestor. |
| 4 | Onboarding ampliado, pulido de la experiencia y pruebas con personas reales para medir. |
| 5 | Congelar el código a mediodía, grabar el plan B, ensayar el pitch. ZIP y entrega. |

Una reunión de 10 minutos cada mañana.

## Lo que coge Alex (con Claude) primero

Lo que desbloquea al resto y no depende de nadie:

1. **Contrato del perfil** ([04_CONTRATO_PERFIL.md](04_CONTRATO_PERFIL.md)). Hecho en borrador; falta revisarlo con las piezas 2, 3 y 4.
2. **La normativa convertida en controles:** cada requisito MiFID pasa a ser una regla concreta del verificador y un campo obligatorio.
3. **Especificación de las 4 herramientas MCP:** entradas, salidas y traducción de restricciones a parámetros de MyInvestor. Base ya escrita en el contrato y en [05_MCP_MYINVESTOR.md](05_MCP_MYINVESTOR.md).
