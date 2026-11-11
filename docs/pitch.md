# Pitch: cifras, cierre y preguntas del jurado

De dónde sale cada cifra nueva de la presentación (diapositivas 6, 7 y 8 de [`entrega/fuente-presentacion/build.js`](../entrega/fuente-presentacion/build.js)), qué contestar a las preguntas previsibles y qué revisar el día de la demo.

> Todos los clientes son **simulados**. Lo que aquí se marca como «estimado» o «supuesto» no está medido: hay que sustituirlo o decirlo así.

## Diapositiva 6 · Frente al test de casillas

**0 de 5 frente a 5 de 5.** En la tirada E-07 del laboratorio hay cinco entrevistas en las que la ficha oculta del cliente dice conocer bien la renta variable y, en realidad, cree que un fondo no puede perder. Un test que registra lo que el cliente marca no detecta ninguna. idóneo abrió la alerta *declarado ≠ demostrado* en las cinco.

| Entrevista | Transcripción | Alerta en `knowledge.equity_funds` |
|---|---|---|
| Carmen, primera repetición | [carmen-jubilada-confiada-r1.txt](evaluacion/laboratorio/e07/carmen-jubilada-confiada-r1.txt) | sí |
| Carmen, segunda repetición | [carmen-jubilada-confiada-r2.txt](evaluacion/laboratorio/e07/carmen-jubilada-confiada-r2.txt) | sí |
| Rosa, 42 años | [v004-rosa-42.txt](evaluacion/laboratorio/e07/v004-rosa-42.txt) | sí |
| Rosa, 71 años | [v009-rosa-71.txt](evaluacion/laboratorio/e07/v009-rosa-71.txt) | sí |
| Íñigo, 25 años | [v012-íñigo-25.txt](evaluacion/laboratorio/e07/v012-%C3%AD%C3%B1igo-25.txt) | sí |

Fuente: [informe-personas.md](evaluacion/laboratorio/e07/informe-personas.md) e [informe-variantes.md](evaluacion/laboratorio/e07/informe-variantes.md). Son cinco entrevistas y cuatro clientes distintos: Carmen se entrevistó dos veces.

Las otras dos alertas esperadas de E-07 son de Ramón, que intenta saltarse el test: son `needs_advisor`, no *declarado ≠ demostrado*, y no entran en esta cifra.

**«No rebaja a quien sí sabe».** El verificador no dio ninguna falsa alarma en 24 pruebas (E-06). En el laboratorio, Javier, que sí sabe, salió con 10 de 10 datos las dos veces y sin alerta esperada.

Cómo decirlo:

- Es una **tasa de detección** sobre casos escritos para sobrevalorarse. No dice cuántos clientes reales se sobrevaloran. Decir «de las cinco entrevistas en que el cliente se sobrevaloraba»; no decir «uno de cada cuatro clientes».
- La comparación es **por construcción**: supone un test que se limita a registrar la casilla. No se ha medido contra el test real de ninguna entidad.

## Diapositiva 7 · Lo que cuesta preguntar bien

| Cifra | De dónde sale | Estado |
|---|---|---|
| ≈ 1 € por entrevista de voz | Claude: entre 0,30 y 0,45 $ por entrevista, estimado a partir de los tokens ([evaluacion/README.md](evaluacion/README.md)). Voz: unos seis minutos (E-03) a entre 0,08 y 0,10 $ por minuto | **Estimado.** El precio por minuto sale de resúmenes de terceros ([happyrobot.ai](https://www.happyrobot.ai/hub/elevenlabs-pricing), [layer3labs.io](https://www.layer3labs.io/guides/elevenlabs-pricing)) que no coinciden entre sí. Sustituir por la factura de ElevenLabs |
| ≈ 10 € con un asesor | 20 minutos a 30 €/h | **Supuesto del equipo.** Sustituir por la cifra de un mentor de MyInvestor o de GPTadvisor |
| 200.000 € de multa | Resolución de la CNMV de 16 de octubre de 2025, [BOE-A-2025-21658](https://www.boe.es/boe/dias/2025/10/27/pdfs/BOE-A-2025-21658.pdf): a CA Indosuez Wealth (Europe), Sucursal en España, «por no recabar información necesaria sobre los conocimientos y experiencia de sus clientes para evaluar la conveniencia e idoneidad» | **Comprobado en el texto oficial.** Infracción muy grave del art. 293.1.a) de la Ley 6/2023, por el art. 203 en relación con los arts. 204 y 205 y con los arts. 54 y 55 del Reglamento Delegado 2017/565 |

Cómo decirlo:

- La resolución recoge **dos** multas de 200.000 € a la misma entidad. La otra es por no informar de costes e incentivos y no tiene que ver con el perfil: no sumarlas.
- Decir por qué fue la multa y parar ahí. No decir que idóneo la habría evitado.
- Son **costes**, no un precio. La regla de la presentación se mantiene: no se dice precio. Si preguntan, lo contrata la entidad y lo integra como una función más.

## Diapositiva 8 · Cierre con dos peticiones

1. **Un piloto:** 100 altas reales de MyInvestor, el test de casillas frente a idóneo. Es la medición que falta: clientes reales y el test real de una entidad.
2. **Permiso** para consultar su catálogo por MCP desde nuestro backend. Hoy sus [términos](https://mcp.myinvestor.es/terms) solo permiten usarlo como conector dentro de una conversación ([diseno/04-mcp-myinvestor.md](diseno/04-mcp-myinvestor.md)).

Si la demo en directo va después de las diapositivas, volver a esta al acabar: la petición debe ser lo último que oiga el jurado.

**Antes del pitch: preguntar a GPTadvisor si su producto ya perfila al cliente.** La pregunta está abierta desde la [auditoría del 8 de noviembre](diseno/02-auditoria-y-decisiones.md). No hemos encontrado nada público que lo confirme ni que lo descarte. Si contestan que sí, la frase del cierre pasa a ser: «somos la capa de pruebas debajo de vuestro perfil: cada dato con su cita literal, comprobada por código».

## Preguntas del jurado

| Pregunta | Respuesta |
|---|---|
| «¿Seis minutos frente a dos de un formulario? Eso hunde la conversión.» | El alta completa por voz son unos seis minutos. La versión corta por escrito deja el perfil listo para validar en 43 segundos (E-08), y después solo se pregunta lo que ha cambiado, con un máximo de seis preguntas |
| «Cero falsas alarmas. ¿Y cuántas se os escapan?» | En la prueba del verificador acertó 21 de 24 (E-06). Los tres fallos eran el mismo caso; se corrigió y al repetirlo salió 3 de 3 |
| «Nuestro test ya tiene preguntas de control.» | Entonces detecta una parte, y la comparación de la diapositiva 6 no es contra ese test: es contra uno que registra la casilla. La diferencia que queda es que unas preguntas fijas se aprenden y no dejan prueba; aquí cada dato guarda la frase del cliente. Por eso pedimos el piloto |
| «Los umbrales os los habéis inventado.» | Son supuestos nuestros y lo decimos. Están aislados en las reglas (`calculos.py` y `rubrica.py`, con su versión), listos para sustituirse por la política de idoneidad que cada entidad ya tiene aprobada |
| «¿Por qué no lo construye GPTadvisor en un sprint?» | La conversación es lo fácil. Lo que aguanta una inspección es que cada dato lleve su cita literal comprobada por código, una rúbrica fija y evaluaciones que se repiten con cada cambio, y eso ya está hecho |
| «El cliente se aprenderá las respuestas.» | El test de casillas se supera marcando una casilla. Aquí hay que explicar con tus palabras qué pasa si el fondo cae, y si la respuesta no convence decide el asesor |

## El día de la demo

- **Que el backend no se duerma.** El plan gratuito de Render se apaga a los 15 minutos sin uso y tarda cerca de un minuto en despertar; el plan Starter no ([despliegue.md](despliegue.md)). Pasar a Starter ese día o llamar a `/api/health` cada diez minutos.
- **Topes de gasto.** `LIMITE_VOZ_DIA` (10) y `LIMITE_SESIONES_DIA` (30) en `render.yaml` se agotan pronto si el jurado prueba la web. Subirlos ese día y volver a bajarlos después.
- **La pantalla de evidencias, a mano.** La vista de la entidad pide la clave del equipo. Llevar la clave, o un QR a la demo guiada, en el resumen de una cara que se entrega.
- **Plan B.** Vídeo grabado de la entrevista y perfil de Carmen precargado, por si falla la red o el micrófono ([diseno/01-diseno.md](diseno/01-diseno.md)). El hueco del vídeo en el README sigue vacío.
- **Tipografía.** Sora instalada en el equipo que proyecta, o exportar antes a PDF ([fuente de la presentación](../entrega/fuente-presentacion/README.md)).

## Prueba con cinco personas

La objeción más fuerte a la evaluación es que todos los clientes son Claude. Cinco personas la contestan, y la auditoría del 8 de noviembre ya lo pedía.

1. Primero, la pregunta de casilla: «¿Conoce los fondos de renta variable? Nada, básico, medio o alto.» Apuntar la respuesta.
2. Después, la entrevista corta por voz (`/onboarding/entrevista`). Cifras inventadas y conocimiento real: no se introducen datos reales.
3. Comparar lo que marcó con el nivel que quedó en el perfil. Contar cuántos marcaron más de lo que demostraron.
4. Pedir permiso a una de las personas para citar una frase suya, sin nombre.

Con el resultado, la diapositiva 6 puede añadir una línea: «y en N de 5 personas reales».
