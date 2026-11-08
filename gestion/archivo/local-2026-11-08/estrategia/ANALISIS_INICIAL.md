# Análisis inicial del reto — 8 de noviembre de 2026

## Fuente y límites
Documento recibido: [Completo hack finance.pdf](../Completo%20hack%20finance.pdf), dos páginas, SHA-256 `2182c34ebb762066c28dbd46af7ddf36d9d12c610bd052fcfb2a928063701341`. La ruta de Downloads indicada no existía al consultar; se leyó y renderizó la copia local del proyecto. El PDF describe rúbrica y entrega; no sabemos si agota las bases.

## Criterios oficiales (p. 1)
| Criterio | Peso | Qué se pide |
| --- | ---: | --- |
| Innovación y viabilidad | 30 % | Problema financiero real, solución útil y aplicable, viabilidad financiera y novedad competitiva frente al mercado. |
| IA frontera | 15 % | Valor diferencial e impacto medible de lenguaje y audio avanzado en usabilidad, interactividad o accesibilidad. |
| UX y accesibilidad | 15 % | Interfaz clara, funcional e intuitiva; tiempos de respuesta razonables. |
| Implementación y código | 30 % | Solución acabada, madura, funcional y lista para ejecutar. |
| Presentación | 10 % | Claridad del problema, solución y arquitectura; impacto y diferencial; tiempo y respuestas. |

Interpretación: creatividad y ejecución suman 60 %, pero no se deben despreciar los restantes 40 puntos. El PDF no establece un modelo concreto, un agente obligatorio, pesos internos, ni que la ausencia de voz descalifique. El 8/11 Fernán aclara que la voz no es obligatoria, aunque el apartado IA la menciona expresamente: valorar cuándo añade utilidad medible y confirmar cómo se aplicará la rúbrica.

## Entrega y aclaraciones
El PDF p. 2 pide GitHub público o compartido con las personas indicadas por organización; ZIP descargado desde GitHub (versión oficial evaluada); README con descripción, requisitos y pasos de instalación, configuración, ejecución y prueba; PDF de una cara sobre problema, solución y diferencial; y PowerPoint. Envío por formulario BEST. Cuenta la última entrega completa dentro del plazo. Cualquier demo debe coincidir con la versión entregada; tras el cierre no se admiten modificaciones.

El PDF pide entregar PowerPoint y luego dice que las diapositivas son opcionales. Fernán aclara que hay que entregar PowerPoint; el uso de diapositivas durante la presentación sigue siendo opcional según el PDF. Fernán indica cierre **miércoles 23:59** y presentación **aproximadamente 10 minutos**, sin confirmación de duración. Provisionalmente 11/11/2026 en hora de Madrid; confirmar zona y horario preciso. Recursos comunicados: 400 € en créditos de Claude y suscripción ElevenLabs Creator; no conocemos límites, titular, periodo o APIs habilitadas.

## Investigación: hecho e hipótesis
- [GPTAdvisor: casos de uso](https://www.gptadvisor.com/casos-de-uso.html) anuncia preparación de reuniones, memoria de clientes, cartera, comparativas y respuestas basadas en documentación. Conclusión: un copiloto genérico de asesor o resumen de reunión se solapa con funciones que ya publicita. No acredita necesidades internas ni quién será jurado.
- [MyInvestor: carteras automatizadas](https://myinvestor.es/inversion/carteras-automatizadas/) anuncia carteras y acceso a su catálogo desde asistentes de IA. Un recomendador de fondos genérico parte con competencia evidente. No sabemos si las necesidades o funciones no publicitadas coinciden con nuestras hipótesis.
- [Finanzas para todos: ECF 2021](https://www.finanzasparatodos.es/encuesta-de-competencias-financieras-2021-tenemos-margen-de-mejora) informa que el 19 % contestó bien tres preguntas concretas; trabajo de campo nov. 2021–jul. 2022 entre población de 18 a 79 años. Es contexto de alfabetización, no prueba de incomprensión de un producto concreto ni de una necesidad de MyInvestor.
- [Aveni Detect](https://aveni.ai/blog/consumer-duty-ai-tools-complete-implementation-guide-for-uk-financial-services/) publicita análisis de comunicaciones, claridad y seguimiento de comprensión. Existe solapamiento con posibles ideas; no afirmar ser los primeros ni compararnos sin probar condiciones.
- [FCA: buenas prácticas sobre IA financiera](https://www.fca.org.uk/publications/good-poor-practice/ai-financial-services) recomienda delimitar necesidades, probar resultados y no presumir que los usuarios comprenden las comunicaciones. Es contexto británico, no una norma española aplicable automáticamente.
- [Embat: conciliación](https://www.embat.io/es/automatizacion-conciliacion-contable) ofrece conciliación continua y tratamiento de excepciones. Otra solución genérica de conciliación requiere un segmento o mecanismo distinto.

## Candidatas para contrastar, no seleccionadas
**A. Comprensión de una decisión de inversión.** Una persona consulta un documento real de un solo producto, ve fuente, costes y riesgos y explica una situación con sus propias palabras; el sistema detecta dudas o datos no respaldados, pide aclaración y ofrece traspaso a un asesor. Cliente potencial entidad financiera; usuarios: clientes y asesores. Voz bidireccional opcional cuando ayude al usuario; vía texto equivalente. Riesgo: GPTAdvisor y Aveni ya cubren partes, y no hay demostración de necesidad en el sponsor. Diferencial propuesto a validar: detectar una confusión concreta del cliente y preservar fuente, incertidumbre y seguimiento, con medición de comprensión; no afirmar novedad absoluta ni demostrar idoneidad/consentimiento.

**B. Liquidez ligada a objetivos.** Un inversor expresa en voz/texto plazos e hitos; una línea de tiempo contrasta aportaciones y necesidades con una simulación determinista parametrizada, cita supuestos y detecta falta de información. Comprador potencial entidad/asesor. Riesgo: GPTAdvisor anuncia memoria y análisis de carteras; la diferencia tendría que estar en la prueba específica, el motor y la explicación, no en recordar fechas. No recomendar inversiones ni conectar cuentas reales como supuesto.

**C. Gestión de excepciones de cobros para autónomos.** Factura y movimiento sintéticos que no casan; proponer causas con evidencia, pregunta de aclaración y revisión del usuario. Riesgo: Embat ya automatiza conciliación; voz y encaje con sponsors no son evidentes. Segmento, datos y complejidad han de validarse antes de construir.

Recomendación provisional: investigar A y B con ejemplos concretos y buscar un motivo de descarte; elegir solo con el equipo, después de hablar con expertos disponibles y consultar competidores. La lista no agota ideas. No se ha validado demanda, diferencia real, disposición a pagar, beneficios ni jurado.

## Validación y próxima sesión de equipo
1. Acordar usuario, momento de fricción, trabajo actual, coste del problema, comprador y alternativa para dos candidatas. Buscar 1–3 opiniones directas si es posible, sin atribuirles representatividad.
2. En 60–90 minutos por candidata: construir guion de una única demo; caso con entradas/salidas y resultado verificable; probar la mayor dependencia y descubrir competidores. Registrar motivo de descarte y no puntuar con pesos inventados.
3. Definir pruebas: casos normales, incompletos, conflictivos y fuera de alcance; revisión de fuente y cifras; latencia/coste observados. Si audio aporta valor, comparar tareas equivalentes con texto con y sin audio, alternando orden, explicitar muestra y no declarar significación general con pruebas pequeñas.
4. Estimar viabilidad: ingresos supuestos por cliente menos coste de modelo, audio, infraestructura y operación; distinguir coste medido de hipótesis, medir tokens/minutos y no vender proyecciones como negocio probado.
5. MVP completo pronto. Descargar el ZIP candidato de GitHub, identificar commit y hash, probarlo en entorno limpio, asegurar acceso al jurado y ensayar la misma versión. Recoger comprobante del formulario.

## Estado de coordinación
Análisis e indicaciones guardados localmente. La carpeta local no es un checkout Git; cambios posteriores al merge dbb06ff no se han sincronizado automáticamente con el repositorio cloud. No copiar claves al repositorio. Actualizar la versión compartida tras comparar y sincronizar explícitamente.
