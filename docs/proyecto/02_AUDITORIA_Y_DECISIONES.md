# Auditoría de la idea y decisiones del equipo

8 nov 2026. Resumen de la auditoría hecha sobre el [documento de diseño](01_DISENO.md) y de lo que decidió el equipo después. Donde una decisión contradice el diseño, manda la decisión.

## Decisiones tomadas

| # | Decisión | Quién | Consecuencia |
| --- | --- | --- | --- |
| D1 | **El producto solo crea perfiles.** No recomienda, no filtra catálogos y no genera informes para banqueros ni clientes. | Alex | Lo que se hace con el perfil (asesorar, asignar cartera, avisar) lo hace el agente de la entidad que lo consume. Nos deja fuera de cualquier discusión sobre asesorar sin licencia. |
| D2 | **Cubre idoneidad y conveniencia.** | Alex, tras la auditoría | El perfil devuelve dos resultados: idoneidad (asesoramiento de GPTadvisor y carteras automatizadas de MyInvestor) y conveniencia (compra sin asesoramiento de fondos, ETF y acciones en MyInvestor). |
| D3 | **Somos una funcionalidad para GPTadvisor y MyInvestor, no un producto de venta.** | Alex | La viabilidad económica tiene poco peso. Basta una diapositiva de valor para ellas (ver más abajo), no un modelo de negocio. |
| D4 | **Equipo de 6 y 5 días: no se recorta alcance por tiempo.** | Alex | Se mantiene el alcance completo del diseño. Lo que cambia es el orden: primero la cadena mínima de punta a punta, luego lo demás. |
| D5 | **La demo aún no se toca.** | Alex | El guion del diseño queda como borrador. |
| D6 | **"Idóneo" es un nombre provisional.** | Alex | En la documentación nueva se usa `[NOMBRE]`. El equipo dará el nombre real. |
| D7 | **El MCP de MyInvestor se usa como conector dentro de Claude**, no llamado desde nuestro backend. | Recomendación tras leer sus términos | Sus términos prohíben el acceso programático sin permiso. Se pide permiso al jurado de MyInvestor por si se puede integrar dentro del producto. Ver [05_MCP_MYINVESTOR.md](05_MCP_MYINVESTOR.md). |

## Quién usa el perfil y para qué

| Consumidor | Qué hace con el perfil | Test MiFID |
| --- | --- | --- |
| Agente de GPTadvisor (asesoramiento) | Propone productos que cumplen las restricciones y justifica la recomendación | Idoneidad |
| Carteras automatizadas de MyInvestor (gestión discrecional) | Asigna la cartera según el perfil de riesgo (`search_portfolios` con `profile` y `risk_max`) | Idoneidad |
| Compra sin asesoramiento en MyInvestor | Avisa si un producto no es conveniente (p. ej., Carmen intenta comprar renta variable que dijo conocer pero no demostró) | Conveniencia |
| Cumplimiento de la entidad | Revisa el expediente en una inspección | Registro |

Nosotros no hacemos ninguna de esas acciones: les damos el perfil en el formato que cada uno ya entiende.

## Puntos de la auditoría

### 1. Lo que podía tumbar la idea

- **Idoneidad frente a conveniencia.** El test de idoneidad solo aplica a asesoramiento y gestión de carteras. Casi todo lo que vende MyInvestor sin asesoramiento pasa por el de conveniencia, que el diseño dejaba fuera. **Resuelto con D2.**
- **¿Expone MyInvestor el nivel de riesgo?** **Resuelto: sí.** `search_funds` acepta `max_risk` (SRRI 1–7). Los ETF no tienen SRRI (solo volatilidad) y las carteras usan su propia escala `risk_max` 0–5. Horizonte, liquidez, importe mínimo y exclusiones sectoriales solo se pueden aplicar como filtro posterior sobre la ficha.
- **Términos de uso del MCP de MyInvestor** (descubierto al inspeccionarlo). Prohíben acceso programático, extracción masiva y productos derivados sin permiso. **Mitigado con D7.**
- **Modelo de negocio.** La rúbrica dice "viable financieramente". **Rebajado con D3**, pero no se deja en blanco (ver "Valor para las dos empresas").

### 2. Orden de construcción (no recorte)

Primero la cadena imprescindible de punta a punta en el móvil:

voz → extractor → verificador → perfil con pruebas → validación del asesor → MCP → consumo desde el agente de la entidad (con MyInvestor como ejemplo).

Después, sin poner en riesgo la demo: onboarding ampliado completo, PWA instalable, retomar la entrevista tras una llamada, entrada por WhatsApp y reevaluación por eventos vitales.

Simplificación técnica sugerida (pendiente de decidir): SQLite en vez de Postgres, con las versiones del perfil como tabla de solo añadir.

### 3. Riesgos técnicos con ElevenLabs

Revisado en su documentación; **sin probar todavía**.

- **Transcripción en directo:** el SDK de navegador (`@elevenlabs/client`) emite eventos `user_transcript` y `agent_response`. El front reenvía cada frase al backend y el panel se actualiza por SSE.
- **Clip de audio de cada prueba:** esos eventos no traen marcas de tiempo del audio. Lo más fiable es descargar al acabar el audio y la transcripción de la conversación (la API trae los segundos por turno) y recortar los clips. Grabar el micro en paralelo con MediaRecorder puede chocar con el SDK en Safari de iPhone.
- **Claude como modelo del agente:** ElevenLabs ofrece Claude, pero se factura en ElevenLabs y no consume nuestros créditos de Claude. La alternativa "Custom LLM" pide un endpoint compatible con OpenAI; la capa de compatibilidad de Anthropic podría valer, pero hay que probarlo y medir la latencia.
- **Demo en directo:** ruido del pabellón, así que auriculares con micro, hotspot propio y HTTPS (sin HTTPS el móvil no da acceso al micro). Revisar los minutos del plan Creator.

### 4. Historia de la demo (para cuando se toque)

- En el guion actual el agente acaba recomendando. Hay que dejar claro que es **el agente de la entidad**, no nosotros.
- El clímax correcto para Carmen es que **se descarte la renta variable que dijo conocer**, no un carrusel de fondos. Para MyInvestor, la cartera asignada (idoneidad) o el aviso de no conveniencia son más defendibles que una lista de fondos.
- Si el verificador se equivoca al rebajar el conocimiento de alguien, el asesor valida y corrige. La `confidence` no puede salir del modelo: sale de una rúbrica determinista.
- **Impacto medible** (lo pide el criterio de IA): tiempo frente al test en formulario, contradicciones detectadas en 3–5 pruebas con personas reales.

### 5. Legal

Los artículos citados en el diseño son correctos (25.2 y 25.6 MiFID II; 54, 54.12 y 55 del Reg. Delegado 2017/565; Reg. 2021/1253; Ley 6/2023; ESMA35-43-3172). Matices:

- **RGPD:** la base legal de la capa MiFID es la obligación legal (art. 6.1.c). El consentimiento solo para la capa personal.
- **Ley de IA:** el art. 50 aplica desde agosto de 2026, así que el aviso de IA es obligatorio. El perfilado para invertir **no** está entre los usos de alto riesgo del Anexo III (que recoge solvencia crediticia y seguros de vida y salud). No inferir emociones de la voz.
- **Registro:** para el expediente, arts. 72–73 del Reg. 2017/565 y art. 25.5 MiFID II. El art. 76 trata de comunicaciones sobre órdenes.

Estos matices son de una revisión hecha con IA, no de un abogado: conviene contrastarlos con el texto oficial antes del pitch.

## Valor para las dos empresas (diapositiva de viabilidad)

Como funcionalidad, no como producto de venta:

- **Coste por onboarding:** minutos de voz más tokens. Estimación sin medir: probablemente menos de 1 € por entrevista. **Hay que medirlo.**
- **Ahorro frente a la alternativa:** una entrevista con un asesor humano, o el riesgo de sanción de la CNMV por un perfil mal hecho.
- **Lo que gana MyInvestor:** más gente que pasa del chat a la contratación con el perfil ya hecho, y cobertura de conveniencia en el canal sin asesoramiento.
- **Lo que gana GPTadvisor:** su agente ya protege lo que responde; ahora también recibe un perfil fiable y auditable.

Pregunta abierta: ¿GPTadvisor ya hace perfilado del cliente dentro de su producto? Hay que tener la respuesta preparada.

## Preguntas que siguen abiertas

1. ¿Cuánto dura el pitch con preguntas? ¿Los 3 minutos de demo son todo el tiempo?
2. ¿Demo en directo o en vídeo? Lo que se enseñe tiene que ser la versión entregada.
3. ¿Solo español? Varios idiomas suman accesibilidad y encajan con ElevenLabs.
4. ¿Alguien ha probado ya el SDK de ElevenLabs en un móvil?
5. Pedir permiso al jurado de MyInvestor para llamar a su MCP desde código.
6. Nombre definitivo del producto.
