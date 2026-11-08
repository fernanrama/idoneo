# Guion del pitch — 6 minutos (diapositivas, luego demo)

Borrador v1 · 8 nov 2026 · Responsable: Rodrigo · Revisión: equipo
Presentación que lo acompaña: [`Idoneo_presentacion.pptx`](Idoneo_presentacion.pptx) (las notas del orador llevan este mismo texto).

> **Estado.** Duración oficial: **5-7 minutos** por grupo, minutos exactos por avisar (fuente: `[MEW26] Horas de presentaciones`, no incluido en el repo). Pitch el **jueves 12/11, Tanda 1 (10:30-12:00)**, aula 4.2.E02. Este guion dura 6 min y se recorta a 5 o se amplía a 7.
> **Orden.** Primero **3:25 de diapositivas** y después **salto directo a la demo en vivo (2:30)**. La demo es lo último que ve el jurado.
> **Nombre.** "Idóneo" es provisional (Alex usa `[NOMBRE]`). Decidir antes de congelar, y si se pone nombre de equipo en la portada.
> **Marcas.** `[PENDIENTE: …]` = dato o función que aún no existe o no está medido. **No se dice en voz alta como hecho.** Si el miércoles sigue pendiente, se quita la frase y la marca amarilla de la diapositiva.

## Una frase para todo el pitch

> *El test MiFID se basa en lo que el cliente dice de sí mismo. Idóneo lo convierte en una conversación que comprueba y deja pruebas.*

## Guion hablado

### Diapositiva 1 · Portada (0:00 – 0:05)

> Buenos días. Esto es Idóneo. `[PENDIENTE: nombre y presentación del equipo]`

### Diapositiva 2 · El problema (0:05 – 0:45)

> Imaginad a Carmen. Tiene 68 años y 80.000 euros en depósitos. Quiere invertir una parte para tener un dinero extra cada mes.
>
> Antes de venderle nada, el banco le hace el test MiFID: un formulario de casillas. Carmen marca que conoce los fondos de renta variable. Pero no sabe que un fondo puede perder valor.
>
> El test no lo detecta, porque se basa en lo que ella declara. La normativa europea ya dice que no basta con fiarse de la autoevaluación del cliente. `[VERIFICAR: directrices ESMA 2023]`
>
> *(Carmen es un caso simulado.)*

### Diapositiva 3 · La solución (0:45 – 1:24)

> Idóneo es un onboarding por voz, pensado primero para el móvil.
>
> En vez de casillas, Carmen habla con un asistente que plantea escenarios y comprueba si lo que dice encaja con lo que demuestra. Y construye un perfil donde cada dato lleva su prueba: la cita exacta de la conversación `[PENDIENTE: y su clip de audio]`.
>
> Ese perfil lo leen los agentes de la entidad, como el de GPTadvisor o el de MyInvestor. Nosotros no recomendamos productos: garantizamos que el agente sabe quién es Carmen.

### Diapositiva 4 · Cómo funciona (1:24 – 1:47)

> Son cuatro pasos. Carmen habla desde el móvil. Claude extrae los datos y comprueba las contradicciones `[PENDIENTE: extractor real]`. Todo se guarda en un perfil versionado, con la fuente y la prueba de cada dato. Y los agentes de la entidad lo leen mediante un servidor MCP.

### Diapositiva 5 · IA de frontera, medible (1:47 – 2:17)

> ¿Dónde está la IA de frontera? En tres sitios.
>
> La voz, con ElevenLabs, permite contestar hablando en vez de rellenar cuarenta casillas `[PENDIENTE: voz probada]`.
>
> Claude detecta las contradicciones mientras ella habla.
>
> Y las cifras las calcula Python, no el modelo. Así podemos explicar cada resultado.
>
> ¿Y el impacto? `[PENDIENTE: medir tiempo frente a un formulario, contradicciones detectadas y latencia — Pablo]`

### Diapositiva 6 · Valor y diferencial (2:17 – 2:47)

> ¿Qué gana cada parte?
>
> MyInvestor recibe un perfil ya hecho y auditable, y cubre también la conveniencia para quien compra sin asesoramiento.
>
> GPTadvisor ya protege lo que su agente responde. Con Idóneo también protege lo que su agente recibe.
>
> Y frente a un formulario, dejamos evidencia: la conversación, la versión del perfil y quién lo validó. Coste por entrevista: `[PENDIENTE: medir voz + modelo]`.

### Diapositiva 7 · Límites, cierre y salto a la demo (2:47 – 3:25)

> Seamos claros con los límites. Los datos de Carmen son simulados. Idóneo no recomienda ni sustituye a un asesor: el perfil queda en borrador hasta que una persona lo valida.
>
> Lo siguiente: la voz con clips de audio y microentrevistas que mantengan el perfil vivo.
>
> `[MÓDULO INTERCAMBIABLE — solo si existe: las entidades usan los perfiles para saber qué clientes encajan con un producto nuevo. Si no existe, se dice como idea futura.]`
>
> GPTadvisor hace fiable la recomendación. **Idóneo hace fiable el perfil sobre el que se recomienda.** Vamos a verlo.

### Demo en vivo (3:30 – 6:00; 5 s para pasar a la app)

Los pasos exactos y el plan B están en [`DEMO_GUION.md`](DEMO_GUION.md). La pantalla pasa de la diapositiva 8 a la app. Esto es lo que se **dice** mientras se hace:

> Esto es el móvil de Carmen. Los datos son simulados.
>
> El asistente le avisa de que es una inteligencia artificial y le pide permiso para grabar. Después le pregunta para qué quiere invertir. Carmen quiere un dinerito extra para complementar la pensión. `[PENDIENTE: que el perfil se rellene en directo mientras habla]`
>
> Y ahora llega el momento clave. Le preguntan qué pasaría si su fondo cae un 20 %, y Carmen dice: *«eso no puede pasar, el fondo es del banco»*.
>
> Había declarado que conocía los fondos de renta variable. Acaba de demostrar lo contrario. Salta la alerta: **declarado no es igual a demostrado**. El asistente se lo explica con calma y sigue.
>
> Veamos lo que ve la entidad. El perfil, con la fuente de cada dato. Tolerancia al riesgo: uno de cinco, conservador. La capacidad de pérdida y el plazo salen de funciones de cálculo, no del modelo. Manda el criterio más restrictivo: **riesgo máximo 3 sobre 7**.
>
> Y la conveniencia: renta variable, **no conveniente**. Renta fija y monetarios, sí.
>
> Si pincho en un dato, veo la cita que lo justifica. Una persona de la entidad lo valida y el perfil pasa a activo.
>
> Por último, el agente de la entidad. En Claude, con Idóneo y el conector público de MyInvestor, pedimos productos que encajen con Carmen. `[PENDIENTE: depende del MCP desplegado y del conector]`
>
> Eso es Idóneo. Gracias, y encantados de responder a vuestras preguntas.

## Versiones por duración

| Versión | Qué se recorta o se añade |
|---|---|
| **5 min** | Demo a 1:45 (sin el paso del conector de MyInvestor). Quitar la diapositiva 4 (se cuenta dentro de la 3). Diapositiva 5 en 25 s |
| **6 min** | El guion de arriba |
| **7 min** | Dar 30 s más a la diapositiva 4 contando la arquitectura con más detalle y dejar 30 s más de demo para repreguntas del asistente |

## Comprobación de tiempos (habla a 130 palabras/min, ritmo tranquilo)

| Diapositiva | Palabras | Habla | Hueco | Margen |
|---|---:|---:|---:|---:|
| 1 · Portada | 5 | 2 s | 5 s | +3 s |
| 2 · Problema | 83 | 38 s | 40 s | +2 s |
| 3 · Solución | 80 | 37 s | 39 s | +2 s |
| 4 · Cómo funciona | 45 | 21 s | 23 s | +2 s |
| 5 · IA de frontera | 47 | 22 s | 30 s | +8 s (aquí entran las métricas medidas) |
| 6 · Valor y diferencial | 60 | 28 s | 30 s | +2 s |
| 7 · Límites y cierre | 63 | 29 s | 38 s | +9 s |
| **Diapositivas** | **383** | **177 s** | **205 s** | **+28 s** |
| Demo (narración, con clips y esperas) | 219 | 101 s | 150 s | +49 s |

Es una estimación por conteo de palabras. **Hay que cronometrarlo leyendo en voz alta** en el primer ensayo. Los márgenes de las diapositivas 2, 3, 4 y 6 son de 2 segundos: si al ensayar se pasan, recortar una frase a cada una.

## Reparto por bloques (propuesta, por si presentan varios)

| Bloque | Quién encaja | Por qué |
|---|---|---|
| Diapositivas 1-3, 6-7 | Rodrigo | Historia, valor, límites y cierre |
| Demo en vivo | Quien lleve el móvil y la voz | Es quien sabe qué pasa si falla |
| Diapositivas 4-5 | Quien lleve los agentes (Hammad o Pablo) | Defiende IA y medición |
La organización no ha dicho cuántas personas presentan. Pendiente de acordar con el equipo.

## Cifras y funciones que NO se pueden decir todavía

| Dato | Quién lo mide o lo termina | Estado |
|---|---|---|
| Tiempo medio de entrevista frente a un formulario | Pablo | Pendiente |
| Contradicciones detectadas en personas reales (3-5 pruebas) | Pablo | Pendiente |
| Latencia de respuesta de la voz | Rodrigo | Pendiente (la voz no se ha probado) |
| Coste por entrevista (voz + modelo) | Pablo | Pendiente |
| Aciertos del extractor por campo | Hammad/Pablo | Pendiente (el extractor es un stub) |
| Clip de audio por dato | Juan y Rodrigo | Pendiente |
| Conector Claude + MyInvestor en la demo | Alejandro | Pendiente (falta URL pública) |

## Qué no decir

- "Somos los primeros" o "nadie lo hace": GPTadvisor y Aveni cubren partes (`gestion/estrategia/ANALISIS_INICIAL.md`).
- "Recomendamos productos": no. Lo hace el agente de la entidad.
- "Llamamos al MCP de MyInvestor desde nuestro código": sus términos lo prohíben sin permiso; se usa como conector dentro de Claude.
- Cualquier cifra de la tabla de arriba, hasta que esté medida.
- Que el perfil "cumple MiFID": decimos que **recoge y documenta** lo que MiFID exige, y que un humano lo valida.

## Diapositivas (7, sin anexos)

| # | Título | Una idea | Visual |
|---|---|---|---|
| 1 | Idóneo | Un test MiFID que habla, comprueba y deja pruebas | Portada oscura |
| 2 | El test se fía de lo que dices | Declarado frente a demostrado | Dos tarjetas: lo que marcó, lo que dijo |
| 3 | Habla, comprueba y deja pruebas | Conversación en vez de formulario | Captura de la entrevista en el móvil |
| 4 | Cómo funciona | Voz → Claude → perfil con pruebas → agentes | Diagrama de cuatro cajas |
| 5 | IA de frontera, medible | Voz + Claude + cálculo en Python | Tres columnas y métricas pendientes en amarillo |
| 6 | Valor para las dos entidades | Perfil auditable; protege lo que el agente recibe | Tres tarjetas: MyInvestor, GPTadvisor, frente a un formulario |
| 7 | Idóneo hace fiable el perfil | Frase de cierre y paso a la demo (los límites se dicen de palabra) | Dark, frase grande |

Colores: los del tema de la app (azul `#0b2a4a`, verde `#12a37f`), para que pitch y demo parezcan un solo producto. No hay anexos: la arquitectura va en la diapositiva 4 y lo que ve la entidad se enseña en la demo. Los temas de normativa, competencia y datos van en `PREGUNTAS_JURADO.md`, no en diapositivas.

## Fuentes que sostienen lo que decimos

| Afirmación | Fuente en el repo |
|---|---|
| El test depende de lo declarado; hay que comprobar | `docs/DISENO.md` (Marco legal MiFID) |
| Solo perfiles, no recomienda | `docs/proyecto/02_AUDITORIA_Y_DECISIONES.md` (D1) |
| Idoneidad y conveniencia | misma auditoría (D2) y `docs/CONTRATOS.md` |
| Los números salen de Python | `backend/app/perfil/calculos.py` |
| MyInvestor solo como conector en Claude | auditoría (D7) y `docs/proyecto/05_MCP_MYINVESTOR.md` |
| Competencia | `gestion/estrategia/ANALISIS_INICIAL.md` |
