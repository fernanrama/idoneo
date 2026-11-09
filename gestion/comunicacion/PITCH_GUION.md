# Guion del pitch — 6 minutos (diapositivas, luego demo)

Borrador v2 · 9 nov 2026 · Responsable: Rodrigo · Revisión: equipo
Presentación que lo acompaña: [`Idoneo_presentacion.pptx`](Idoneo_presentacion.pptx) (las notas del orador llevan este mismo texto). Se genera con [`fuente-presentacion/`](fuente-presentacion/README.md): versión de trabajo (con etiquetas ámbar) o `--final`.

> **Estado.** Duración oficial: **5-7 minutos** por grupo, minutos exactos por avisar (fuente: `[MEW26] Horas de presentaciones`, no incluido en el repo). Pitch el **jueves 12/11, Tanda 1 (10:30-12:00)**, aula 4.2.E02. Este guion dura 6 min y se recorta a 5 o se amplía a 7.
> **Orden.** Primero **3:24 de diapositivas** y después **salto directo a la demo en vivo (2:30)**. La demo es lo último que ve el jurado.
> **Nombre.** "Idóneo" es provisional (Alex usa `[NOMBRE]`). Decidir antes de congelar, y si se pone nombre de equipo en la portada.
> **Marcas.** `[PENDIENTE: …]` = dato o función que aún no existe o no está medido. **No se dice en voz alta como hecho.** Si el miércoles sigue pendiente, la versión `--final` de la presentación reescribe esa frase como «siguiente paso» y quita la etiqueta ámbar; aquí se quita la frase.

## Una frase para todo el pitch

> *El test MiFID se basa en lo que el cliente dice de sí mismo. Idóneo lo convierte en una conversación que comprueba y deja pruebas.*

## Guion hablado

### Diapositiva 1 · Portada (0:00 – 0:05)

> Buenos días. Esto es Idóneo. `[PENDIENTE: nombre definitivo y presentación del equipo]`

### Diapositiva 2 · Carmen: lo que marcó y lo que dijo (0:05 – 0:38)

> Imaginad a Carmen. Tiene 68 años y 80.000 euros en depósitos. En el test MiFID de su banco marcó que conoce bien los fondos de renta variable.
>
> Pero cuando le preguntan qué pasaría si su fondo baja, dice: *«eso no puede pasar, el fondo es del banco»*. Marcó una cosa y demostró la contraria.
>
> Y el test, que se basa en lo que ella declara, no lo detecta.
>
> *(Carmen es un caso simulado.)*

### Diapositiva 3 · Habla, comprueba y deja pruebas (0:38 – 1:08)

> Idóneo cambia el test por una conversación.
>
> Habla: onboarding por voz, pensado primero para el móvil `[PENDIENTE: voz probada]`. Comprueba: plantea escenarios y contrasta lo declarado con lo demostrado. Y deja pruebas: cada dato con su cita, su fuente y su versión `[PENDIENTE: y su clip de audio]`.
>
> Nosotros no recomendamos productos: garantizamos que el agente de la entidad sabe quién es Carmen.

### Diapositiva 4 · De la conversación al dato (1:08 – 1:38)

> Así se ve el paso clave. Carmen dice «eso no puede pasar». El sistema lo compara con lo que declaró `[PENDIENTE: extractor con Claude en directo]`: había dicho alto, ha demostrado ninguno.
>
> El dato queda guardado con su fuente, la cita exacta y el minuto en que lo dijo. Y con su tolerancia al riesgo pasa igual: declaró tres sobre cinco, demostró uno.

### Diapositiva 5 · Lo que recibe el agente (1:38 – 2:10)

> Esto es lo que recibe el agente. El riesgo máximo de Carmen es tres sobre siete. Sale de tres criterios y manda el más restrictivo: su tolerancia al riesgo.
>
> Y la conveniencia: la renta variable no es conveniente para ella; los depósitos y la renta fija, sí. Todo se calcula con código, no con el modelo, y lo valida una persona antes de que el perfil sea apto.

### Diapositiva 6 · La IA como contrapeso (2:10 – 2:37)

> ¿Por qué una IA? ESMA advierte de que con sistemas automatizados el riesgo de que el cliente se sobrevalore es mayor. Idóneo es el contrapeso, y tiene tres piezas.
>
> La voz, para que Carmen conteste hablando `[PENDIENTE: voz probada]`. Claude, que comprueba lo que dice `[PENDIENTE: extractor]`. Y código, que calcula los números, porque el modelo nunca calcula un número.
>
> `[PENDIENTE: impacto medido — tiempo frente a un formulario, contradicciones detectadas y latencia (Pablo). Si no se mide, no se dice.]`

### Diapositiva 7 · Entra en vuestros agentes (2:37 – 3:04)

> Y esto encaja en vuestros agentes. GPTadvisor protege lo que su agente responde. Idóneo protege lo que su agente recibe.
>
> Para MyInvestor, un perfil ya hecho y auditable, y la conveniencia para quien compra sin asesoramiento. Nosotros no recomendamos: recomienda el agente de la entidad, y valida una persona.

### Diapositiva 8 · Cierre y salto a la demo (3:04 – 3:24)

> Seamos claros con los límites: los datos de Carmen son simulados y el perfil queda en borrador hasta que una persona lo valida.
>
> GPTadvisor hace fiable la recomendación. **Idóneo hace fiable el perfil sobre el que se recomienda.** Vamos a verlo.
>
> `[MÓDULO INTERCAMBIABLE — solo si existe: las entidades usan los perfiles para saber qué clientes encajan con un producto nuevo. Si no existe, se dice como idea futura.]`

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
| **5 min** | Demo a 1:45 (sin el paso del conector de MyInvestor) y saltar la diapositiva 4 (el paso clave ya se ve en la demo) |
| **6 min** | El guion de arriba |
| **7 min** | Dar 15 s más a la diapositiva 4 (el paso clave con calma), 15 s más a la 6 y 30 s más de demo para repreguntas del asistente |

## Comprobación de tiempos (habla a 130 palabras/min, ritmo tranquilo)

| Diapositiva | Palabras | Habla | Hueco | Margen |
|---|---:|---:|---:|---:|
| 1 · Portada | 5 | 2 s | 5 s | +3 s |
| 2 · Carmen | 68 | 31 s | 33 s | +2 s |
| 3 · Habla, comprueba, deja pruebas | 56 | 26 s | 30 s | +4 s |
| 4 · De la conversación al dato | 58 | 27 s | 30 s | +3 s |
| 5 · Lo que recibe el agente | 68 | 31 s | 32 s | +1 s |
| 6 · La IA como contrapeso | 57 | 26 s | 27 s | +1 s |
| 7 · Entra en vuestros agentes | 49 | 23 s | 27 s | +4 s |
| 8 · Cierre | 41 | 19 s | 20 s | +1 s |
| **Diapositivas** | **402** | **185 s** | **204 s** | **+19 s** |
| Demo (narración, con clips y esperas) | 219 | 101 s | 150 s | +49 s |

Es una estimación por conteo de palabras. **Hay que cronometrarlo leyendo en voz alta** en el primer ensayo. Si al ensayar alguna diapositiva se pasa de su hueco, recortar una frase a esa y no al resto.

## Reparto por bloques (propuesta, por si presentan varios)

| Bloque | Quién encaja | Por qué |
|---|---|---|
| Diapositivas 1-3, 5, 7-8 | Rodrigo | Historia, valor, límites y cierre |
| Demo en vivo | Quien lleve el móvil y la voz | Es quien sabe qué pasa si falla |
| Diapositivas 4 y 6 | Quien lleve los agentes (Hammad o Pablo) | Defiende IA y medición |
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

## Diapositivas (8, sin anexos)

| # | Título | Visual | Qué demuestra |
|---|---|---|---|
| 1 | Idóneo | Portada oscura con ondas de voz | Identidad |
| 2 | Carmen: lo que marcó / lo que dijo | Pantalla partida: casilla marcada ≠ cita sobre ondas | El problema (innovación) |
| 3 | Habla, comprueba y deja pruebas | Tres palabras grandes + móvil con la captura real | La solución y la UX |
| 4 | De la conversación al dato | Burbujas de chat → tarjeta del dato: declarado Alto → demostrado Ninguno, con cita y minuto | Cómo funciona (implementación) |
| 5 | Lo que recibe el agente | Escala de riesgo 1-7 con la marca en el 3, tres criterios y semáforo de conveniencia | Resultado calculado y validado |
| 6 | La IA como contrapeso | Aviso de ESMA (párr. 52) + tres roles: Voz, Claude y Código | IA de frontera (15 %) |
| 7 | Entra en vuestros agentes | Cauce Cliente → Idóneo → Agente → Propuesta con tramos protegidos | Valor y viabilidad |
| 8 | Idóneo hace fiable el perfil | Frase de cierre sobre ondas y «demo en vivo» | Cierre y paso a la demo |

Colores: los del tema de la app (azul `#0b2a4a`, verde `#12a37f`), para que pitch y demo parezcan un solo producto. Transición suave (fundido) entre diapositivas. No hay anexos: lo que ve la entidad se enseña en la demo, y los temas de normativa, competencia y datos van en `PREGUNTAS_JURADO.md`.

Los valores de «confianza» del perfil **no salen en pantalla**: son de ejemplo (la rúbrica aún no está implementada).

## Fuentes que sostienen lo que decimos

| Afirmación | Fuente en el repo |
|---|---|
| El test depende de lo declarado; hay que comprobar | `docs/DISENO.md` (Marco legal MiFID) |
| Solo perfiles, no recomienda | `docs/proyecto/02_AUDITORIA_Y_DECISIONES.md` (D1) |
| Idoneidad y conveniencia | misma auditoría (D2) y `docs/CONTRATOS.md` |
| Los números salen de Python | `backend/app/perfil/calculos.py` |
| MyInvestor solo como conector en Claude | auditoría (D7) y `docs/proyecto/05_MCP_MYINVESTOR.md` |
| Competencia | `gestion/estrategia/ANALISIS_INICIAL.md` |
