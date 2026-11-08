# [NOMBRE] · Diseño del producto (Hack Finance)

8 nov 2026 · Alejandro (Alex). Documento de diseño original, copiado tal cual salvo el nombre ("Idóneo" era provisional y se sustituye por `[NOMBRE]`) y unas notas marcadas como **Actualización**. Las decisiones posteriores a este documento están en [02_AUDITORIA_Y_DECISIONES.md](02_AUDITORIA_Y_DECISIONES.md) y prevalecen sobre lo que diga aquí.

## Resumen

[NOMBRE] es un onboarding por voz, pensado primero para móvil, que convierte el test MiFID en un perfil de cliente verificado y con pruebas de audio. Ese perfil se lo damos a los agentes de la entidad, como el de GPTadvisor, que son quienes lo usan para personalizar.

- **Problema:** el test MiFID se basa en lo que el cliente declara de sí mismo, y el cliente se sobrevalora. Además no deja pruebas de qué entendía, no explica las preferencias ESG y es poco accesible para personas mayores.
- **Solución:** un agente de voz que comprueba en vez de preguntar, agentes que rellenan y verifican el perfil en tiempo real, y un registro que enlaza cada dato con el fragmento de audio que lo justifica.
- **Producto:** un perfil estructurado y verificado, servido por MCP y API, más el expediente de idoneidad que exige la norma. No hacemos informes para banqueros ni para clientes: eso depende de si es banca privada o retail, y lo genera el agente de cada entidad a partir del perfil.
- **Móvil primero:** la mayor parte del uso diario está en el móvil, así que la entrevista se diseña para el teléfono y funciona igual en web.
- **Encaje con el jurado:** GPTadvisor protege lo que su agente responde; [NOMBRE] protege lo que su agente recibe. Se conecta con el MCP público de MyInvestor, construido con GPTadvisor, para que la demo acabe con productos reales filtrados según el perfil.
- **Límite que defendemos:** [NOMBRE] no recomienda productos. Recoge información, la evalúa y la deja lista para el agente.

## Marco legal MiFID que cubrimos

[NOMBRE] cubre la recogida y evaluación de idoneidad que exige MiFID II, siguiendo las [directrices de ESMA de 2023](https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf), que la CNMV aplica. Cada fila de esta tabla se convierte en un control del agente verificador y en una línea del informe.

| Requisito | Norma | Cómo lo cumple [NOMBRE] |
| --- | --- | --- |
| Informar al cliente de qué es la evaluación y para qué sirve, en lenguaje claro | Directrices ESMA 2023 | El agente lo explica al empezar y el cliente lo confirma por voz (queda grabado) |
| Conocimientos y experiencia: productos conocidos, operaciones hechas, formación, profesión | Art. 25.2 MiFID II; arts. 54 y 55 Reg. Delegado 2017/565 | Preguntas de comprobación ("¿qué haría si su fondo cae un 20%?"), no casillas; nivel declarado frente a nivel demostrado |
| Situación financiera, incluida la capacidad de soportar pérdidas | Art. 54 Reg. Delegado 2017/565 | Ingresos, gastos fijos, patrimonio, deudas y colchón; cálculo determinista de la pérdida asumible |
| Objetivos: finalidad, plazo y tolerancia al riesgo | Art. 54 Reg. Delegado 2017/565 | Objetivos con importe y fecha; tolerancia medida con escenarios, no con una escala del 1 al 7 |
| Preferencias de sostenibilidad (ESG) | Reg. Delegado 2021/1253 | Explicadas con ejemplos cotidianos; se registra la preferencia o la ausencia de ella |
| No fiarse solo de la autoevaluación; mecanismos contra la sobrevaloración | Directrices ESMA 2023; [comunicado CNMV](https://periscopiofiscalylegal.pwc.es/nuevas-medidas-garantizar-fiabilidad-informacion-obtenida-en-evaluacion-conveniencia-e-idoneidad-clientes-entidades-inversion/amp/) | Agente verificador: marca cada contradicción entre lo declarado y lo demostrado |
| Coherencia de la información del cliente | Directrices ESMA 2023 | Reglas de coherencia (p. ej., objetivo a 1 año frente a inversión de riesgo) + revisión del verificador |
| Sin información suficiente, no se recomienda | Art. 54 Reg. Delegado 2017/565 | El perfil no se marca como "apto para recomendar" hasta cubrir todos los campos obligatorios |
| Informe de idoneidad antes de la operación | Art. 25.6 MiFID II; art. 54.12 Reg. Delegado 2017/565 | [NOMBRE] genera la parte de perfil del informe; la recomendación la añade el asesor o su agente |
| Mantener la información actualizada | Directrices ESMA 2023 | Perfil versionado y reevaluación periódica o cuando cambia la vida del cliente |
| Registro de toda la evaluación | Arts. 72 a 76 Reg. Delegado 2017/565 | Audio, transcripción, perfil y correcciones del asesor, con sello de tiempo |
| Avisar de que es una IA, supervisión humana y responsabilidad de la entidad | [Declaración ESMA sobre IA (2024)](https://cms.law/en/aut/legal-updates/esma-issues-first-formal-guidance-on-use-of-ai-in-retail-financial-services); art. 50 Ley de IA | Aviso al empezar; el asesor valida el perfil antes de usarlo |
| Datos personales y grabación | RGPD | Consentimiento explícito al empezar; la voz no se usa para identificar al cliente |

La norma española que traspone MiFID II es la Ley 6/2023 de los Mercados de Valores y de los Servicios de Inversión. Quedan fuera del MVP el KYC antiblanqueo y la firma del contrato. Antes del pitch hay que revisar los números de artículo con el texto oficial: aquí están citados de memoria.

> **Actualización (8 nov):** el producto cubre también el **test de conveniencia** (compra sin asesoramiento de fondos, ETF y acciones en MyInvestor). Sale casi directo del bloque de conocimientos y experiencia. El perfil da dos resultados: idoneidad y conveniencia. Ver [04_CONTRATO_PERFIL.md](04_CONTRATO_PERFIL.md).
>
> **Actualización (8 nov), matices legales de la auditoría:** la base legal RGPD de la capa MiFID es la obligación legal (art. 6.1.c), no el consentimiento; el consentimiento solo vale para la capa personal. El art. 50 de la Ley de IA aplica desde agosto de 2026 (aviso de IA obligatorio); el perfilado para invertir no está en el Anexo III de alto riesgo. No inferir emociones de la voz. Para el expediente de idoneidad la referencia de registro son los arts. 72–73 del Reg. 2017/565 y el 25.5 MiFID II (el 76 trata de comunicaciones sobre órdenes).

## Onboarding ampliado

Encima de la capa MiFID obligatoria va una capa de personalización opcional, con consentimiento aparte, que es lo que hace que el perfil sirva para algo más que para cumplir. El agente la pregunta de forma natural en la misma conversación y el cliente puede saltarse cualquier bloque.

| Bloque | Qué recoge | Para qué sirve |
| --- | --- | --- |
| Momento vital | Edad, personas a cargo, vivienda (alquiler, hipoteca, plan de compra), eventos próximos (boda, hijo, herencia) | Ordenar los objetivos por plazo y anticipar necesidades de liquidez |
| Estabilidad de ingresos | Asalariado, funcionario o autónomo; ingresos fijos o variables | Ajustar el colchón y la capacidad real de asumir pérdidas |
| Jubilación | Edad objetivo, pensión esperada, planes que ya tiene | Calcular la brecha de jubilación y el esfuerzo mensual |
| Lo que ya tiene fuera | Fondos, depósitos o planes en otras entidades y lo que paga por ellos | Detectar comisiones altas y dinero parado; base para el análisis de "value for money" |
| Contexto fiscal | Residencia fiscal y si conoce los traspasos entre fondos sin tributar | Proponer cambios sin coste fiscal; preparar la conversación con el asesor |
| Comportamiento real | Qué hizo en caídas pasadas (2020, 2022) o qué haría | Contrastar la tolerancia declarada con la real |
| Valores y exclusiones | Sectores que no quiere (armas, tabaco, combustibles fósiles) más allá de la ESG formal | Filtrar productos y personalizar el discurso |
| Cómo quiere que le hablen | Canal (WhatsApp, email, llamada), frecuencia, audio o texto, nivel de detalle, idioma | Que informes y avisos le lleguen como los va a leer |
| Qué le preocupa y qué quiere aprender | Dudas abiertas y temas que no entiende | Personalizar la educación financiera y la primera reunión |

Lo que no preguntamos: salud, ideología, religión ni ningún otro dato sensible que no haga falta para invertir. La capa de personalización se guarda separada de la capa MiFID, para poder borrarla sin tocar el registro regulatorio.

## Experiencia móvil y web

La entrevista se diseña para el móvil, porque ahí está la mayor parte del uso diario, y en web es el mismo flujo con más espacio. La voz encaja de forma natural en el teléfono: hablar 7 minutos es más fácil que rellenar 40 casillas en una pantalla pequeña.

- **Una sola base de código:** web responsive instalable como PWA, para servir móvil y ordenador sin hacer dos apps.
- **Una pantalla, un gesto:** un botón grande para hablar, subtítulos de lo que se dice y una barra con los bloques del perfil que se van completando.
- **Pensado para la vida real:** si entra una llamada o se cierra la app, la entrevista sigue donde se quedó, porque el perfil se guarda bloque a bloque.
- **Voz o texto en cada pregunta:** quien esté en el metro o en la oficina puede contestar escribiendo, sin perder la comprobación de lo que dice.
- **Por partes:** la capa MiFID obligatoria va primero; la de personalización se puede hacer en otro momento.
- **Accesible:** letra grande, subtítulos siempre visibles y opción de que el agente hable más despacio.
- **Se entra desde donde ya está el cliente:** un enlace desde la app de la entidad, WhatsApp o el email abre la entrevista directamente.
- **Rapidez:** el objetivo es que el agente responda en menos de un segundo; la verificación pesada se hace en segundo plano.

En la demo, la entrevista se hace en un móvil real proyectado en pantalla, para que el jurado vea la experiencia tal y como la viviría el cliente.

## Modelo de perfil y memoria

Cada dato del perfil es un objeto con su valor, de dónde sale, cuánta confianza tenemos y el fragmento de audio que lo prueba. Esto es lo que diferencia [NOMBRE] de un formulario, y es la parte de Pablo.

```json
{
  "client_id": "carmen-68",
  "version": 3,
  "status": "validated",
  "mifid": {
    "knowledge.equity_funds": {
      "value": "low",
      "declared": "high",
      "source": "demonstrated",
      "confidence": 0.86,
      "evidence": [{"session": "s-0142", "t": [212.4, 219.8],
        "quote": "eso no puede pasar, el fondo es del banco"}],
      "flags": ["declared_vs_demonstrated"]
    },
    "financial.loss_capacity_eur": {
      "value": 12000, "source": "calculated",
      "inputs": ["income", "fixed_costs", "savings", "debts"]
    },
    "objectives": [{"goal": "complementar pensión", "horizon_years": 10, "priority": 1}],
    "sustainability": {"value": "no_preference", "explained": true}
  },
  "personal": {"communication": {"channel": "whatsapp", "format": "audio"}},
  "review": {"validated_by": "asesor-07", "changes": [], "next_review": "2027-11-08"}
}
```

- **Fuente de cada dato:** `declared` (lo dijo), `demonstrated` (lo probó al responder), `calculated` (sale de una fórmula determinista, nunca del modelo) o `advisor` (lo corrigió el asesor).
- **Estados del perfil:** borrador → validado por el asesor → activo → pendiente de revisión. Solo un perfil activo se expone como "apto para recomendar".
- **Versiones:** nunca se sobrescribe; cada cambio crea una versión nueva con su motivo. Es lo que se enseña en una inspección.
- **Memoria:** sesiones (audio y transcripción), hechos del perfil y eventos que obligan a reevaluar ("me caso en junio", "he heredado"). Un cambio relevante abre una entrevista corta solo sobre lo que ha cambiado.
- **Separación:** la capa MiFID y la personal se guardan aparte, con permisos distintos.

## Salidas del perfil

[NOMBRE] produce dos cosas: el perfil para los agentes y el expediente que exige la norma. Los informes para banqueros o clientes no son parte del producto, porque cambian según sea banca privada o retail: los genera el agente de cada entidad a partir de nuestro perfil.

| Salida | Qué contiene | Cómo se consume |
| --- | --- | --- |
| Perfil para agentes | Perfil en JSON con fuente y confianza de cada dato; restricciones que cualquier recomendación debe cumplir (riesgo máximo, plazo, liquidez, exclusiones); alertas abiertas | Servidor MCP y API REST |
| Contexto para el modelo | Resumen breve del cliente escrito para que lo lea otro agente, no una persona: qué quiere, qué entiende y qué no, cómo prefiere que le hablen | Herramienta MCP |
| Expediente de idoneidad | Audio, transcripción, perfil, versiones y quién lo validó, con sello de tiempo | Exportación JSON o PDF para cumplimiento y auditoría |

Herramientas MCP del MVP:

1. `get_client_profile(client_id)`: el perfil activo, con fuente y confianza de cada dato.
2. `get_investment_constraints(client_id)`: las reglas que cualquier recomendación debe cumplir, listas para usarse como filtros.
3. `get_evidence(client_id, field)`: la cita y el fragmento de audio que justifican un dato.
4. `get_client_context(client_id)`: el resumen para el modelo.

La revisión humana se mantiene, porque la exige la norma: el perfil queda en borrador hasta que alguien de la entidad lo valida. En el MVP eso es una pantalla mínima de validación, no un panel de banquero.

La herramienta 2 es la que une [NOMBRE] con MyInvestor: sus restricciones se traducen directamente en filtros sobre el catálogo (sección siguiente).

## Integración con GPTadvisor y MyInvestor

La integración con MyInvestor es real desde el primer día: tienen un [servidor MCP público](https://mcp.myinvestor.es/) en `https://mcp.myinvestor.es/mcp`, desarrollado con GPTadvisor y sin necesidad de cuenta. Según su [política de privacidad](https://mcp.myinvestor.es/privacy), solo expone datos públicos de productos (nombre, ISIN, TER, patrimonio, rentabilidad histórica) y ningún dato de clientes. Ese hueco es justo el que llena [NOMBRE].

> Diagrama del flujo: ver [diagramas/idea-final-preview.png](diagramas/idea-final-preview.png) (editable en [diagramas/idea-final.excalidraw](diagramas/idea-final.excalidraw)).

Cómo funciona la cadena:

- **[NOMBRE] publica su propio MCP remoto** (URL pública desplegada), con las 4 herramientas de la sección de informes.
- **En Claude se activan los dos conectores.** El agente pide a [NOMBRE] las restricciones de Carmen y las usa como filtros sobre el catálogo de MyInvestor: nivel de riesgo máximo, plazo, liquidez, coste y exclusiones.
- **GPTadvisor encaja igual.** Su agente ya se conecta a fuentes externas por API, MCP o ficheros, así que [NOMBRE] es una fuente más. Con el agente de GPTadvisor la integración es la misma; en la demo, Claude hace de agente.
- **La contratación sigue como hoy:** MyInvestor permite empezarla en el chat y [completarla en su app o web](https://www.fundssociety.com/es/?p=302934), donde el cliente se identifica.

> **Actualización (8 nov):** el MCP de MyInvestor sí expone el riesgo SRRI 1–7 en fondos (`max_risk`), pero sus términos de uso **prohíben llamarlo por programa** desde un backend sin permiso explícito. Su uso como conector dentro de Claude sí está permitido. Detalle en [05_MCP_MYINVESTOR.md](05_MCP_MYINVESTOR.md).

La siguiente fase con ellos, que se cuenta en el pitch como visión y no como algo hecho: que el perfil de [NOMBRE] sustituya al test MiFID del alta de MyInvestor, de modo que quien llega desde un chat ya traiga su perfil verificado.

## Arquitectura de agentes y stack

El perfil versionado es el centro: los agentes solo escriben en él y todas las salidas solo leen de él. Así el panel, el PDF, el audio y el MCP nunca se contradicen.

> Diagrama de arquitectura: ver [diagramas/idea-final-preview.png](diagramas/idea-final-preview.png).

- **Presupuesto:** los 400 $ de API van íntegros a los agentes del producto; el desarrollo no los consume. Eso permite usar modelos buenos donde importa sin miedo a quedarnos cortos.
- **Reparto de modelos:** en la conversación manda la latencia, así que va el modelo más capaz que responda en menos de un segundo (Sonnet, o Haiku si hace falta). Sonnet en el extractor, que trabaja en tiempo real. Opus en el verificador y en el resumen para el modelo, que van en segundo plano.
- **Los números nunca los pone el modelo:** pérdida asumible, horizonte y brecha de jubilación salen de funciones en Python que el extractor llama como herramientas.
- **Voz:** ElevenLabs Agents para la conversación. Hay que confirmar cómo recibimos la transcripción en directo (websocket o webhook), cómo se conecta Claude como modelo del agente y cómo funciona su SDK en el navegador del móvil.
- **Front:** Next.js como PWA, diseñado primero para móvil; la misma app sirve en web.
- **Backend:** FastAPI con Postgres (o Supabase) para perfil, versiones y pruebas; el audio, en almacenamiento de objetos.
- **MCP:** servidor remoto con URL pública y transporte HTTP, para conectarlo en Claude igual que el de MyInvestor.
- **Límite real:** los minutos de voz del plan Creator de ElevenLabs, no el presupuesto de Claude.

## Demo de 3 minutos

> **Actualización (8 nov):** la demo aún no se toca; este guion es el borrador original. Ojo: en el paso 4 el agente acaba recomendando, y el producto **no** recomienda. Hay que presentarlo claramente como el agente de la entidad.

La demo cuenta una historia completa: Carmen habla con [NOMBRE] desde su móvil, el perfil se construye con pruebas y un agente lo usa para buscar productos reales de MyInvestor que lo respetan.

1. **0:00–0:20 · El problema.** "Carmen, 68 años, 80.000 € en depósitos. En el test de su banco marcó que conoce los fondos de renta variable. No sabe que puede perder un 30% en un año."
2. **0:20–1:30 · La entrevista en el móvil.** Un compañero hace de Carmen en un teléfono proyectado. Al lado, el perfil se rellena en tiempo real. Momento clave: Carmen dice "eso no puede pasar, el fondo es del banco" y salta la alerta de declarado frente a demostrado. El agente se lo explica y sigue.
3. **1:30–2:00 · El perfil con pruebas.** El JSON del perfil, con fuente y confianza de cada dato. Se pincha en "conocimiento: bajo" y suena el clip de Carmen. Alguien de la entidad lo valida y pasa a activo.
4. **2:00–2:40 · La conexión.** En Claude, con los conectores de [NOMBRE] y de MyInvestor activos: "Busca en MyInvestor productos que encajen con Carmen". El agente lee sus restricciones de [NOMBRE], filtra el catálogo real de MyInvestor y descarta lo que no encaja.
5. **2:40–3:00 · El cierre.** "El agente de cada entidad decide cómo hablar con Carmen, sea banca privada o retail. Nosotros garantizamos que sabe quién es Carmen." Y la frase final: "GPTadvisor hace fiable la recomendación. [NOMBRE] hace fiable el perfil sobre el que se recomienda."

Plan B obligatorio: un vídeo grabado de la entrevista y un perfil precargado, por si falla la red o el micrófono. La demo debe ser la misma versión que se entrega, como pide el reglamento.

## Fuentes

- [MyInvestor MCP (mcp.myinvestor.es)](https://mcp.myinvestor.es/)
- [Política de privacidad del MCP de MyInvestor](https://mcp.myinvestor.es/privacy)
- [Funds Society: MyInvestor y GPTadvisor en ChatGPT, Claude y Perplexity](https://www.fundssociety.com/es/?p=302934)
- [Merca2: MyInvestor integra su oferta en ChatGPT y Claude](https://www.merca2.es/2026/06/09/myinvestor-ia-inversion-chatgpt-claude-2393312/)
- [GPTadvisor: gestión patrimonial agéntica](https://www.gptadvisor.com/es.html)
- [Directrices de ESMA sobre idoneidad MiFID II (ESMA35-43-3172)](https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf)
- [CMS: directrices de idoneidad de ESMA](https://cms.law/en/hun/legal-updates/esma-issues-guidelines-on-mifid-ii-suitability-requirements)
- [PwC: comunicado de la CNMV sobre la fiabilidad de la información](https://periscopiofiscalylegal.pwc.es/nuevas-medidas-garantizar-fiabilidad-informacion-obtenida-en-evaluacion-conveniencia-e-idoneidad-clientes-entidades-inversion/amp/)
- [ESMA: revisión conjunta de idoneidad de 2020](https://www.esma.europa.eu/sites/default/files/library/esma35-43-2748%5Fpublic%5Fstatement%5Fon%5F2020%5Fcsa%5Fon%5Fsuitability.pdf)
- [ESMA: revisión de sostenibilidad en la idoneidad (mayo 2026)](https://www.esma.europa.eu/sites/default/files/2026-05/ESMA35-915049491-6291_Statement_on_the_CSA_on_MiFID_II_sustainability_aspects.pdf)
- [CMS: guía de ESMA sobre IA en servicios minoristas](https://cms.law/en/aut/legal-updates/esma-issues-first-formal-guidance-on-use-of-ai-in-retail-financial-services)
- [Opsio: Digital Omnibus y fechas de la Ley de IA](https://opsiocloud.com/es/knowledge-base/omnibus-digital-ley-ia/)
