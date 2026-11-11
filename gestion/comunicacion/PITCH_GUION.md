# Guion del pitch — 6 minutos (diapositivas, luego demo)

Borrador v3 · 10 nov 2026 · Responsable: Rodrigo · Revisión: equipo
Presentación: [`Idoneo_presentacion.pptx`](Idoneo_presentacion.pptx) (las notas del orador llevan este mismo texto). Se genera con [`fuente-presentacion/`](fuente-presentacion/README.md): versión de trabajo (con etiquetas ámbar) o `--final`.

> **Cuándo.** Jueves 12/11, Tanda 1 (10:30-12:00), aula 4.2.E02. **Somos los últimos de la tanda.** Duración oficial: **5-7 minutos** (fuente: `[MEW26] Horas de presentaciones`, no incluido en el repo). Este guion dura 6 min.
> **Orden.** Primero **3:45 de diapositivas** y después **salto directo a la demo en vivo (2:15)**. La demo es lo último que ve el jurado.
> **Marcas.** `[PENDIENTE: …]` = dato o función que aún no existe. **No se dice en voz alta como hecho.**

## Qué ha cambiado desde la v2 (9/11)

| Antes | Ahora | Fuente |
|---|---|---|
| Voz sin probar | Probada **una vez** de punta a punta (45 turnos, 6 min) | E-03 |
| Extractor de mentira (stub) | Claude extrae los datos en directo | E-04, E-05 |
| «Si no se mide, no se dice» | Hay cifras medidas, **con sus límites** | E-04, E-05 |
| MCP sin URL | Claude leyó el perfil por un túnel temporal | README, 9/11 |
| Colores azul y verde | Estilo «noche» de la web nueva, con su esfera 3D | PR 22 |

Las fuentes `E-0x` están en `gestion/evaluacion/PLAN_Y_EVIDENCIAS.md`.

## Una frase para todo el pitch

> *El test MiFID se fía de lo que el cliente dice de sí mismo. Idóneo lo convierte en una conversación que comprueba y deja pruebas.*

## Guion hablado

### Diapositiva 1 · Portada (0:00 – 0:05)

> Buenos días. Esto es Idóneo: tu perfil inversor, en una conversación.

`[PENDIENTE: si el equipo decide decir su nombre («Somos Real Betis…»). No sale escrito en la portada, solo se dice.]`

### Diapositiva 2 · Carmen: lo que marcó y lo que dijo (0:05 – 0:38)

> Imaginad a Carmen. Tiene 68 años y 80.000 euros en depósitos. En el test MiFID de su banco marcó que conoce bien los fondos de renta variable.
>
> Pero cuando le preguntan si un fondo así podría perder dinero, dice: *«eso no puede pasar, el fondo es del banco»*. Marcó una cosa y demostró la contraria.
>
> Y el test, que se fía de lo que ella declara, no lo detecta.
>
> *(Carmen es un caso simulado.)*

### Diapositiva 3 · Habla, comprueba y deja pruebas (0:38 – 1:08)

> Idóneo cambia el test por una conversación.
>
> Habla: el cliente contesta por voz o por escrito, desde el móvil. Comprueba: plantea escenarios y contrasta lo declarado con lo demostrado. Y deja pruebas: cada dato con su frase, su fuente y su versión.
>
> Nosotros no recomendamos productos: garantizamos que el agente de la entidad sabe quién es Carmen.

`[PENDIENTE: clip de audio por dato. Hasta que exista, no se dice «y su audio».]`

### Diapositiva 4 · Cada dato queda con su prueba (1:08 – 1:38)

> Así se ve el paso clave. Carmen dice «eso no puede pasar». Claude lo extrae mientras habla y lo compara con lo que declaró: había dicho alto, ha demostrado ninguno.
>
> El dato queda guardado con su fuente, la frase exacta y el minuto en que lo dijo. Con su tolerancia al riesgo pasa igual: declaró tres sobre cinco, demostró uno.

### Diapositiva 5 · Lo que recibe la entidad (1:38 – 2:10)

> Esto es lo que ve la entidad. Carmen es conservadora: riesgo máximo tres sobre siete. Sale de tres criterios y manda el más restrictivo, su tolerancia al riesgo.
>
> Y la conveniencia: los depósitos y la renta fija, sí; la renta variable, no. Todo lo calculan reglas fijas en código, no el modelo. Y hasta que una persona de la entidad lo valida, el agente no puede usarlo.

### Diapositiva 6 · Por qué una IA (2:10 – 2:58)

> ¿Por qué una IA? ESMA advierte de que con sistemas automatizados el riesgo de que el cliente se sobrevalore es mayor. Idóneo es el contrapeso.
>
> La voz, para que Carmen conteste hablando. Claude, que extrae cada dato y marca las contradicciones. Y código, que calcula los números, porque el modelo nunca calcula un número.
>
> Lo que hemos medido: el extractor acertó 31 de 31 datos en siete entrevistas; con Carmen, 10 de 10, y detectó la contradicción; y el asistente responde en 1,8 segundos de mediana, en la prueba por escrito. Con un límite que decimos claro: clientes simulados, una repetición y casos escritos por nosotros.

### Diapositiva 7 · Entra en los agentes que ya tenéis (2:58 – 3:28)

> Y esto entra en los agentes que ya tenéis. GPTadvisor protege lo que su agente responde; Idóneo protege lo que su agente recibe.
>
> Se conecta por MCP, el estándar de los agentes de IA: el agente pide las restricciones de Carmen y recibe riesgo máximo tres y la renta variable como no conveniente.
>
> Nosotros no recomendamos: recomienda el agente de la entidad, y valida una persona.

### Diapositiva 8 · Cierre y salto a la demo (3:28 – 3:45)

> Un límite claro: los datos de Carmen son simulados y el perfil queda en borrador hasta que una persona lo valida.
>
> GPTadvisor hace fiable la recomendación. **Idóneo hace fiable el perfil sobre el que se recomienda.** Vamos a verlo.

### Demo en vivo (3:45 – 6:00)

Pasos exactos, pantallas y plan B en [`DEMO_GUION.md`](DEMO_GUION.md). Esto es lo que se **dice**:

> Esto es Idóneo en directo. A la izquierda, lo que vive Carmen. A la derecha, lo que recibe la entidad. Los datos son simulados.
>
> El asistente avisa de que es una inteligencia artificial y pide permiso. Carmen quiere un dinero extra para complementar la pensión. Mirad la derecha: cada dato aparece con la frase exacta que lo justifica.
>
> Y ahora, el momento clave. Le preguntan si un fondo de renta variable podría perder dinero, y Carmen dice: *«eso no puede pasar, el fondo es del banco»*. Había declarado que conocía ese producto. Salta el aviso: **declarado no es igual a demostrado**. El asistente se lo explica con calma y sigue.
>
> Pasamos a la entidad. Conservador, riesgo máximo 3 sobre 7, renta variable no conveniente. Si pincho en el aviso, veo la frase. Una persona lo valida, y el perfil pasa a activo.
>
> Y por último, el agente. En Claude, con Idóneo y el conector de MyInvestor, pedimos productos para Carmen: solo salen los que respetan su riesgo máximo.
>
> Eso es Idóneo. Gracias, y encantados de responder a vuestras preguntas.

## Versiones por duración

| Versión | Qué se recorta o se añade |
|---|---|
| **5 min** | Saltar la diapositiva 4 (el paso clave ya se ve en la demo) y la demo sin el paso de Claude con MyInvestor (cerrar en la entidad validada) |
| **6 min** | El guion de arriba |
| **7 min** | 15 s más a la diapositiva 4 y, en lugar de la demo guiada, la **entrevista corta por voz** (`carmen-corta`, unos 45 s más): Carmen contesta en directo las dos preguntas que faltan, salta el aviso y se valida. Ver `docs/MODO_ASESOR_DEMO.md` |

## Comprobación de tiempos (habla a 130 palabras/min, ritmo tranquilo)

| Diapositiva | Palabras | Habla | Hueco | Margen |
|---|---:|---:|---:|---:|
| 1 · Portada | 11 | 5 s | 5 s | 0 s |
| 2 · Carmen | 70 | 32 s | 33 s | +1 s |
| 3 · Habla, comprueba, deja pruebas | 57 | 26 s | 30 s | +4 s |
| 4 · Cada dato queda con su prueba | 60 | 28 s | 30 s | +2 s |
| 5 · Lo que recibe la entidad | 67 | 31 s | 32 s | +1 s |
| 6 · Por qué una IA | 101 | 47 s | 48 s | +1 s |
| 7 · Entra en los agentes | 66 | 30 s | 30 s | 0 s |
| 8 · Cierre | 39 | 18 s | 17 s | −1 s |
| **Diapositivas** | **471** | **217 s** | **225 s** | **+8 s** |
| Demo (narración, con esperas) | 179 | 83 s | 135 s | +52 s |

Conteo por palabras: **cronometrarlo en voz alta** en el primer ensayo. Si alguna diapositiva se pasa de su hueco, recortar una frase a esa y no al resto. El margen de la demo es para esperar a la voz y a la red.

## Reparto

| Papel | Quién | Qué hace |
|---|---|---|
| Habla (diapositivas y demo) | `[PENDIENTE: decidir, una o dos personas]` | Cuenta la historia. Mejor una sola voz en las diapositivas |
| Lleva la demo | Rodrigo | Pasa las diapositivas, cambia a la app, lanza la demo y aplica el plan B si algo falla |
| Tiempos | Rodrigo | Cronometra los ensayos y avisa con la mano a los 3:45 y a los 5:30 |
| Preguntas técnicas | Quien lleve los agentes (Alex o Pablo) | Responde IA, medición y MCP (ver `PREGUNTAS_JURADO.md`) |

## Cifras: qué se puede decir y cómo

| Dato | Se puede decir | Cómo decirlo | Fuente |
|---|---|---|---|
| Aciertos del extractor | Sí | «31 de 31 datos en siete entrevistas **simuladas**» | E-04 |
| Carmen de punta a punta | Sí | «10 de 10 y detectó la contradicción, con Carmen **simulada** por Claude» | E-05 |
| Respuesta del asistente | Sí | «1,8 s de **mediana** por respuesta» (sin la voz) | E-05 |
| Voz real | Sí, con cuidado | «La hemos probado de punta a punta» (una vez, 45 turnos) | E-03 |
| Coste por entrevista | Solo si preguntan | «Unos 0,6 $ **estimados** por tokens, no medidos en factura» | E-02 |
| Tiempo frente a un formulario | **No** | No se ha medido | — |
| Pruebas con personas reales | **No** | No se han hecho (solo una del equipo con cifras inventadas) | — |
| Latencia de la voz | **No** | No se ha medido aparte | — |
| Clip de audio por dato | **No** | Pendiente | — |

Límites que **siempre** acompañan a las cifras: clientes simulados, una repetición, casos escritos por el equipo. No es una validación independiente.

## Qué no decir

- «Somos los primeros» o «nadie lo hace»: GPTadvisor y Aveni cubren partes (`gestion/estrategia/ANALISIS_INICIAL.md`).
- «Recomendamos productos»: no. Lo hace el agente de la entidad.
- «Llamamos al MCP de MyInvestor desde nuestro código»: sus términos lo prohíben sin permiso; se usa como conector dentro de Claude.
- Que el perfil «cumple MiFID»: decimos que **recoge y documenta** lo que MiFID exige, y que una persona lo valida.
- Los porcentajes de «confianza» que se ven en la app: son supuestos del equipo, no una medida (rúbrica v2 de `backend/app/agentes/`).

## Diapositivas (8, sin anexos)

**Regla: solo el texto necesario.** Cada diapositiva lleva su mensaje (título), la imagen y los rótulos justos para entenderla. Nada de pies, números ni párrafos. El detalle se dice en voz alta (está en las notas del orador).

| # | Título o mensaje | Lo que se ve | Qué demuestra |
|---|---|---|---|
| 1 | Idóneo · «Tu perfil inversor, en una conversación.» | Esfera 3D y una línea: qué es | Identidad |
| 2 | El test se fía de lo que el cliente declara | Quién es Carmen; test con «Los conozco bien» marcado ≠ la pregunta que le hacen y su respuesta; conclusión abajo | El problema (innovación) |
| 3 | Idóneo cambia el test por una conversación | Habla · Comprueba · Deja pruebas, cada una con su icono y una línea; móvil con la demo guiada real | La solución y la UX |
| 4 | Cada dato queda con su prueba | Frase de Carmen → Claude lo extrae → «declaró Alto, demostró Ninguno», aviso y minuto 0:57 | Cómo funciona (implementación) |
| 5 | Lo que recibe la entidad | Captura real + Conservador (3 de 7), renta variable no conveniente, lo valida una persona | Resultado calculado y validado |
| 6 | ESMA avisa: el cliente tiende a sobrevalorarse | «Por eso Idóneo comprueba»: Voz · Claude · Código; «Lo que hemos medido»: 31/31, 10/10 y 1,8 s; «clientes simulados» | IA de frontera (15 %), con su límite |
| 7 | Se conecta a los agentes de IA de las entidades | Cliente → Idóneo → Agente → Propuesta, «por MCP» y qué es MCP en una línea | Valor y viabilidad |
| 8 | Idóneo hace fiable el perfil sobre el que se recomienda | Esfera y botón «Demo en vivo · datos simulados» | Cierre y paso a la demo |

Estilo: el mismo que la web (fondo casi negro, brillos azul-violeta-rosa, tarjetas de vidrio, esfera 3D). Sin logos de terceros.

## Fuentes que sostienen lo que decimos

| Afirmación | Fuente en el repo |
|---|---|
| El test depende de lo declarado; hay que comprobar | `docs/DISENO.md` (Marco legal MiFID) |
| Aviso de ESMA sobre sistemas automatizados | `gestion/comunicacion/REVISION_NORMATIVA.md` (párr. 52) |
| Solo perfiles, no recomienda | `docs/proyecto/02_AUDITORIA_Y_DECISIONES.md` (D1) |
| Idoneidad y conveniencia | misma auditoría (D2) y `docs/CONTRATOS.md` |
| Los números salen de Python | `backend/app/perfil/calculos.py` |
| Lo que devuelve el MCP | `backend/app/mcp/servidor.py` (`get_investment_constraints`) |
| Cifras medidas | `gestion/evaluacion/PLAN_Y_EVIDENCIAS.md` (E-02 a E-05) |
| MyInvestor solo como conector en Claude | auditoría (D7) y `docs/proyecto/05_MCP_MYINVESTOR.md` |
| Competencia | `gestion/estrategia/ANALISIS_INICIAL.md` |
