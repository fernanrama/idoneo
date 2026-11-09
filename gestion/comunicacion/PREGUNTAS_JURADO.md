# Preguntas del jurado y respuestas

9 nov 2026 · Responsable: Rodrigo · Revisión: equipo

> **Formato:** respuesta corta (1-2 frases) → prueba (dónde se ve) → límite (qué NO decir).
> **Regla de oro:** si algo no está medido o no funciona el miércoles, se dice tal cual. Ante la duda: «eso lo hemos diseñado así, pero aún no lo hemos medido».
> Las citas legales están contrastadas en [`REVISION_NORMATIVA.md`](REVISION_NORMATIVA.md). Las marcas `(si está hecho)` se revisan antes del jueves.
> **Rúbrica:** innovación y viabilidad 30 % · IA de frontera 15 % · UX y accesibilidad 15 % · implementación 30 % · presentación 10 %.

---

## A. Problema, innovación y viabilidad (30 %)

### 1. ¿Qué problema real resuelve y quién lo sufre?
- **Respuesta:** El test MiFID se basa en lo que el cliente declara de sí mismo, y el cliente tiende a sobrevalorarse. Idóneo lo convierte en una conversación que contrasta lo declarado con lo demostrado y deja pruebas.
- **Prueba:** el caso de Carmen: declara conocer la renta variable y dice «el fondo es del banco». Declarado ≠ demostrado. Y ESMA advierte (directrices 2023, párr. 52) de que el riesgo de sobrevaloración es **mayor** cuando el cliente da la información a través de un sistema automatizado con poca interacción humana: justo lo que Idóneo compensa comprobando.
- **Límite:** Carmen es un caso **simulado**. No hemos probado con clientes reales (si no se ha hecho).

### 2. ¿En qué se diferencia de lo que ya existe (GPTadvisor y otros)?
- **Respuesta:** GPTadvisor protege lo que su agente **responde**; Idóneo protege lo que su agente **recibe**: un perfil fiable, con prueba de cada dato. Es una pieza que se integra, no un competidor.
- **Prueba:** `docs/proyecto/02_AUDITORIA_Y_DECISIONES.md` (D1 y D3) y `gestion/estrategia/ANALISIS_INICIAL.md`.
- **Límite:** **no decir «somos los primeros» ni «nadie lo hace»**. GPTadvisor anuncia memoria de clientes y Aveni analiza comprensión: hay solapamientos parciales.

### 3. ¿Es viable económicamente? ¿Quién paga?
- **Respuesta:** Lo planteamos como funcionalidad para GPTadvisor y MyInvestor, no como producto de venta. El valor está en un perfil ya hecho y auditable.
- **Prueba:** diapositiva 6.
- **Límite:** **el coste por entrevista no está medido** (voz + modelo). No dar cifras. Si insisten: «lo vamos a medir con minutos de voz y tokens reales; hoy no tenemos el dato».

### 4. ¿Por qué no un formulario mejor o un asesor humano?
- **Respuesta:** Un formulario recoge lo declarado; Idóneo comprueba y deja evidencia. Un asesor humano es caro para cada alta, y aquí el asesor **valida** el perfil en vez de construirlo desde cero.
- **Límite:** no afirmar ahorros concretos sin medirlos.

### 5. ¿Cumple MiFID? ¿Es legal?
- **Respuesta:** Ayuda a **recoger y documentar** la evaluación que exige MiFID II (art. 25.2 para la idoneidad y 25.3 para la conveniencia), y el Reglamento Delegado 2017/565 (art. 54.7) obliga a asegurar que la información del cliente sea fiable, y las directrices de ESMA de 2023 piden contrastar la autoevaluación con criterios objetivos. La responsabilidad sigue siendo de la entidad y un asesor valida el perfil.
- **Prueba:** `REVISION_NORMATIVA.md`, filas 1, 2 y 6.
- **Límite:** **no decir «cumple MiFID»**. Los umbrales de riesgo son supuestos del equipo, pendientes de revisión por una persona del sector.

### 6. ¿Qué haríais con los datos personales y la grabación de voz?
- **Respuesta:** Separamos dos capas: la MiFID (necesaria para la evaluación) y la personal (opcional, con consentimiento aparte, borrable). La voz no se usa para identificar a la persona.
- **Prueba:** `docs/DISENO.md` (capas) y RGPD arts. 6.1 y 9.
- **Límite:** la base jurídica concreta la decide la **entidad** como responsable del tratamiento. **No decir «la ley exige grabar»**: grabar la entrevista es decisión de diseño, con consentimiento.

### 7. ¿Y la Ley de IA?
- **Respuesta:** Avisamos al empezar de que habla con una IA, que es lo que exige el art. 50.1, aplicable desde el 2 de agosto de 2026. Además, no tomamos decisiones automáticas: valida una persona.
- **Prueba:** el aviso es el primer paso de la entrevista. `REVISION_NORMATIVA.md`, filas 13 y 14.
- **Límite:** no hemos resuelto si Idóneo sería «proveedor» o «responsable del despliegue». No es asesoramiento jurídico.

---

## B. IA de frontera (15 %)

### 8. ¿Qué aporta la IA que no haga un formulario?
- **Respuesta:** Tres cosas: la voz permite contestar hablando en vez de rellenar decenas de casillas; Claude plantea escenarios y detecta contradicciones mientras el cliente habla; y las cifras las calcula Python, no el modelo.
- **Prueba:** diapositivas 4 y 5; demo (alerta «declarado ≠ demostrado»).
- **Límite:** **hoy el extractor con Claude está en desarrollo y la voz no está probada** (si sigue así el miércoles, decirlo: «la alerta de la demo parte de una conversación guiada»).

### 9. ¿Y si el modelo se equivoca o inventa?
- **Respuesta:** Por diseño, el modelo no pone ningún número: riesgo máximo, capacidad de pérdida y conveniencia salen de funciones deterministas. La confianza sale de una rúbrica fija, no de la opinión del modelo. Si es baja, el asistente repregunta. Y el perfil queda en borrador hasta que una persona lo valida.
- **Prueba:** `backend/app/perfil/calculos.py` y `docs/CONTRATOS.md`.
- **Límite:** la rúbrica de confianza **no está implementada todavía** (la define el extractor). No decir que está.

### 10. ¿Cómo medís el impacto?
- **Respuesta:** Vamos a medir tres cosas: tiempo frente a un formulario, contradicciones detectadas con personas reales y latencia de la voz.
- **Límite:** **no hay datos todavía**. Si no se miden, decirlo así y no dar cifras. Una muestra pequeña (3-5 personas) no prueba significación general.

### 11. ¿Por qué ElevenLabs y Claude? ¿Y la latencia y el coste?
- **Respuesta:** ElevenLabs para la conversación por voz y Claude para extraer y comprobar. Los modelos se eligen por variable de entorno, para poder cambiar según la latencia.
- **Prueba:** `.env.example` (`MODEL_EXTRACTOR`, `MODEL_VERIFICADOR`).
- **Límite:** latencia y coste **sin medir**.

---

## C. UX y accesibilidad (15 %)

### 12. ¿Es accesible para una persona mayor?
- **Respuesta:** Está pensada primero para móvil, con un botón grande, subtítulos de lo que se dice y la posibilidad de contestar por escrito.
- **Prueba:** la demo y `frontend/README.md`.
- **Límite:** el tamaño de letra ajustable y la voz más lenta están **en curso / pendientes**. No hemos probado con personas mayores reales.

### 13. ¿Qué pasa si falla el micrófono o la red?
- **Respuesta:** El cliente puede responder por escrito dentro de la misma sesión, y para la demo tenemos una ejecución guiada y un vídeo de respaldo.
- **Límite:** el modo texto completo (`/chat`) está pendiente (si no se ha hecho).

---

## D. Implementación (30 %)

### 14. ¿Qué funciona hoy y qué es simulado?
- **Respuesta (honesta):** Funciona la entrevista guiada, el perfil con fuente y prueba por dato, el cálculo del riesgo y la conveniencia, la vista de la entidad con validación humana y un servidor MCP con 4 herramientas. Los datos de Carmen son simulados. Lo siguiente es la voz real con clips de audio y que el extractor rellene el perfil en directo.
- **Prueba:** `backend/` (159 tests pasan en el equipo de Rodrigo el 8/11) y la demo.
- **Límite:** actualizar esta respuesta con el estado real del miércoles a las 18:00.

### 15. ¿Se puede ejecutar y probar?
- **Respuesta:** Sí: README con instalación, configuración, ejecución y pruebas, y `pytest` en `backend/`.
- **Límite:** que el ZIP descargado de GitHub arranca en una carpeta limpia lo comprueba Alejandro el martes. No afirmarlo antes.

### 16. ¿Cómo se integra con MyInvestor? ¿Usáis su MCP?
- **Respuesta:** Idóneo publica su propio servidor MCP con 4 herramientas (perfil, restricciones, evidencia y contexto). El agente de la entidad usa esas restricciones sobre el catálogo de MyInvestor. El MCP público de MyInvestor se usa como **conector dentro de Claude**.
- **Límite:** **sus términos prohíben el acceso programático sin permiso**: no decir que lo llamamos desde nuestro código. La URL pública de nuestro MCP está pendiente (si no se ha hecho).

### 17. ¿Por qué Idóneo no recomienda productos?
- **Respuesta:** Es una decisión de diseño (D1): recomendar es asesorar, y eso lo hace el agente de la entidad, con su licencia y sus controles. Nosotros garantizamos que el agente sabe quién es el cliente.

---

## E. Visión y siguientes pasos

### 18. ¿Qué haríais con más tiempo?
- **Respuesta:** (1) voz real con clips de audio por dato; (2) microentrevistas cortas que mantengan el perfil actualizado cuando cambie la vida del cliente, algo que el art. 54.7 pide en relaciones continuas; (3) que las entidades usen los perfiles para saber qué clientes encajan con un producto nuevo (solo como idea, no está construida).
- **Límite:** presentar (3) **siempre como idea futura**, salvo que exista el miércoles.

---

## Preguntas trampa (cuidado)

| Pregunta | Respuesta honesta |
|---|---|
| «¿Esto lo habéis medido con clientes reales?» | «No. Carmen es un caso simulado; las pruebas con personas reales son el siguiente paso.» |
| «¿La voz funciona ahora mismo?» | Responder con lo que sea cierto el jueves. Si no está probada: «hoy la demo es una ejecución guiada». |
| «¿El perfil se rellena solo mientras hablan?» | Igual: depende de si el extractor está terminado. |
| «¿Cuánto cuesta cada entrevista?» | «No lo hemos medido todavía.» No dar estimaciones como datos. |
| «¿Vuestro sistema es el que cumple MiFID?» | «Ayuda a documentarlo; la responsabilidad es de la entidad y valida una persona.» |
| «¿Podéis acceder al MCP de MyInvestor desde vuestro backend?» | «Solo como conector en Claude; sus términos no permiten otra cosa sin permiso.» |

## Reparto sugerido de respuestas (si presentan varios)

| Tema | Quién responde |
|---|---|
| Problema, valor, normativa, límites | Rodrigo |
| Voz, móvil, accesibilidad | Quien lleve el frontend y la voz |
| Agentes, medición, cálculo | Quien lleve los agentes |
| MCP, integración, despliegue | Quien lleve la integración |
