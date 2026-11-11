# Estado común — 8 noviembre 2026

## Objetivo actual
Dejar preparada la gestión integral del hackathon: repositorio, ideas, producto, desarrollo, evaluación, aprendizaje, demo, presentación y entrega. Las seis notas iniciales están creadas. El enunciado ha sido aportado y analizado por dirección; compartir el análisis y contrastar candidatas con el equipo antes de elegir producto y arquitectura. Fuente: [ANALISIS_INICIAL.md](estrategia/ANALISIS_INICIAL.md).

## Actualización 8/11 tarde — desarrollo iniciado
- **Producto: Idóneo** (D-008), indicado por Fernán: el equipo empieza a desarrollarlo. Diseño de Alejandro en [docs/diseno/01-diseno.md](../docs/diseno/01-diseno.md). Demanda, novedad y encaje con los patrocinadores siguen siendo hipótesis por validar.
- **Repo reorganizado** (D-009): gestión en `gestion/`, producto en `docs/`, código en `backend/` y `frontend/`. Checkout local: `C:\Users\ferna\gcx\hack-finance-uc3m-2026`. La carpeta antigua queda como copia de seguridad.
- **PDF del enunciado fuera del repo** (D-010): solo en local, en `gestion/enunciado/`, porque el repo será visible para el jurado.
- **Stack v0** (D-011): FastAPI + Next.js + ElevenLabs + Claude + MCP. Backend v0 probado en local (5 tests y arranque con datos simulados de Carmen). Pendiente de las pruebas de voz, del MCP de MyInvestor y del despliegue.
- Reparto confirmado por Fernán en [gestion/coordinacion/REPARTO.md](../gestion/coordinacion/REPARTO.md): A Juan; B Hammad (entrevistador y extractor) y Pablo (verificador y medición); C Fernán; D Alejandro (incluye integración y entrega). Rodrigo: pitch y revisión financiera (propuesta).
- Lo que sigue más abajo es el estado previo a esta actualización; donde contradiga lo anterior, prevalece esta sección.

## Decisiones vigentes
- Navegador integrado para investigación web.
- Dirección general en el chat original; seis chats de especialidad con notas compartidas.
- Foco provisional de Fernán: desarrollo de la aplicación, con tutoría financiera aplicada.
- No se ha elegido idea, stack, marca, reparto de personas ni presupuesto.
- Fernán autoriza delegación entre los seis chats y subagentes delimitados, dejando resultados por escrito. La preparación inicial no requería más datos; ahora el equipo debe contrastar candidatas y aclaraciones pendientes.
- Repositorio privado creado con autorización de Fernán: https://github.com/fernanrama/hack-finance-uc3m-2026 . GitHub está conectado con acceso al repositorio, según confirmación de Fernán. Este entorno cloud dispone de un checkout Git; esto no acredita el estado del espacio local original.
- Preferencia de ejecución: nube para tareas autónomas y acceso móvil con PC apagado; local para pruebas interactivas, integración y demo cuando aporte valor. Optimizar por utilidad, no por cantidad de agentes.
- Los seis chats originales son locales. Su creación no configura un entorno cloud ni garantiza acceso móvil al mismo historial.
- El aviso previo de cuota agotada queda como antecedente: Fernán confirma que el entorno cloud `hack-finance-uc3m-2026` ya está publicado. Esta sesión accede al checkout cloud. No se infiere ningún reinicio de cuota ni cambio de plan. La prueba desde móvil sigue pendiente.
- Fernán confirma que los chats 03 (producto) y 06 (operaciones) se reanudaron y completaron sin error. No implica implementación de una app ni pruebas de producto.
- Carga inicial por navegador: documentos raíz y paquete `hack-finance-bootstrap-documentacion.zip`. Puesta a punto cloud: las 16 entradas se validaron como rutas relativas dentro del repositorio, sin enlaces simbólicos; su contenido coincide íntegramente con los archivos de las seis carpetas del checkout. El ZIP se retiró y la PR #1 ya está integrada en `main` mediante `dbb06ff`, comprobado en esta sesión. Se conservan sus cambios.

## Enunciado recibido, fuentes y aclaraciones
Dirección leyó y renderizó la copia local de `Completo hack finance.pdf` (dos páginas). Huella SHA-256 comunicada: `2182c34ebb762066c28dbd46af7ddf36d9d12c610bd052fcfb2a928063701341`. El PDF solo está en el equipo local; no está en cloud y aquí no se ha recalculado su huella. [Análisis revisado](estrategia/ANALISIS_INICIAL.md) conserva páginas, fuentes externas y límites; no sabemos si el PDF agota las bases.

Rúbrica (p. 1): innovación y viabilidad 30 %, IA frontera 15 %, UX/accesibilidad 15 %, implementación/código 30 %, presentación 10 %. Entrega (p. 2): GitHub público o compartido con las personas indicadas, ZIP de GitHub como versión oficial, README reproducible, PDF de una cara y PowerPoint; formulario BEST. Cuenta la última entrega completa dentro del plazo; demo coincidente y sin cambios tras cierre. No se han cambiado permisos ni enviado entregables.

Fernán aclara: voz no obligatoria y PowerPoint obligatorio; uso de diapositivas opcional según PDF. Cierre comunicado: miércoles 23:59; fecha provisional 11/11/2026, zona de Madrid supuesta por confirmar. Presentación de aproximadamente diez minutos: estimación, duración no confirmada. Recursos comunicados: 400 € en créditos Claude y ElevenLabs Creator, sin límites, titular, periodo o APIs habilitadas confirmados. Pendientes también reglas completas de IA/código previo, datos, accesos, desempates y aplicación del criterio de audio.

## Sincronización de esta actualización
Según dirección, la carpeta local no es un checkout Git y sus cambios posteriores a `dbb06ff` no se sincronizaron automáticamente. Esta rama incorpora explícitamente el análisis comunicado y el estado asociado; no el PDF ni otros cambios locales desconocidos. Integración pendiente de revisión. No copiar claves.

## Propuestas aún no elegidas
Copiloto para asesores; conciliación de movimientos y facturas; simulador financiero conversacional. Son hipótesis previas al reto, no compromisos. El análisis añade A (comprensión de una decisión de inversión), B (liquidez ligada a objetivos) y C (excepciones de cobros para autónomos). Se propone contrastar A y B, sin selección ni validación de demanda, novedad, beneficios o disposición a pagar.

## Información del equipo pendiente
Confirmar la separación de los seis nombres, habilidades, disponibilidad y responsabilidad de integración. No bloquear el arranque por ello.

## Hoja de ruta provisional
La espera del enunciado queda superada por su recepción. Conservar las fechas declaradas del evento (8–12 de noviembre), distinguiéndolas del cierre de entrega comunicado (miércoles 23:59; 11/11 provisional, zona por confirmar). Recalcular el plan con ese cierre y la duración pendiente. Propuesta: contrastar dos candidatas durante 60–90 minutos cada una, buscar motivos de descarte y decidir con el equipo; no son validaciones ejecutadas. Orden de hitos: entender y elegir → recorrido completo → diferencial y evaluación → estabilización y ensayos → entrega.

## Uso
Leer AGENTS.md. Consultar coordinacion/TABLERO.md y coordinacion/areas/ para avances. Los chats no reciben automáticamente cada conversación de los demás: las notas son el punto de sincronización.
