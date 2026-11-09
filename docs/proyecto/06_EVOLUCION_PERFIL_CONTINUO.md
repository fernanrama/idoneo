# Idóneo: evolución hacia un perfil financiero continuo

9 noviembre 2026 · Propuesta estratégica para revisión del equipo. «Idóneo» sigue siendo un nombre provisional.

## Visión y alcance

La entrevista inicial es el primer paso. La propuesta es que Idóneo mantenga un perfil financiero documentado que pueda actualizarse cuando cambien las necesidades del inversor y que otros agentes puedan consultar, con los permisos correspondientes, antes de contextualizar alternativas.

El valor esperado es reducir preguntas repetidas y dar a la entidad información más actual y trazable. Es una hipótesis de producto: todavía no se han medido ahorro de tiempo, precisión de las microentrevistas ni impacto en clientes reales.

Este documento desarrolla la propuesta aportada en `Propuesta.pdf` (referencia local, no incorporada al repositorio). La actualización por eventos vitales ya aparece en [el diseño original](01_DISENO.md), [la auditoría](02_AUDITORIA_Y_DECISIONES.md) y [el contrato del perfil](04_CONTRATO_PERFIL.md). Aquí se ordena esa visión en tres fases, sin repetir el esquema ni cambiar contratos técnicos, cálculos o reparto. El estado de implementación se ha contrastado por lectura del código de la base local `a062686`; no acredita nuevas pruebas de funcionamiento con servicios reales.

Contraste posterior con `main` en `470facd`: desde `ee4c48d` se han incorporado normalización de cifras, guardas de contexto y plausibilidad, procesamiento en serie por sesión y evaluación del extractor con entrevistas simuladas. Las [ejecuciones E-00 y E-01](../../gestion/evaluacion/PLAN_Y_EVIDENCIAS.md#2-ejecuciones-y-evidencias) registran resultados y limitaciones de esa evaluación; no validan la voz ni las microentrevistas. Estos cambios no añaden rutas administrativas, permisos de terceros ni un flujo de perfil continuo.

Idóneo recoge, comprueba y documenta información; **no recomienda ni selecciona productos**. Las recomendaciones y decisiones de la entidad siguen siendo responsabilidad de sus profesionales y sistemas. **Idóneo no garantiza por sí solo el cumplimiento MiFID**: evidencias, cálculos y validación humana son apoyos que requieren controles, revisión normativa y procesos de la entidad.

## Fase 1 — Entrevista MiFID inteligente

El recorrido propuesto combina una entrevista por voz con ElevenLabs y Claude, una alternativa escrita y supervisión humana:

1. Explicar al cliente el propósito de la evaluación y el uso de IA, y gestionar los avisos y permisos que correspondan.
2. Recoger conocimientos, experiencia, situación económica, objetivos, liquidez, tolerancia al riesgo y preferencias.
3. Plantear escenarios para comprobar la comprensión, en vez de dar por válido lo que el cliente declara saber.
4. Detectar contradicciones, guardar datos estructurados con su fuente y evidencia, y crear versiones con motivo y autor. Los resultados financieros se calculan con código; el modelo no fija esos números.
5. Presentar el perfil y las alertas a una persona de la entidad, que revisa, corrige y valida antes de utilizarlo como perfil activo.

**Implementado:** modelo estructurado, evidencias con cita y referencia al turno, versionado, cálculos deterministas, API, pantalla de validación y servidor MCP de lectura. El extractor con Claude y el entrevistador de texto tienen implementación; necesitan configuración de acceso al servicio. El verificador actual incluye reglas deterministas de contradicción, no una revisión completa con Claude.

**Parcialmente preparado:** integración del SDK de ElevenLabs, URL firmada y reenvío de turnos al backend. La documentación de voz deja pendientes las pruebas con cuenta real y móvil, la configuración de Claude en el agente de voz y la recuperación de audio. Las marcas de tiempo del navegador son aproximadas; una cita almacenada no acredita por sí sola la disponibilidad de un clip reproducible. La fase completa de voz, evidencias de audio y revisión no se presenta como validada de punta a punta.

Referencias de implementación: [agentes](../../backend/app/agentes/README.md), [voz y límites de la prueba](../../frontend/README.md#voz-con-elevenlabs-lo-comprobado-y-lo-pendiente), [backend integrado](../CONTRATOS.md#backend-integrado-persistencia-validación-y-versionado).

## Fase 2 — Microentrevistas adaptativas

**Hoja de ruta: las microentrevistas todavía no funcionan como un flujo de producto completo.**

La propuesta es abrir una conversación breve cuando cambien los objetivos, la necesidad de liquidez, la situación económica o las preferencias del cliente. Se comprobarían los atributos afectados y sus dependencias, conservando la información que siga siendo válida. Una actualización parcial no debe dar por vigente el resto del perfil sin comprobarlo ni impedir una reevaluación más amplia cuando haga falta.

El recorrido previsto sería:

1. Registrar el cambio comunicado, su origen y el motivo de revisión.
2. Determinar qué datos hay que confirmar y formular preguntas específicas, sin repetir innecesariamente toda la evaluación.
3. Guardar respuestas y evidencias, crear nuevas versiones y recalcular los resultados afectados mediante las funciones deterministas.
4. Comparar la versión previa con la propuesta: qué cambió, por qué, con qué evidencia y qué restricciones se ven afectadas.
5. Solicitar revisión humana cuando proceda; en el recorrido de Carmen se requiere antes de compartir el perfil actualizado como validado. Un cambio material, información insuficiente o contradicciones deben poder ampliar la evaluación.

**Base parcialmente preparada:** el backend conserva versiones con motivos y autoría, permite leer el historial y versiones concretas, admite parches por campo y tiene estados de revisión. Un cambio de datos por un agente sobre un perfil activo puede llevarlo a `review_due`; abrir después una sesión permite retomar la evaluación. El entrevistador de texto ya recibe campos pendientes o que conviene repreguntar. Estas piezas no constituyen un planificador de microentrevistas.

**Pendiente:** detección y registro específico de eventos vitales, selección adaptativa del alcance, comparación de versiones en la interfaz, caducidad automática de `next_review`, avisos al asesor y un recorrido probado de actualización y nueva validación. No se proponen aquí endpoints ni cambios de esquema.

Hay un límite relevante para el diseño futuro: hoy [el perfil para consumidores](../../backend/app/perfil/store.py) busca el último `active`; puede seguir sirviendo una versión activa anterior aunque la última esté en revisión. Por tanto, el sistema actual no garantiza que un cambio de liquidez bloquee el consumo del perfil antiguo. La política de vigencia y bloqueo ante cambios materiales deberá acordarse y probarse antes de habilitar esta fase; este documento no la modifica.

## Fase 3 — Verificación para otros agentes

**Hoja de ruta:** GPTadvisor y otros agentes autorizados podrían solicitar comprobaciones puntuales cuando falte información o cambie el contexto. La petición debería identificar el atributo que necesita comprobarse y el motivo; Idóneo iniciaría una microentrevista con el cliente, documentaría el resultado y lo sometería a revisión humana cuando corresponda. El agente solicitante no validaría por sí mismo el perfil.

Tras la revisión, el consumidor autorizado recibiría por API/MCP la versión adecuada del perfil, su estado, restricciones y evidencias necesarias. El objetivo es que pueda conocer tanto la información actualizada como sus límites, sin confundir una propuesta de cambio con una versión validada.

Esto permitiría a MyInvestor contextualizar alternativas de su catálogo según conocimientos, experiencia, horizonte, capacidad de soportar pérdidas, liquidez, riesgo y preferencias del inversor. El interés en un tipo de inversión no bastaría para considerarlo adecuado o conveniente. Que un catálogo incorpore nuevos productos y que una entidad quiera comprobar atributos adicionales son escenarios futuros, no integraciones ni acuerdos confirmados.

**Disponible como base:** API y cuatro herramientas MCP de lectura para perfil, restricciones, evidencias y contexto. El repositorio documenta una prueba de consumo desde Claude junto al conector de MyInvestor; eso no demuestra una integración operativa con GPTadvisor ni un servicio de verificaciones solicitado por terceros.

**Pendiente:** solicitudes de verificación, inicio de microentrevistas por otros agentes, devolución de resultados, autenticación y autorización de consumidores, permisos por cliente y propósito, minimización de datos y trazabilidad de accesos. Las lecturas actuales de API/MCP no autentican a sus consumidores; la demo debe usar datos simulados. `ADMIN_TOKEN` protege determinadas acciones administrativas, pero no resuelve esos permisos ni el filtro `Host`/`X-Forwarded-Host` autentica al asesor.

La vía documentada para el catálogo de MyInvestor es su uso conversacional como conector en Claude; no se añade acceso programático desde Idóneo ni una copia del catálogo. Cualquier integración adicional requerirá revisar las condiciones y permisos aplicables. Véanse [los límites y condiciones ya recogidos](05_MCP_MYINVESTOR.md).

## Ejemplo: Carmen comunica una nueva necesidad de liquidez

**Escenario ilustrativo con datos simulados; no es una funcionalidad ya disponible ni una recomendación financiera.** Carmen tiene un perfil validado y comunica: «Necesito disponer de 6.000 euros dentro de tres meses para una reforma».

| Paso propuesto | Qué ocurriría | Situación actual |
| --- | --- | --- |
| Registrar la novedad | Vincular la necesidad de liquidez con Carmen, la fecha, el motivo y su declaración | Existen sesiones, turnos y evidencias; el disparador específico está pendiente |
| Acotar la conversación | Confirmar importe, fecha, si sustituye o se añade al objetivo anterior y si cambia el ahorro disponible; comprobar otros atributos solo si se ven afectados | La selección de una microentrevista está pendiente |
| Actualizar y comparar | Crear versiones sin sobrescribir el historial y mostrar diferencias en objetivo, horizonte, liquidez y resultados recalculados | Versionado y cálculos implementados; comparación guiada pendiente |
| Revisar | El asesor comprueba la evidencia y las contradicciones y valida la actualización; no se activa automáticamente por haber terminado de hablar | Validación implementada; orquestación del recorrido y política sobre el activo anterior pendientes |
| Compartir | Un agente autorizado recibe la versión validada y aplica sus restricciones al contextualizar alternativas del catálogo | Lectura API/MCP disponible; permisos y solicitudes de verificación pendientes |

No se fija de antemano un nuevo nivel de riesgo ni un producto para Carmen: dependen de los datos confirmados, los cálculos y la revisión. Si GPTadvisor detectase primero que falta una comprobación de liquidez, podría solicitar ese mismo recorrido en la fase 3; hoy no existe esa solicitud.

## Resumen de estado y siguiente paso

| Capacidad | Estado de esta propuesta |
| --- | --- |
| Perfil estructurado, validación de datos, versiones, cálculos y validación humana | Implementado como base del MVP |
| Entrevista completa por voz y evidencias con audio comprobado | Parcialmente preparado; integración y prueba real pendientes |
| Actualización dirigida por cambios y comparación guiada | Hoja de ruta; se apoya en piezas existentes |
| Verificaciones iniciadas por agentes autorizados | Hoja de ruta; el MCP actual es de lectura |

El siguiente paso propuesto es revisar esta visión con producto, backend, voz, evaluación e integración y acordar un único caso de Carmen para una futura prueba. Antes de desarrollarlo habrá que definir vigencia de versiones, alcance de la revisión humana y permisos de terceros. Esa decisión se tramitará aparte: este documento no cambia el alcance comprometido de la demo ni autoriza trabajo sobre otros módulos.
