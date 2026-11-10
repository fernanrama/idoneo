# Propuesta local de seguridad y persistencia de la memoria personal

Corrección revisable del prototipo local sobre #21, preparada desde el commit original de Pablo
`b1b182ed8aaa6710a7df59dcbc571508d38605d8` e integrada con main
`8b698b795da2ee2be8ef28ee58590f0baf819453` (#22/#23). El commit de integración es `1149da4`.
El usuario ha revisado el resultado y autorizado su publicación mediante push normal a
`feat/personal-memory-elevenlabs-harness`, manteniendo #21 abierta y sin fusionarla a main.

Se aceptan provisionalmente: credenciales de posesión para clientes ficticios, validación web
bloqueada, recuperación y revocación individual pendientes, ADMIN_TOKEN exclusivo de servicios
de confianza y borrado con revisión técnica sin afirmar eliminación de copias externas.
Estas condiciones no constituyen autenticación bancaria ni autorización para producción.
Los respaldos locales se conservan fuera del repositorio y no forman parte de los commits.

[Inventario completo de archivos modificados y añadidos](MEMORIA_PERSONAL_ARCHIVOS.md).

## Autorización del prototipo

La posesión de una credencial autoriza un cliente concreto. No verifica nombre, identidad civil,
condición de cliente de una entidad ni identidad de asesor. No se denomina login bancario.

- `POST /api/sessions` sin `client_id` genera un identificador nuevo en el servidor y realiza un alta
  exclusiva. Solo después de un alta genuina entrega `access_token` junto a la sesión.
- Abrir otra sesión indicando un `client_id` requiere una credencial válida para ese cliente.
  La respuesta no entrega otra credencial. No existe recuperación por conocer un identificador.
- La credencial está firmada con HMAC y tiene caducidad. `CLIENT_ACCESS_SECRET` es obligatorio,
  solo servidor y de al menos 32 caracteres; sin él la emisión falla de forma cerrada. No se guarda
  en Markdown, Git ni salidas de coordinación. La TTL propuesta es ocho horas.
- Lecturas y escrituras de clientes/sesiones, contexto de agentes y bootstrap de voz comprueban
  el permiso del cliente. Un `session_id` solo identifica un recurso, no autoriza operaciones.
- REST y las cuatro herramientas MCP aplican la misma separación entre clientes. El consumidor
  MCP debe proporcionar una credencial autorizada; ser una herramienta de lectura no le da acceso.
- El servicio local configurado con `ADMIN_TOKEN` es una credencial privilegiada explícita,
  no un usuario final. No hay proxy lector anónimo que añada ese token por estar en localhost.
- Los tokens no se incluyen en URLs, snapshots, eventos ni logs. El frontend guarda la credencial
  en `sessionStorage` y únicamente metadatos de sesión en `localStorage`.
- Las respuestas privadas no se cachean. CORS expone ETag para que el navegador pueda enviar la
  siguiente precondición. CORS y la comprobación de Host no se consideran autorización.

La pérdida/caducidad de la credencial no permite reclamar los datos antiguos por `client_id`.
Rotar el secreto invalida todas las credenciales; no hay revocación selectiva ni recuperación de cuenta.
Una XSS puede leer `sessionStorage`: esta solución requiere revisar el transporte antes de usar datos reales.

## Revisión y borrado

Ejemplos reproducibles, exclusivamente con clientes ficticios de los tests:

1. En #21, abrir sesión con `{"client_id":"cliente-victima-test"}` permitía utilizar esa sesión
   para leer y mutar su memoria sin demostrar permiso. Ahora `test_credencial_solo_se_emite_en_alta_exclusiva`
   y `test_conocer_session_id_no_da_acceso` verifican 401 sin credencial y 404 con la de otro cliente,
   para GET/PUT/DELETE, tanto en memoria como SQLite. Las cuatro herramientas MCP comprueban lo mismo.
2. Guardar preferencias en v1, preparar un PUT con ellas, borrar y entregar ese PUT tarde restauraba
   datos en #21. Ahora DELETE deja v2 y el PUT con `If-Match: "personal-1"` devuelve 412 sin escribir.
   Se reproduce en `test_put_retrasado_no_reactiva_memoria_borrada` y en la integración TS/API.
3. Un fallo de volcado JSON podía dejar la memoria del proceso por delante del archivo. El test
   `test_fallo_de_json_personal_no_deja_cambios_en_memoria` inyecta el fallo y comprueba ambos estados.

`GET /api/sessions/{sid}/memory` devuelve `version` y un ETag fuerte `"personal-N"`. Sin antecedentes
la revisión es 0. Una capa revocada sigue devolviendo su revisión, con `enabled=false` y `data={}`.

`PUT` y `DELETE` requieren un único If-Match con la revisión observada. Falta: **428**. Revisión
obsoleta: **412**. No se acepta `*` como permiso para omitir el control. Una actualización fallida
no se reintenta automáticamente usando el estado nuevo.

La comparación, lectura, mezcla y escritura ocurren dentro de una misma transacción personal.
DELETE elimina todas las versiones con contenido y conserva una revisión técnica vacía, sin
consentimiento y con número anterior + 1. No reinicia la secuencia. Una petición anterior al borrado
ya no puede restaurar los datos; una reactivación requiere revisión vigente y consentimiento explícito.

Un DELETE sobre una revisión ya revocada conserva la revisión y devuelve cero versiones eliminadas.
Repetir una petición con If-Match anterior sigue siendo un conflicto: el cliente debe leer el estado.
La revisión técnica conserva identificador, fecha y autor de la revocación, sin preferencias borradas.
Este comportamiento no se describe como eliminación de todas las filas ni de copias externas.

## Persistencia, consentimiento y compatibilidad

- Memoria: un mismo RLock cubre toda la operación. Si se persiste JSON, se escribe una copia en un
  temporal, se sincroniza y sustituye el archivo antes de actualizar las referencias en memoria.
  Las escrituras MiFID no reescriben el archivo personal. Esta modalidad coordina un proceso.
- SQLite: reserva de escritura antes de leer la revisión y una conexión para toda la transacción.
  Las pruebas concurrentes usan un archivo temporal y conexiones independientes.
  Un candado común cubre también sesiones, turnos y MiFID en cada instancia SQLite para que la
  conexión física compartida de StaticPool no confirme/revierta una transacción personal ajena.
  Cinco pruebas de reproducción fallaron antes de completar esta protección y pasan con ella.
- El código SQL conserva la vía PostgreSQL con bloqueo de la fila del cliente, pero no se conecta
  ni se afirma verificado con PostgreSQL real en esta propuesta.
- Todos los escritores personales usan la vía transaccional. Los métodos internos de fixture no
  son endpoints y no se utilizan como alternativa a If-Match en la API.
- La edición conserva la fecha original del consentimiento; no se infiere consentimiento de
  una sesión, de los avisos MiFID ni de una respuesta del modelo. La reactivación es explícita.
- El modelo de lectura admite los datos aceptados antes de #21. Los límites nuevos se aplican
  a los bloques nuevos/modificados, sin perder claves desconocidas de bloques históricos intactos.
- La proyección a agentes admite únicamente campos y tipos previstos, con límites de longitud.
  Los valores antiguos incompatibles se conservan para el propietario, pero no se proyectan.
  Marcar texto como datos reduce riesgo de instrucciones maliciosas; no demuestra inmunidad del modelo.
- Ninguna operación personal cambia números, evidencias, estado o historial MiFID. `exclusions`
  puede cambiar filtros de productos sin cambiar `profile_version`; sigue siendo una capa distinta.

## Frontend y voz

El cliente envía Authorization en las rutas privadas e If-Match en las mutaciones personales.
Un 412 muestra el conflicto y exige revisar/confirmar; no guarda de nuevo por iniciativa propia.
La interfaz explica que borrar afecta a toda la capa personal y no elimina el expediente MiFID.

Se conserva `bootstrapVoz(session_id)` con su usuario seudónimo, variables dinámicas y ubicación.
El fallback público no elimina los errores de autorización ni habilita memoria ajena. Los tests
utilizan transportes simulados; no se configura ni llama a una cuenta real de ElevenLabs.

La demo sin credenciales usa `/api/demo/profile` y `/api/demo/constraints`: fixture ficticio fijo,
sin `personal`, separado del cliente mutable de Carmen. No entrega credenciales para ese cliente.
`DEMO_ENDPOINTS=0` deshabilita la lectura de demo. La vista de entidad puede leer datos del propietario
que posee la credencial o la demostración fija; el acceso de un asesor desde otro navegador no se
resuelve usando un identificador o un proxy anónimo con privilegios.

La validación web devuelve 403 incluso con Bearer de cliente y servicio configurado en Next.
El proxy no añade ADMIN_TOKEN ni realiza peticiones al backend. La API de validación requiere
propietario y servicio explícitos; la interfaz deja el botón deshabilitado. No se inventan roles
ni un login de asesor: habilitar esa acción exige acordar un contrato independiente.

## Límites aceptados provisionalmente y decisiones para producción

| Tema | Propuesta local | Alternativa que requiere acuerdo |
|---|---|---|
| Identidad y transporte | Credencial de posesión en sessionStorage | Sesión HttpOnly con protección CSRF o identidad autenticada de una entidad |
| Acceso de asesores/MCP | MCP con credencial explícita; validación web bloqueada | Roles y permisos por entidad/asesor, con delegación y auditoría |
| Caducidad y recuperación | TTL ocho horas, sin recuperación por ID | Renovación, revocación selectiva y recuperación con identidad verificada |
| Borrado | Toda la capa personal, revisión vacía técnica | Borrado solo de preferencias conversacionales o política distinta de metadatos |
| Datos anteriores | Preservar sin normalizar silenciosamente | Conversión versionada y revisada de formatos históricos |
| Demo pública | Fixture fijo exclusivamente ficticio | Exposición de otro conjunto explícitamente aprobado |
| Voz y copias externas | Borrado del almacén local | Coordinación con retención, conversaciones activas y copias de proveedores |

No se usan datos reales, Supabase ni APIs de pago. La publicación de esta corrección en #21 está
autorizada tras la revisión del usuario. No se autoriza fusionar a main ni habilitar uso de producción.

## Evidencia

Las reproducciones iniciales y la evolución de los resultados se mantienen en
[`backend/tests/MEMORIA_PERSONAL_CONTRATO_PENDIENTE.md`](../backend/tests/MEMORIA_PERSONAL_CONTRATO_PENDIENTE.md).
Resultado: **474 tests backend correctos, 28 omitidos y 1 deseleccionado** (el que invoca el script
de migraciones), sin fallos. Incluye las regresiones #19/#20 y una integración del código TypeScript
real con uvicorn en un puerto local efímero. PostgreSQL se mantuvo deshabilitado.

Frontend integrado: **18 tests de contrato**, lint y build de producción correctos. Además,
`npm run test:integracion`, con `IDONEO_PYTHON` apuntando al entorno existente, levanta Next/uvicorn
propios en puertos efímeros y verifica seis rutas, autorización, CAS, consentimiento, independencia
MiFID, bloqueo del proxy y bootstrap sin claves. No toca los servidores de la demo.

La integración local real conserva las páginas, estilos, `/escenario`, guion y componentes de main;
resuelve los conflictos de README, página de perfil y hook de entrevista. El componente personal
se monta desde el proveedor compartido; no necesita el antiguo ui.tsx eliminado por #23. API y vista
de entidad combinan las adaptaciones de seguridad con main. Los scripts/prompts/harness de Pablo,
el webhook y la herramienta datos_pendientes se mantienen.

JUnit actualizado: `/private/tmp/idoneo-pr21-integracion-final.xml`. #19: 35 correctos y 5 omitidos;
#20: 56 correctos. Autorización: 63 correctos; reproducciones: 25 correctos. La comprobación anterior
por copia y `verificar-main.mjs` queda como evidencia histórica; el resultado actual usa el árbol
real integrado. Las fuentes del build se sustituyen por un archivo local mediante el hook de prueba
`NEXT_FONT_GOOGLE_MOCKED_RESPONSES` del Next instalado, sin red. No acredita fidelidad visual.
No se ha usado navegador interactivo, PostgreSQL real ni llamadas a proveedores.

Reproducción cerrada de la autovalidación: con el proxy anterior, propietario + ADMIN_TOKEN añadido
por Next permitían validar. Los tests del cliente fallaron primero (200 en lugar de 403). Tras
retirar el reenvío privilegiado pasan, y la prueba HTTP contra Next compilado confirma 403 incluso
si se presenta el Bearer y se manipula X-Forwarded-Host. La aserción de consentimiento que comprobaba
otro cliente en la reproducción inicial se corrigió para comprobar el cliente de la petición.

Archivos de producción modificados: `backend/app/perfil/{store,personal}.py`,
`backend/app/perfil/almacenes/{base,memoria,bd}.py`, `backend/app/acceso.py`, `backend/app/main.py`,
`backend/app/voz.py`, `backend/app/mcp/servidor.py`, `backend/app/agentes/memoria.py`;
`frontend/src/lib/{api,credenciales,tipos,demo,iniciarVoz}.ts`, `onboarding.tsx`, `useEntrevista.ts`,
`servidor/entidad.ts`, componente de memoria y su CSS, montaje de perfil, aviso/permisos en la vista
de entidad y rutas Next de validación/reset. `.env.example` documenta únicamente nombres y requisitos de configuración.
Tests nuevos y adaptaciones de los existentes acompañan los cambios; no hay migraciones.
`docs/CONTRATOS.md`, `frontend/README.md` y los ejemplos de entorno describen el contrato propuesto.
