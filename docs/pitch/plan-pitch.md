# Plan del pitch de idóneo (jueves 12/11)

Tanda 1 (10:30–12:00), aula 4.2.E02. Tenemos de 5 a 7 minutos y después vienen las preguntas del jurado.

**Objetivo:** que en 6 minutos el jurado salga con tres ideas claras.

1. **El problema es real y les toca a ellos.** El perfil inversor sigue siendo un test de casillas basado en lo que el cliente *dice*, y ahora los bancos venden en un chat con IA.
2. **idóneo funciona hoy.** Lo que se ve es la versión entregada, desplegada y medida, no una maqueta.
3. **Encaja sin pisar a nadie.** idóneo no recomienda. Crea el perfil vivo, con pruebas, y se lo da al agente de la entidad (GPTadvisor, Claude, el de MyInvestor).

> Frase que tiene que quedar: **«GPTadvisor hace fiable la recomendación. idóneo hace fiable el perfil sobre el que se recomienda.»**

---

## 1. Qué puntúa y dónde lo ganamos

| Criterio (peso) | Qué pide la rúbrica | Dónde lo enseñamos |
|---|---|---|
| **Innovación y viabilidad (30 %)** | Problema real, solución útil, viable financieramente, novedoso frente a lo que existe | Vídeo (problema), diapositiva «El hueco», diapositiva «Valor para cada uno» con el coste por entrevista |
| **IA frontera (15 %)** | Lenguaje y audio avanzados con un **impacto medible** en usabilidad o accesibilidad | Vídeo (conversación por voz), prueba de audio en la demo, cifras de 43 s y unos 2 s de latencia, accesibilidad para clientes como Carmen |
| **UX y accesibilidad (15 %)** | Interfaz clara e intuitiva y tiempos de respuesta razonables | Capturas reales en el vídeo, demo en vivo cronometrada (Claude + MyInvestor en unos 16 s), QR para que lo prueben |
| **Implementación técnica (30 %)** | «Solución acabada, madura y funcional lista para ejecutar» | Arquitectura, demo en vivo de la versión entregada, tests, CI, e2e, LLMOps (`/operaciones`, juez calibrado), despliegue público |
| **Presentación (10 %)** | Problema, solución y arquitectura claros, impacto, **gestión del tiempo** y respuestas precisas | Minutado con margen, reparto de preguntas por especialista |

**Conclusión:** el 60 % (innovación + implementación) se gana demostrando que **es real y está acabado**. El vídeo emociona, pero la demo y la arquitectura son las que puntúan. Por eso la demo no se recorta: si hay que cortar, se corta en las diapositivas.

## 2. El jurado: qué valora cada uno

| Jurado | Qué le importa | Qué le decimos | Qué evitamos |
|---|---|---|---|
| **GPTadvisor (2 personas, la mitad del jurado)** | Su agente asesora a entidades y se conecta a fuentes por API y MCP. Les importa que lo que reciba sea fiable, auditable y fácil de integrar | idóneo es **una fuente más para su agente**: un MCP con 4 herramientas de solo lectura. «La IA entiende y propone, el código decide, una persona valida.» LLMOps: trazas, juez calibrado, CI que bloquea regresiones | Parecer competencia: **no recomendamos productos**. No vender «sustituimos al asesor» |
| **MyInvestor (1 persona)** | Lanzó su catálogo en ChatGPT, Claude y Perplexity con GPTadvisor (junio de 2026). La identificación y la firma se hacen en su app. La prensa habla de «zonas grises» por enseñar productos antes de conocer al cliente | El cliente que llega del chat puede traer **su perfil hecho y con pruebas**. Devolvemos las restricciones **en el formato de su catálogo** (riesgo SRRI máximo, tipo de activo, divisa). Cubre también la **conveniencia** del canal sin asesoramiento. Respetamos sus términos: nuestro backend **nunca** llama a su MCP | Criticar su chat. «Zona gris» se convierte en «oportunidad»: su chat ya trae clientes y nosotros les ponemos el perfil delante |
| **ElevenLabs (1 persona)** *(entiendo que es lo que llamas «Level Labs»; si es otra empresa, avisad)* | Que la voz no sea un adorno: agente conversacional en castellano, latencia, herramientas del agente, audio | Entrevista con ElevenLabs Agents en castellano, con herramientas de cliente (`datos_pendientes`) y de sistema (`end_call`). **El audio es la prueba**: al colgar descargamos la grabación y cada dato suena con el fragmento que lo justifica. Voz para quien no se maneja con formularios | Decir que la voz «entiende emociones» (no inferimos emociones de la voz, lo prohíbe nuestro diseño). Prometer una entrevista por voz en directo en el aula |

## 3. Estructura y minutado (objetivo 6:00, tope 6:50)

| Tiempo | Tramo | Quién habla | Pantalla | Criterio |
|---|---|---|---|---|
| 0:00–1:30 | **Vídeo** | Nadie (Rodrigo le da al play) | Vídeo a pantalla completa | Innovación, IA, UX |
| 1:30–1:50 | **Puente: el hueco** | Rodrigo | D1 «La pieza que falta» | Innovación |
| 1:50–2:35 | **Cómo funciona por dentro** | Alex | D2 Arquitectura | Implementación, IA |
| 2:35–4:35 | **Demo en vivo** | Fernán (a los mandos y narra la entidad) y Alex (narra Claude + MyInvestor) | Navegador y terminal | Implementación, UX |
| 4:35–5:10 | **Lo que hemos medido** | Pablo | D4 Medido + LLMOps | Implementación, IA |
| 5:10–5:45 | **Valor para cada uno** | Rodrigo | D5 Valor y viabilidad | Innovación (viabilidad) |
| 5:45–6:00 | **Cierre** | Rodrigo | D6 Frase, lema y QR | Presentación |
| 6:00–6:50 | **Margen** | | | Cambios de pantalla, risas, un fallo |

**Por qué este orden:** el vídeo abre con emoción; la arquitectura va antes de la demo para que el jurado sepa qué está mirando; la demo va en el centro (si falla, aún queda tiempo para recuperarse) y cerramos con cifras y valor, que no pueden fallar. Terminar con la demo es arriesgado: si se cuelga, es lo último que recuerdan.

**Si nos dicen que son 5 minutos:** el vídeo baja a 1:00 (se quita la escena 5), fuera «Lo que hemos medido» (se dice una frase en el cierre) y la demo se queda en evidencia + validación + Claude (1:30).

**Señales de tiempo:** Juan cronometra desde la primera fila y enseña tarjetas: **«3:00»** (la demo debería ir por Claude), **«5:00»** (hay que estar en «Valor») y **«6:15»** (cerrar ya, saltando lo que quede).

### Quién habla y por qué

- **Rodrigo:** abre, conecta y cierra. Lleva el pitch y la normativa, y dirige el turno de preguntas.
- **Alex:** arquitectura e integración MCP + MyInvestor. Es quien montó el MCP, el despliegue y la integración.
- **Fernán:** conduce la demo. Es el dueño del front y de la voz, así que sabe salir de cualquier pantalla rara.
- **Pablo:** lo medido. Verificador y medición son su parte del reparto.
- **Juan:** cronometra y es el especialista del backend (perfil versionado, persistencia, cálculos) en las preguntas.
- **Hammad:** si viene, responde preguntas del extractor junto a Alex.

Máximo cuatro voces en los 6 minutos: cada cambio de persona cuesta unos 5 s. Los cambios están en los bordes de los tramos, nunca en mitad de una frase. El reparto se puede cambiar, pero cada uno debe ensayar **su** texto.

## 4. El vídeo (1:30)

### Qué hace el vídeo y qué no

El vídeo **emociona y plantea el problema**. Las diapositivas **explican** y la demo **demuestra**. Si el vídeo explica la arquitectura, la repetimos y perdemos 30 s.

**Sí entra:**

- La historia de **Carmen** (68 años, 80.000 € en depósitos, quiere un complemento para la pensión). Es una persona, no un concepto.
- **Su voz** (los audios de ElevenLabs que ya están en `frontend/public/demo/carmen/`) y la frase clave: *«Eso no puede pasar, el fondo es del banco.»*
- El **contraste**: el test de casillas («Conozco bien los fondos de renta variable ✓») frente a lo que demuestra en la conversación.
- El **porqué ahora**: la inversión ya se busca en un chat con IA, y ESMA avisa de que en los sistemas automatizados el cliente se sobrevalora más.
- **Capturas reales** de la versión entregada: aura, pregunta de comprobación, tarjetas de datos entrando, aviso *declarado ≠ demostrado*, vista de la entidad, «Validar», «¿Ha cambiado algo en tu vida?».
- El **logo y el lema** al final.
- **Subtítulos quemados** en todo el vídeo: si el sonido del aula falla, se entiende igual (y es coherente con la accesibilidad que defendemos).

**No entra:**

- Arquitectura, nombres de tecnologías, cifras de tests o de evaluación (van en las diapositivas).
- Pantallas que **no** existan en la versión entregada (la rúbrica exige que lo que se enseñe sea la versión entregada).
- Imágenes generadas que parezcan fotos (Alex ya las descartó) y logos de terceros. Los nombres sí se pueden decir.
- Que idóneo recomiende un fondo, o cualquier «cumplimos MiFID».
- Música con derechos. Mejor una pista libre o generada con ElevenLabs Music.
- Más de 1:30. Cada segundo de vídeo de más es un segundo de demo de menos.

### Guion escena a escena

Narrador: una voz de ElevenLabs en castellano (distinta de la de Carmen y de la del entrevistador). En los créditos: «Voces generadas con ElevenLabs · Carmen y sus datos son simulados».

| Tiempo | Imagen | Sonido y texto en pantalla |
|---|---|---|
| **0:00–0:10** | Negro. Aparece, letra a letra: «Carmen. 68 años. 80.000 € ahorrados.» | Voz de Carmen: *«Quiero tener un dinerito extra cada mes para complementar la pensión.»* |
| **0:10–0:25** | Un formulario de casillas genérico (dibujo propio, sin marca). El cursor marca «Conozco bien los fondos de renta variable ✓» y «Siguiente». | Narrador: *«Antes de invertir, el banco tiene que saber quién eres. Hoy lo pregunta con casillas. Y Carmen marca que sabe.»* |
| **0:25–0:38** | Corte seco a negro. La frase aparece grande. | Voz de Carmen: *«Eso no puede pasar, el fondo es del banco.»* Texto: **«Declaró que sabía. No lo sabía.»** |
| **0:38–0:50** | Una burbuja de chat genérica con una búsqueda de fondos. Texto: «ESMA: el riesgo de sobrevalorarse es mayor en los sistemas automatizados.» | Narrador: *«Y ahora la inversión se busca en un chat con IA. Si el perfil está mal, la mejor recomendación también lo está.»* |
| **0:50–1:10** | Revelación: logo de idóneo y entra el aura. Captura real de `/escenario`: la pregunta *«¿Podría perder dinero un fondo así?»*, las tarjetas de datos entrando y el aviso ámbar *declarado ≠ demostrado*. | Narrador: *«idóneo cambia el cuestionario por una conversación. Pregunta, comprueba lo que de verdad entiendes y guarda la frase exacta que lo demuestra.»* |
| **1:10–1:22** | Vista de la entidad (lavanda): perfil por validar, clic en «Validar». Después, en el móvil, «¿Ha cambiado algo en tu vida?» → «Me han subido el sueldo» → las preguntas que se harán. | Narrador: *«La entidad recibe un perfil con pruebas, lo firma una persona, y el perfil sigue vivo cuando cambia la vida.»* |
| **1:22–1:30** | Fondo noche, logo y lema. | Texto: **«Del cuestionario a la conversación. Perfiles vivos que cumplen la norma.»** Silencio de 1 s antes de que hable Rodrigo |

Unas 75 palabras de narración: cabe de sobra a ritmo tranquilo.

### Cómo hacerlo esta noche

1. **Capturas (Fernán, 30 min):** grabar en el portátil, a 1080p y con el navegador a pantalla completa: `/escenario` → «Ver la demo guiada» (a 1×, luego se acelera en el montaje), `/entidad/carmen-68` (revisión, evidencias, validar) y «¿Ha cambiado algo?». Desde el **mismo commit que va en el ZIP**.
2. **Voces (Alex o Pablo, 15 min):** narración con ElevenLabs (Text to Speech). Las frases de Carmen ya están grabadas.
3. **Montaje (Rodrigo + Fernán, 1–1,5 h):** CapCut, DaVinci Resolve o Clipchamp. Subtítulos, música suave, cortes secos en 0:25 y en 0:50.
4. **Exportar en MP4 (H.264, 1080p)** y probarlo **dentro del PowerPoint** en el portátil que proyecta. Copias en un USB y en el segundo portátil.

## 5. Diapositivas

La presentación actual (`entrega/Idoneo_presentacion.pptx`) tiene 7 diapositivas técnicas. Propuesta para el pitch con vídeo: **6 en el recorrido y 5 de reserva** para las preguntas o por si falla la demo.

| # | Diapositiva | Origen | Mensaje (título) | Se ve |
|---|---|---|---|---|
| **V** | Vídeo | Nueva | — | El MP4 incrustado, que arranca al hacer clic |
| **D1** | La pieza que falta | Nueva (sustituye a la portada: el logo ya sale al final del vídeo) | «El agente ya recomienda. El perfil sigue siendo un test de casillas.» | Tres pasos: *el cliente busca en un chat* → *el agente recomienda* → *el perfil… casillas* (en ámbar). Abajo, la cita de ESMA |
| **D2** | Cómo funciona por dentro | Actual 2 | «La IA entiende y propone. El código decide. Una persona valida.» | Los 6 pasos ya dibujados |
| **D3** | Demo en vivo | Actual 7 (solo el botón) | «Demo en vivo · versión entregada · datos simulados» | Se enseña 2 s y se cambia al navegador |
| **D4** | Lo que hemos medido | Actual 6 + una fila | «Medido, con su límite» | Las 4 cifras (31/31, 70/70, 0 falsas alarmas, 43 s) y una fila nueva: *más de 750 tests sin claves · e2e en cada PR · juez LLM calibrado · trazas y costes en vivo · desplegado*. Debajo, el límite: clientes simulados |
| **D5** | Valor para cada uno | Nueva | «Una función dentro de la app de cada entidad» | Tres columnas: **GPTadvisor** (perfil fiable y auditable para su agente, por MCP), **MyInvestor** (quien llega del chat trae su perfil, y conveniencia en el canal sin asesoramiento), **La entidad** (el asesor solo interviene en los avisos; menos de 0,5 $ de IA por entrevista). El sello «Powered by idóneo» |
| **D6** | Cierre | Actual 7 | La frase de GPTadvisor + el lema | Icono, las dos frases, lema y un **QR** a la versión desplegada |
| R1 | Cada dato, con su prueba | Actual 3 | Plan B si falla la demo | |
| R2 | Lo que recibe el asesor | Actual 4 | Plan B si falla la demo | |
| R3 | Dentro de la app y por MCP | Actual 5 | Para preguntas de integración | |
| R4 | Marco normativo | Nueva (de `docs/normativa.md`) | Para preguntas legales | Art. 25 MiFID II, art. 54.7 del Reg. Delegado 2017/565, ESMA párr. 52, RGPD art. 22, Ley de IA art. 50.1 |
| R5 | Qué es real y qué simulado | Nueva (del README) | Para preguntas de madurez | |

**Ojo con la entrega:** el PowerPoint que se va a usar se entrega **hoy antes de las 23:59** con el formulario. Los cambios de diapositivas tienen que estar hechos antes. Si el MP4 pesa demasiado para el formulario, la diapositiva V lleva el vídeo enlazado (enlace no listado) y en el aula se reproduce desde el archivo local.

Reglas que ya sigue la presentación y se mantienen: Sora instalada en el portátil (o exportar a PDF), sin logos de terceros, sin valores de «confianza» en pantalla y Carmen siempre como caso simulado.

## 6. Guion palabra a palabra

Unas 2,5 palabras por segundo, a ritmo tranquilo. Las cifras entre corchetes son el tiempo de cada tramo.

### Rodrigo · Puente [20 s] · D1

> Esto que acabáis de ver no es una maqueta: es la versión que hemos entregado. Y el problema es real. Hoy los bancos ya venden en un chat, y los agentes ya recomiendan. Pero el perfil sobre el que recomiendan sigue siendo un test de casillas que se rellena en dos minutos y que nadie comprueba. Alex os cuenta cómo lo arreglamos.

### Alex · Cómo funciona por dentro [45 s] · D2

> El cliente habla con idóneo, por voz con ElevenLabs o por escrito, y Claude conduce la entrevista. En cada turno, un agente extractor propone los datos con la frase exacta del cliente. Pero el código no se fía: comprueba que la cita existe palabra por palabra y decide el nivel con una rúbrica fija. Un verificador busca contradicciones, como la de Carmen. El riesgo, la idoneidad y la conveniencia los calculan reglas en Python, nunca el modelo. Cada cambio es una versión nueva que no se sobrescribe. Y nada sale hasta que una persona de la entidad lo valida. Después, el agente de la entidad lo lee por API o por MCP. Os lo enseñamos.

### Demo en vivo [2:00] · Fernán y Alex

Guion de clics y frases en la sección 7.

### Pablo · Lo que hemos medido [35 s] · D4

> ¿Cómo sabemos que funciona? Lo hemos medido con clientes simulados y con Claude real. En siete entrevistas difíciles, con evasivas, correcciones e intentos de manipulación, acierta 31 de 31 datos y no escribe ni uno prohibido. El verificador, cero falsas alarmas. Un perfil completo, listo para validar, en unos 43 segundos. Y lo mantenemos así: más de 750 tests, una prueba de punta a punta en cada cambio y un juez calibrado con nuestras notas que bloquea una versión que empeore. El límite, claro: son clientes simulados. El siguiente paso es un piloto con personas.

### Rodrigo · Valor para cada uno [35 s] · D5

> idóneo no es otra app: es una función dentro de la app de cada entidad. Para GPTadvisor, su agente recibe un perfil fiable y auditable por MCP, sin cambiar nada. Para MyInvestor, quien llega desde el chat puede traer su perfil hecho, y cubre también la conveniencia de quien compra sin asesoramiento. Para la entidad, el asesor solo interviene cuando hay un aviso, y cada entrevista cuesta menos de medio dólar en IA. No recomendamos productos: eso lo hace el agente de la entidad. Nosotros garantizamos que sabe quién es el cliente.

### Rodrigo · Cierre [15 s] · D6

> GPTadvisor hace fiable la recomendación. idóneo hace fiable el perfil sobre el que se recomienda. Del cuestionario a la conversación: perfiles vivos que cumplen la norma. El QR os lleva a probarlo. Gracias.

## 7. La demo en vivo (2:00)

**Recomendación: no hacer una entrevista por voz en directo.** El micrófono del aula, el ruido, la red y la latencia lo hacen arriesgado, y la conversación ya sale en el vídeo. En directo enseñamos lo que **solo se cree viéndolo funcionar**: la prueba con audio, la validación humana y un agente real que usa nuestro MCP con el catálogo real de MyInvestor. La voz en directo se ofrece en las preguntas, con el QR.

Todo en **local** (la validación y el MCP de demostración solo funcionan en local, a propósito) y con el **mismo commit que el ZIP**.

| Tiempo | Clic (Fernán) | Quién dice qué |
|---|---|---|
| **0:00–0:10** | Pestaña ya abierta en `localhost:3000/entidad/carmen-68`, vista de revisión | **Fernán:** «Esto es lo que recibe el asesor tras la conversación de Carmen: el perfil ya hecho, conservador, y un aviso.» |
| **0:10–0:35** | Pestaña **Evidencias** → **Conocimiento: fondos de renta variable** → ▶ | **Fernán:** «Declaró que conocía bien la renta variable. Escuchad lo que demostró.» *(suena: «Eso no puede pasar, el fondo es del banco.»)* «Cada dato guarda su frase, el segundo exacto y su audio. Si el asesor duda, lo escucha.» |
| **0:35–0:45** | **Validar perfil** → aparece `active`, versión nueva | **Fernán:** «Nada sale sin que una persona firme. Ahora sí, el perfil está disponible para el agente.» |
| **0:45–1:30** | Cambiar a la terminal con Claude Code ya abierto y el prompt ya escrito. **Enter.** | **Alex:** «Ahora hacemos de GPTadvisor. Claude es el agente de la entidad, con dos conectores: el nuestro y el MCP público de MyInvestor, el que lanzaron con GPTadvisor.» *(mientras responde, unos 16 s)* «Le pedimos los límites de Carmen: riesgo máximo tres de siete, nada de renta variable porque no la entiende. Y con esos límites busca en el catálogo real.» *(sale el resultado)* «Fondos de renta fija y monetarios en euros, riesgo tres o menos, ninguno de renta variable, y el porqué con la frase de Carmen. Nosotros no elegimos los fondos: ponemos los límites. Elige el agente.» |
| **1:30–1:55** | *Solo si el reloj marca menos de 4:10 y salió bien en el ensayo de esta noche (necesita un perfil de cliente ya validado y abierto en su pestaña; si no, se omite, porque ya sale en el vídeo).* Cambiar a la pestaña del cliente, **Mi perfil** → **¿Ha cambiado algo en tu vida?** → «Me han subido el sueldo» | **Fernán:** «Y cuando la vida cambia, no se repite el test. El cliente lo cuenta y solo se le pregunta lo afectado. Lo decide el código, no el modelo, y la entidad ve el antes y el después.» |
| **1:55–2:00** | Volver al PowerPoint (D4) | — |

Prompt para Claude Code (corto, porque el largo daba respuestas demasiado largas en E-09):

> Usa idóneo para leer las restricciones de carmen-68 y busca en MyInvestor 3 fondos compatibles. Explica en 4 líneas qué descartas y por qué, con la evidencia de la entrevista.

### Preparación (T-60 min, en el aula o justo antes)

- [ ] Portátil enchufado, en modo no molestar, notificaciones fuera, brillo al máximo y resolución 1920×1080. Pantalla duplicada y **probada con el proyector del aula**.
- [ ] Sonido: que se oiga el vídeo y el ▶ de la evidencia en la sala. Llevar un altavoz por si acaso.
- [ ] Backend y frontend en local arrancados con `next build` (nada de `npm run dev`), y el log con `MODO ASESOR DE DEMO ACTIVO` y `CREDENCIAL MCP DE DEMO ACTIVA`.
- [ ] **Reiniciar la demo** (Carmen vuelve a «por validar»).
- [ ] Claude Code abierto **en la misma terminal** donde se exportó `IDONEO_MCP_TOKEN`; `claude mcp list` con `idoneo` y `myinvestor` conectados; el prompt escrito sin pulsar Enter. Fuente de la terminal a 20 pt.
- [ ] Hacer **una pasada completa en seco** (validar + Claude) y volver a reiniciar la demo.
- [ ] Pestañas en este orden: PowerPoint · `/entidad/carmen-68` · terminal · perfil del cliente. Saber el atajo para cambiar entre ellas sin buscar.
- [ ] Datos móviles compartidos listos por si falla la wifi (Claude y MyInvestor necesitan red).
- [ ] Despertar la versión desplegada (abrirla 10 min antes: el plan gratuito tarda cerca de un minuto en la primera petición) para que el QR funcione.

### Plan B

**Regla de los 10 segundos:** si algo no responde en 10 s, no se arregla en el escenario. Se dice una frase y se pasa al plan B.

| Si falla… | Hacemos | Frase |
|---|---|---|
| El vídeo no suena | Sigue con subtítulos | — |
| El vídeo no arranca | Archivo MP4 desde el escritorio o el USB; si tampoco, Rodrigo cuenta la historia de Carmen en 30 s con D1 | «Os lo contamos nosotros.» |
| El ▶ de la evidencia no suena | Leer la cita en voz alta y seguir | «Lo dice ella, en el segundo 57.» |
| «Validar» da error | «Reiniciar la demo» una vez; si no, R2 | «Así queda tras validarlo.» |
| Claude tarda más de 25 s o falla | Vídeo de respaldo de E-09 (grabado esta noche, 30 s) | «Para no esperar a la red, aquí lo tenéis grabado con esta misma versión.» |
| No hay red | Vídeo de respaldo de toda la demo (1:30) | Igual |
| Se cuelga el portátil | Segundo portátil con el PDF de las diapositivas y los dos vídeos de respaldo | — |

**Esta noche hay que grabar dos vídeos de respaldo** desde el commit del ZIP: (1) la demo entera de la tabla (1:30) y (2) solo Claude + MyInvestor (30 s). Así el plan B también es la versión entregada.

## 8. Qué decir y qué no

**Decir:**

- «Versión entregada», «datos simulados», «lo valida una persona».
- «Declarado frente a demostrado» y «cada dato con su prueba».
- «No recomendamos: ponemos los límites. Elige el agente de la entidad.»
- Las cifras **con su límite** (clientes simulados). Al jurado técnico le da más confianza la honestidad que el 100 %.
- Los nombres de quienes nos escuchan (GPTadvisor, MyInvestor, ElevenLabs), con lo que ganan.

**No decir:**

- «Cumplimos MiFID» o «aprobado por la CNMV». Ayudamos a la entidad a **recoger y documentar** la evaluación; la responsabilidad sigue siendo suya. El lema dice «cumplen la norma»: si preguntan, se matiza así.
- «Sustituimos al asesor» o «recomendamos fondos».
- «La IA entiende las emociones de la voz» (no lo hacemos, y es justo lo que la Ley de IA mira con lupa).
- Cifras de mercado que no hayamos comprobado (tamaño del mercado, multas, ahorro en euros) o un precio.
- Jerga interna: `pending_review`, Pydantic, «el fixture», `messages.parse`, nombres de ramas.
- «Esto todavía no funciona», «no nos ha dado tiempo» o disculpas. Lo que falta se cuenta como hoja de ruta.
- Leer las diapositivas.

## 9. Preguntas probables del jurado

**Cómo responder:** Rodrigo reparte la pregunta al especialista en una palabra («Alex»). Respuesta en menos de 30 s: primero el sí o el no, después una prueba y se calla. Si no lo hemos medido, se dice: «no lo hemos medido; lo mediríamos así».

| Tema | Responde |
|---|---|
| Arquitectura, MCP, MyInvestor, despliegue, LLMOps, extractor | Alex |
| Perfil versionado, persistencia, cálculos, seguridad del backend | Juan |
| Verificador y evaluación | Pablo |
| Interfaz, voz y accesibilidad | Fernán |
| Normativa, negocio y visión | Rodrigo |

### GPTadvisor

**¿Qué pasa si el modelo se inventa un dato?** *(Alex)*
El modelo solo propone. El código comprueba que la cita aparece literal en lo que dijo el cliente y, si no, descarta el dato con su motivo. La confianza la pone una rúbrica fija, no el modelo. En siete entrevistas difíciles, cero datos prohibidos escritos. Y al final firma una persona.

**¿Cómo se integra con nuestro agente?** *(Alex)*
Como una fuente más, que es como ya trabaja vuestro agente: un servidor MCP con cuatro herramientas de solo lectura (restricciones, evidencia, perfil y contexto) o la API REST. Lo hemos probado con Claude y el conector de MyInvestor, y en producción se autenticaría con OAuth del conector.

**¿Por qué no recomendáis vosotros también?** *(Rodrigo)*
Porque eso ya lo hacéis vosotros, y bien. Lo que falta es la entrada: si el perfil está mal, la mejor recomendación también. Separarlo además deja claro quién responde de qué.

**¿Cómo sabéis que no empeora al cambiar un prompt?** *(Alex)*
Cada llamada a Claude queda trazada, sin guardar lo que dice el cliente. Tenemos un juez LLM calibrado contra nuestras notas (acuerdo de ±1 punto en el 100 % de los casos) y la CI de evaluaciones bloquea una versión que baje de los umbrales. La página `/operaciones` enseña latencia, caché, fallos y coste por agente y por versión de prompt.

**¿Qué modelos usáis y por qué?** *(Alex)*
Claude Sonnet 5.5 con esfuerzo bajo en el entrevistador escrito, el extractor y el verificador: unos 2 s por llamada. En la voz, el agente de ElevenLabs usa Claude Haiku 5.5 por latencia. Cada agente tiene su modelo configurable.

**¿Y si el cliente miente?** *(Pablo)*
No detectamos mentiras: detectamos incoherencias y lo que no se demuestra. Si dice que sabe y no lo demuestra, vale lo demostrado y salta el aviso. Si pide «apunta que sé mucho», no se escribe: es uno de los casos de prueba.

### MyInvestor

**¿Llamáis a nuestro MCP desde vuestro servidor?** *(Alex)*
No. Vuestros términos solo permiten usarlo como conector dentro de una conversación, así que nuestro backend nunca lo llama. Devolvemos las restricciones en el formato de vuestro catálogo y es el agente quien busca. Si nos dais permiso, la integración directa es inmediata.

**¿Cómo encaja con el chat en ChatGPT y Claude?** *(Rodrigo)*
Hoy el chat enseña productos antes de conocer al cliente, y la identificación llega luego, en la app. Con idóneo, el perfil se hace en una conversación, con pruebas, y el agente ya sabe qué límites respetar. Sería la siguiente fase: que el perfil de idóneo sustituya al test del alta.

**¿Sirve para quien compra ETF o acciones sin asesoramiento?** *(Juan)*
Sí. Calculamos idoneidad y también conveniencia por familia de producto, que es lo que exige el canal sin asesoramiento. Carmen sale conveniente para depósitos, monetarios y renta fija, y no para renta variable.

**¿Qué pasa si cambia la vida del cliente?** *(Fernán)*
Pulsa «¿Ha cambiado algo?» y elige qué ha pasado. Un planificador determinista decide qué preguntar, seis preguntas como máximo, sin repetir la entrevista. Mientras nadie valida, el agente sigue usando la última versión validada y sabe qué datos están en revisión.

### ElevenLabs

**¿Por qué voz y no un formulario mejor?** *(Fernán)*
Porque el problema es de comprensión, no de diseño del formulario: en una casilla, Carmen marca «sé»; en una conversación, demuestra que no. Y la voz abre la puerta a quien no se maneja con formularios. Siempre hay subtítulos y alternativa por escrito.

**¿Qué usáis de ElevenLabs?** *(Fernán / Alex)*
ElevenLabs Agents en castellano con una herramienta de cliente (`datos_pendientes`, para que la entrevista sepa qué falta) y la de colgar. El prompt vive en el repo y se sincroniza con un script. Al colgar, el backend descarga el audio y alinea los tiempos, así cada dato suena con su fragmento. Las voces de la demo guiada también son de ElevenLabs.

**¿Qué latencia tiene?** *(Alex)*
La primera entrevista por voz completa fueron 45 turnos en unos 6 minutos. Por escrito, unos 2 s por respuesta, y el extractor trabaja en segundo plano sin retrasar la conversación. La voz no la hemos medido turno a turno; es lo siguiente.

**¿Usáis la voz para identificar al cliente?** *(Rodrigo)*
No. La voz no se usa para identificar (sería un dato biométrico, art. 9 del RGPD) ni para inferir emociones. La identificación la sigue haciendo la entidad.

**¿Otros idiomas?** *(Fernán)*
Hoy, castellano. El agente de ElevenLabs admite muchos idiomas y el perfil no depende del idioma: es lo siguiente en accesibilidad.

### Generales

**¿Es viable? ¿Cuánto cuesta?** *(Rodrigo)*
La parte de IA cuesta menos de medio dólar por entrevista (estimado a partir de los tokens), más los minutos de voz. Lo contrata la entidad como una función de su app. A cambio, el asesor solo interviene en los avisos y el perfil queda documentado para el supervisor. El precio se fija con la entidad.

**¿Está mejor que el test de casillas? ¿Lo habéis comparado?** *(Pablo)*
No lo hemos comparado con personas reales, y lo decimos. Lo siguiente es un piloto: las mismas personas con el test y con idóneo, midiendo tiempo, contradicciones detectadas y cuántas veces el asesor cambia el perfil.

**¿Quién responde si el perfil está mal?** *(Rodrigo)*
La entidad, como hoy. idóneo le ayuda a cumplir el art. 54.7 del Reglamento Delegado 2017/565 (información fiable y coherente) y lo que pide ESMA en el párrafo 52 contra la sobrevaloración. Y por eso firma una persona (art. 22 del RGPD).

**¿Es de alto riesgo según la Ley de IA?** *(Rodrigo)*
Según el texto, el perfilado para invertir no está en el Anexo III. Sí aplica el aviso del art. 50.1, y la entrevista lo da al empezar. No es una opinión jurídica.

**¿Qué es real y qué simulado?** *(Juan)*
Reales: Claude como entrevistador, extractor y verificador, la voz con ElevenLabs, nuestro MCP y el catálogo de MyInvestor. Simulados: Carmen y el resto de clientes y los umbrales de los cálculos, que son supuestos nuestros pendientes de revisión experta.

**¿Está listo para producción?** *(Juan)*
Está desplegado (Vercel, Render y Supabase) con topes diarios de gasto y se instala en 10 minutos con el README. Para una entidad faltan identidad real: login del cliente, SSO del asesor y OAuth en el MCP. La validación y el MCP de demostración solo funcionan en local, a propósito.

**¿Cómo guardáis los datos? ¿Se pueden borrar?** *(Juan)*
El perfil es una cadena de versiones que no se modifican: en Postgres la propia base bloquea `UPDATE` y `DELETE` del registro. La memoria personal va aparte, con su consentimiento, y se puede borrar.

**¿Qué haríais con tres meses más?** *(Rodrigo)*
Piloto con personas reales, identidad y OAuth, comprobaciones que pidan agentes autorizados y medición de la voz turno a turno.

## 10. Esta noche y mañana

Hora de Madrid. La entrega cierra hoy a las **23:59**.

| Cuándo | Qué | Quién |
|---|---|---|
| Ya | Congelar el código del ZIP y anotar el commit | Alex |
| 20:30–21:15 | Capturas del vídeo y los dos vídeos de respaldo desde ese commit | Fernán |
| 20:30–21:00 | Narración con ElevenLabs | Alex o Pablo |
| 21:00–22:30 | Montaje del vídeo | Rodrigo + Fernán |
| 21:00–22:30 | Diapositivas D1, D4, D5, D6 y las de reserva en `build.js` | Alex o Rodrigo |
| 22:30–23:15 | Ensayo completo cronometrado, dos veces (vale por videollamada) | Todos |
| Antes de 23:45 | PowerPoint final, PDF de una cara, ZIP y formulario | Alex |
| Mañana 9:00 | Último ensayo con el reloj | Todos |
| Mañana 10:00 | Aula: proyector, sonido, red y la preparación de la sección 7 | Fernán + Juan |

**Ensayar con el reloj es lo que más puntúa por hora invertida.** La gestión del tiempo está en la rúbrica y la mayoría de equipos se pasa.
