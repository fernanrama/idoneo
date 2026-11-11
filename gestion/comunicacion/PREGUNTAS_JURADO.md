# Preguntas del jurado y respuestas

v2 · 10 nov 2026 · Responsable: Rodrigo · Revisión: equipo

> **Cambios de la v2:** voz probada, extractor funcionando, cifras medidas (con sus límites), rúbrica de confianza v2, MCP probado por túnel. Cifras en `gestion/evaluacion/PLAN_Y_EVIDENCIAS.md` (E-02 a E-05).

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
- **Prueba:** `docs/diseno/02-auditoria-y-decisiones.md` (D1 y D3) y `gestion/estrategia/ANALISIS_INICIAL.md`.
- **Límite:** **no decir «somos los primeros» ni «nadie lo hace»**. GPTadvisor anuncia memoria de clientes y Aveni analiza comprensión: hay solapamientos parciales.

### 3. ¿Es viable económicamente? ¿Quién paga?
- **Respuesta:** Lo planteamos como funcionalidad para GPTadvisor y MyInvestor, no como producto de venta. El valor está en un perfil ya hecho y auditable.
- **Prueba:** diapositiva 6.
- **Si preguntan por el coste:** «unos **0,6 $ por entrevista estimados** con los tokens del laboratorio y precios estándar de Sonnet». (E-02)
- **Límite:** es una **estimación**, no la factura, y no incluye los minutos de voz de ElevenLabs.

### 4. ¿Por qué no un formulario mejor o un asesor humano?
- **Respuesta:** Un formulario recoge lo declarado; Idóneo comprueba y deja evidencia. Un asesor humano es caro para cada alta, y aquí el asesor **valida** el perfil en vez de construirlo desde cero.
- **Límite:** no afirmar ahorros concretos sin medirlos.

### 5. ¿Cumple MiFID? ¿Es legal?
- **Respuesta:** Ayuda a **recoger y documentar** la evaluación que exige MiFID II (art. 25.2 para la idoneidad y 25.3 para la conveniencia), y el Reglamento Delegado 2017/565 (art. 54.7) obliga a asegurar que la información del cliente sea fiable, y las directrices de ESMA de 2023 piden contrastar la autoevaluación con criterios objetivos. La responsabilidad sigue siendo de la entidad y un asesor valida el perfil.
- **Prueba:** `REVISION_NORMATIVA.md`, filas 1, 2 y 6.
- **Límite:** **no decir «cumple MiFID»**. Los umbrales de riesgo son supuestos del equipo, pendientes de revisión por una persona del sector.

### 6. ¿Qué haríais con los datos personales y la grabación de voz?
- **Respuesta:** Separamos dos capas: la MiFID (necesaria para la evaluación) y la personal (opcional, con consentimiento aparte, borrable). La voz no se usa para identificar a la persona. Antes de empezar, el cliente marca dos casillas: que sabe que habla con una IA y que acepta que se guarde la conversación.
- **Estado:** la memoria personal, separada y con su propio consentimiento, ya está en `main` (PR 21, unida el 10/11).
- **Prueba:** `docs/diseno/01-diseno.md` (capas) y RGPD arts. 6.1 y 9.
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
- **Prueba medida:** con Carmen simulada por Claude, 10 de 10 datos y la contradicción detectada (E-05). En la primera entrevista por voz real, la alerta saltó con la frase «un fondo del banco no puede bajar» (E-03).
- **Límite:** la demo del pitch es una **ejecución guiada** (repite una conversación de ejemplo). La voz real funciona, pero se ha probado de punta a punta **una vez**.

### 9. ¿Y si el modelo se equivoca o inventa?
- **Respuesta:** El modelo **propone** y el código **decide**. Riesgo máximo, capacidad de pérdida y conveniencia salen de funciones deterministas. La confianza sale de una rúbrica fija en código, no de la opinión del modelo; por debajo de 0,65 el dato se marca para revisar y el asistente repregunta. Y el perfil queda en borrador hasta que una persona lo valida.
- **Prueba:** `backend/app/perfil/calculos.py`, `backend/app/agentes/rubrica.py` (v2) y `docs/contratos.md`. En E-04 el extractor no dio ningún dato erróneo ni prohibido en 31.
- **Límite:** los pesos de la rúbrica son **supuestos del equipo**, no están calibrados con datos reales.

### 10. ¿Cómo medís el impacto?
- **Respuesta:** Hemos medido la calidad técnica: el extractor acierta **31 de 31** datos en 7 entrevistas simuladas, sin errores (E-04); con Carmen simulada, **10 de 10** y la contradicción detectada (E-05); el asistente responde en **1,8 s de mediana** (E-05).
- **Límite:** clientes **simulados** (por Claude o escritos por el equipo), **una repetición**, y el equipo ajusta los prompts con esos mismos casos (riesgo de sobreajuste). **No** hemos medido el tiempo frente a un formulario ni probado con personas reales: es el siguiente paso.

### 11. ¿Por qué ElevenLabs y Claude? ¿Y la latencia y el coste?
- **Respuesta:** ElevenLabs para la voz (con Claude Haiku como modelo del agente de voz, por rapidez) y Claude para extraer (Sonnet, esfuerzo bajo) y verificar. Los modelos se cambian por variable de entorno.
- **Prueba:** `.env.example` (`MODEL_EXTRACTOR`, `MODEL_VERIFICADOR`, `MODEL_ENTREVISTADOR`). Extractor: mediana 1,7 s y p95 2,7 s por llamada (E-04); va en segundo plano, no hace esperar al cliente.
- **Límite:** la latencia de la voz no se ha medido aparte; coste solo **estimado** (≈ 0,6 $ por entrevista, E-02).

---

## C. UX y accesibilidad (15 %)

### 12. ¿Es accesible para una persona mayor?
- **Respuesta:** Está pensada primero para móvil, con un botón grande, subtítulos de lo que se dice y la posibilidad de contestar por escrito.
- **Prueba:** la demo y `frontend/README.md`.
- **Límite:** no hemos probado con personas mayores reales. El botón de tamaño de letra se quitó en el rediseño (PR 23); la letra base es grande (17 px).

### 13. ¿Qué pasa si falla el micrófono o la red?
- **Respuesta:** El cliente puede responder por escrito dentro de la misma sesión, y para la demo tenemos una ejecución guiada y un vídeo de respaldo.
- **Límite:** el modo texto necesita la clave de Claude en el servidor; sin ella devuelve error (y hoy la pantalla no lo explica bien: fallo avisado al equipo).

---

## D. Implementación (30 %)

### 14. ¿Qué funciona hoy y qué es simulado?
- **Respuesta (honesta):** Funciona la entrevista por voz o por texto, el extractor que rellena el perfil en directo, el verificador que marca «declarado ≠ demostrado», el cálculo del riesgo y la conveniencia, la vista de la entidad con validación humana y un servidor MCP con 4 herramientas. Los datos de Carmen son simulados y la demo del pitch es una ejecución guiada. Falta: clip de audio por dato y pruebas con personas reales.
- **Prueba:** `backend/` (346 tests pasan, 26 omitidos, en el equipo de Rodrigo el 10/11) y la demo.
- **Límite:** actualizar esta respuesta con el estado real del miércoles a las 18:00.

### 15. ¿Se puede ejecutar y probar?
- **Respuesta:** Sí: README con instalación, configuración, ejecución y pruebas, y `pytest` en `backend/`.
- **Límite:** que el ZIP descargado de GitHub arranca en una carpeta limpia lo comprueba Alejandro el martes. No afirmarlo antes.

### 16. ¿Cómo se integra con MyInvestor? ¿Usáis su MCP?
- **Respuesta:** Idóneo publica su propio servidor MCP con 4 herramientas (perfil, restricciones, evidencia y contexto). El agente de la entidad usa esas restricciones sobre el catálogo de MyInvestor. El MCP público de MyInvestor se usa como **conector dentro de Claude**.
- **Prueba:** el 9/11 Claude leyó el perfil activo de Carmen por nuestro MCP a través de un túnel temporal.
- **Límite:** **sus términos prohíben el acceso programático sin permiso**: no decir que lo llamamos desde nuestro código. No hay URL pública fija: el túnel se levanta desde un portátil para la demo. Desde la PR 21 el MCP exige credencial; la conexión de Claude.ai con la autenticación nueva está en revisión.

### 17. ¿Por qué Idóneo no recomienda productos?
- **Respuesta:** Es una decisión de diseño (D1): recomendar es asesorar, y eso lo hace el agente de la entidad, con su licencia y sus controles. Nosotros garantizamos que el agente sabe quién es el cliente.

---

## E. Visión y siguientes pasos

### 18. ¿Qué haríais con más tiempo?
- **Respuesta:** (1) pruebas con personas reales y clips de audio por dato; (2) microentrevistas cortas que mantengan el perfil actualizado cuando cambie la vida del cliente, algo que el art. 54.7 pide en relaciones continuas; (3) que las entidades usen los perfiles para saber qué clientes encajan con un producto nuevo (solo como idea, no está construida).
- **Límite:** presentar (3) **siempre como idea futura**, salvo que exista el miércoles.

---

## Preguntas trampa (cuidado)

| Pregunta | Respuesta honesta |
|---|---|
| «¿Esto lo habéis medido con clientes reales?» | «No. Las cifras son con clientes simulados; las pruebas con personas reales son el siguiente paso.» |
| «¿La demo es en directo?» | «Es una ejecución guiada con una conversación de ejemplo. La voz real funciona y la hemos probado de punta a punta; no la usamos aquí para no depender de la red.» |
| «¿El perfil se rellena solo mientras hablan?» | «Sí: Claude extrae cada dato con su frase mientras habla, y el código decide si lo acepta.» |
| «¿Cuánto cuesta cada entrevista?» | «Unos 0,6 $ estimados por tokens; no es la factura y falta sumar la voz.» |
| «¿Qué son los porcentajes junto a cada dato?» | «La confianza, de una rúbrica fija en código con supuestos nuestros. No es una medida; por debajo de 0,65 se revisa.» |
| «¿Por qué desaparece el aviso al validar?» | «Al validar, la persona da el aviso por revisado; queda registrado quién lo hizo y cuándo.» (Intencionado: `backend/app/perfil/store.py`.) |
| «¿Vuestro sistema es el que cumple MiFID?» | «Ayuda a documentarlo; la responsabilidad es de la entidad y valida una persona.» |
| «¿Podéis acceder al MCP de MyInvestor desde vuestro backend?» | «Solo como conector en Claude; sus términos no permiten otra cosa sin permiso.» |

## Reparto sugerido de respuestas (si presentan varios)

| Tema | Quién responde |
|---|---|
| Problema, valor, normativa, límites | Quien presente (Rodrigo apoya con este documento) |
| Voz, móvil, accesibilidad | Quien lleve el frontend y la voz |
| Agentes, medición, cálculo | Quien lleve los agentes |
| MCP, integración, despliegue | Quien lleve la integración |
