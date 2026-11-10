# Memoria personal de #21: reproducciones e implementación local revisable

## Estado y alcance

Comprobado el 10/11/2026 en GitHub: #21 continúa abierta, sin commits nuevos respecto a la auditoría.

- Rama de Pablo: `feat/personal-memory-elevenlabs-harness`.
- Commit: `b1b182ed8aaa6710a7df59dcbc571508d38605d8`.
- Base indicada por GitHub: `main`, SHA `0177888e26c78349304f9d95d1fd2a3ba4730663`.
- GitHub informa conflictos de #21 con su base (`mergeable=false`, `dirty`). Estado remoto: conflictos pendientes allí. La copia local integra main para revisión, sin commit.
- Rama propia local: `fix/perfil-memoria-atomicidad-propuesta`, creada desde ese commit exacto.
- Worktree: `/private/tmp/idoneo-pr21-perfil-propuesta`. La demo conserva su checkout de `main`.

**Hay una implementación local sin publicar**, tras la autorización posterior del usuario para
abordar conjuntamente perfiles, autorización/API y frontend. Se reutilizaron estas reproducciones.
La primera etapa se detuvo ante el cambio de contrato; el alcance posterior permite implementar
la propuesta completa para revisión. El contrato y sus decisiones pendientes están en
[`docs/MEMORIA_PERSONAL_SEGURIDAD.md`](../../docs/MEMORIA_PERSONAL_SEGURIDAD.md).
No se ha hecho commit, push, merge a main ni PR ni se ha modificado la rama remota de Pablo o la demo.
Se ha preparado el merge de main en esta copia aislada, sin cerrarlo con un commit.

## Resultado actual

- Suite conjunta final: **474 pasan, 28 omitidos y 1 deseleccionado**, sin fallos.
- Incluye las reproducciones actualizadas, memoria/JSON, SQLite, concurrencia, rollback,
  compatibilidad, consentimiento, independencia MiFID y regresiones #19/#20.
- La revisión final añadió cinco reproducciones fallidas de conexión SQLite compartida (StaticPool):
  lecturas de sesión, turnos, historial/autor y escritura de turnos podían interferir en una transacción
  personal. Tras usar un único candado para todas las conexiones SQLite del almacén, las cinco pasan.
- Autorización REST/MCP, no emisión de credenciales por ID existente, caducidad y configuración
  cerrada; ETag/If-Match 428/412; pruebas reales del cliente TS contra una API local efímera.
- Frontend: **18 tests de contrato**, lint y build de producción correctos en la rama #21.
  La integración actual ya usa el árbol local con main y #22/#23, no una copia superpuesta.
  Pasa también la prueba HTTP Next/API en puertos efímeros. Fuentes locales, sin red.
- JUnit: `/private/tmp/idoneo-pr21-integracion-final.xml`.
- PostgreSQL real, navegador interactivo y llamadas reales de voz no se verificaron.

La suite completa se ejecutó con el entorno local indicado al final, sin excluir las reproducciones,
y con `--deselect=tests/test_migraciones.py::test_el_script_se_niega_con_sqlite`.
No se ejecutaron migraciones ni servicios externos.

## Evidencia ejecutada primero

`test_memoria_personal_reproduccion.py`: **17 fallos y 8 éxitos** sobre #21, sin cambios de producción.
Este fue el resultado inicial, antes de implementar. Los casos se adaptaron después al contrato
obligatorio de revisión y consentimiento; no se silencian mediante xfail.

| Casos | Resultado | Evidencia |
|---|---|---|
| PUT preparado antes de DELETE, entregado después, memoria y SQLite | 2 fallos | La memoria se reactiva y vuelve a guardar el cuerpo anterior. |
| PUT copia datos; DELETE termina; PUT continúa, memoria y SQLite | 2 fallos | Reaparece la copia antigua con consentimiento. Dos hilos y eventos controlan el intercalado. |
| Guardar v1/v2, borrar y volver a consentir, memoria y SQLite | 2 fallos | La nueva capa vuelve a v1. No hay revisión durable que distinga las épocas. |
| Lectura de cuatro estructuras antiguas en JSON y SQLite | 8 fallos | `concerns` texto, `communication` texto y exclusiones largas provocan error; claves internas antiguas se descartan. |
| Editar otro bloque conservando claves antiguas, JSON y SQLite | 2 fallos | Se pierde una clave interna de `communication` al guardar el snapshot nuevo. |
| Fallo simulado de escritura JSON personal | 1 fallo | El archivo anterior queda intacto, pero la memoria ya contiene la operación que falló. |
| Consentimiento ausente/falso, memoria y SQLite | 4 éxitos | La API responde 422 y no escribe. No acredita identidad ni autoría del consentimiento. |
| Edición, fecha de consentimiento e historial personal | 2 éxitos | Conserva fecha, snapshots y evita versiones redundantes. |
| Independencia completa de MiFID y evidencias | 2 éxitos | Actualizar/borrar memoria no cambia snapshots, evidencias ni historial MiFID. |

Los registros antiguos se insertan directamente en archivos/tablas de pruebas para representar
datos aceptados por el contrato anterior. No se conectó a una base existente ni se aplicaron migraciones.
La reproducción inicial pausaba PUT antes de DELETE. La regresión actual controla el intercalado
dentro de la transacción y demuestra que DELETE no puede interponerse en una lectura/escritura
parcial. También comprueba que una petición entregada después del borrado falla por revisión obsoleta.

## Por qué es imprescindible coordinar el contrato

Después del borrado, estas dos acciones tienen exactamente la misma representación actual:

```json
{"consent_given": true, "updates": {"communication": {"pace": "slow"}}, "forget": []}
```

1. Una petición preparada antes del borrado y entregada tarde.
2. Una aceptación nueva e intencionada del cliente después del borrado.

La API no recibe una revisión esperada. `actualizar_personal()` tampoco recibe esa precondición
y fuerza el consentimiento a `True`. El almacén no dispone de información para distinguirlas.
Una transacción evita la carrera entre copiar y borrar, pero no evita la petición antigua que
empieza después de terminar el borrado. Rechazar para siempre toda reactivación tampoco preserva
el comportamiento del producto.

Añadir una versión opcional y seguir aceptando los llamadores actuales dejaría la vía insegura abierta.
Exigirla únicamente en `perfil/` rompería esos llamadores. La implementación posterior exige la
precondición en dominio y API, y adapta explícitamente el frontend; no conserva ese fallback inseguro.

## Contrato implementado como propuesta, pendiente de aprobación del equipo

1. GET devuelve la revisión personal vigente también cuando la memoria está deshabilitada.
   Sin antecedentes, revisión 0. Puede exponerse mediante ETag.
2. PUT y DELETE requieren la revisión esperada, por ejemplo con If-Match. Ausencia y conflicto
   necesitan respuestas acordadas (propuesta: 428 y 412).
3. El almacén comprueba la revisión dentro de la misma transacción que lee, mezcla y persiste.
   Un conflicto no se reintenta adoptando la revisión nueva ni en backend ni en frontend.
4. DELETE elimina el contenido y todas sus versiones personales y deja un registro técnico vacío,
   sin consentimiento y con revisión anterior + 1. El identificador y los metadatos técnicos
   permanecen; no debe describirse como eliminación de todas las filas.
5. Un PUT anterior al borrado pierde; una reactivación exige revisión vigente y aceptación explícita.
6. Acordar también DELETE repetido, `deleted_versions`, fecha/autor de revocación, la conservación
   del registro técnico y qué significa `store.personal()` tras borrar. El GET actual oculta la
   versión de capas sin consentimiento y devuelve `version: null`: debe adaptarse.
7. La API verifica permisos de posesión o de servicio antes de acceder al recurso. Los snapshots
   mantienen el autor técnico del manejador (`agent:memory`); no atribuyen identidad humana.
   `client_id`, `session_id` y un booleano de consentimiento no sustituyen autorización.

Se implementó autorización por credencial de posesión, sin presentarla como autenticación real.
No se ha alterado el harness de ElevenLabs ni llamado a sus servicios.

## Trabajo realizado dentro de perfil/

- Una transacción personal común en `almacenes/{base,memoria,bd}.py` para todos los escritores,
  incluidos guardar, actualizar, borrar y los usos internos de fixtures/reset.
- Memoria: un mismo RLock, copia completa y persistencia antes de cambiar referencias. Separar la
  escritura JSON personal de la escritura del perfil para que ninguna ruta la reescriba sin atomicidad.
  Esta modalidad seguirá limitada a un proceso.
- SQLite: transacción de escritura antes de leer (por ejemplo BEGIN IMMEDIATE); pruebas entre
  conexiones independientes a un archivo temporal.
- PostgreSQL: bloqueo de la fila estable del cliente dentro de la misma conexión/transacción,
  respetado por todos los escritores. Verificación real pendiente en un entorno autorizado.
- `store.py`: precondición de revisión, consentimiento explícito, revisión vacía y conflictos de
  dominio; sin rebasar peticiones antiguas sobre el estado posterior al borrado.
- `personal.py`: separar lectura compatible de validación de entradas nuevas. Validar solo bloques
  modificados y conservar los demás sin pérdida de claves ni truncamientos. La proyección al agente
  deberá excluir valores antiguos incompatibles sin borrarlos en almacenamiento.
- No modificar cifras, evidencias, estados, cálculos ni historial MiFID. Delimitar que el borrado
  actual alcanza toda la capa personal; `exclusions` afecta a los filtros de productos.

Se añadieron tests de revisión ausente/obsoleta, tombstone tras reinicio, rollback del borrado,
PUT/PUT y PUT/DELETE con hilos y conexiones SQLite independientes, fallos JSON y proyección segura
de datos antiguos. PostgreSQL sigue sin verificación real en este trabajo.

## Suite original y regresiones (línea base anterior a la implementación)

Suite original ejecutada con las reproducciones excluidas: **357 pasan, 26 se omiten y 1 se deselecciona**.

- #19, `test_validar_atomicidad.py`: **35 pasan y 5 se omiten** por no aplicar a memoria.
- #20, `test_calculos_obsoletos.py`: **56 pasan**.
- Las demás omisiones requieren PostgreSQL. `TEST_POSTGRES_URL` se fijó vacío.
- Se deseleccionó `test_migraciones.py::test_el_script_se_niega_con_sqlite` para no invocar el script
  de migraciones. Los tests estáticos del esquema sí se ejecutaron.
- Advertencia existente: deprecación de Starlette TestClient/httpx.
- JUnit local: `/private/tmp/idoneo-pr21-suite-base.xml`.

Comandos desde `backend/` del worktree, utilizando el virtualenv ya instalado del proyecto:

```sh
env PERFIL_ALMACEN=memoria DATA_PERSIST=0 DATABASE_URL= TEST_POSTGRES_URL= \
  ANTHROPIC_API_KEY= ELEVENLABS_API_KEY= ELEVENLABS_AGENT_ID= LOAD_DEMO_FIXTURE=0 \
  /Users/juanfernandezcondormango/hack-finance-uc3m-2026/backend/.venv/bin/python \
  -m pytest -q tests/test_memoria_personal_reproduccion.py --tb=short

env PERFIL_ALMACEN=memoria DATA_PERSIST=0 DATABASE_URL= TEST_POSTGRES_URL= \
  ANTHROPIC_API_KEY= ELEVENLABS_API_KEY= ELEVENLABS_AGENT_ID= LOAD_DEMO_FIXTURE=0 \
  /Users/juanfernandezcondormango/hack-finance-uc3m-2026/backend/.venv/bin/python \
  -m pytest -q --ignore=tests/test_memoria_personal_reproduccion.py \
  --deselect=tests/test_migraciones.py::test_el_script_se_niega_con_sqlite
```

La suite usa procesos propios de pruebas y puertos efímeros; no modifica ni detiene los servidores de
la demo. No se realizaron llamadas a APIs de pago, Supabase ni PostgreSQL ni se ejecutaron migraciones.

## Siguiente revisión

Juan, Pablo y Alejandro deben revisar el contrato implementado y las decisiones pendientes antes
de publicarlo. El usuario no autoriza aún commit, push ni PR. Los conflictos con main se han resuelto en la copia local; el merge permanece sin commit para revisión.
La prueba HTTP Next/API verifica además el bloqueo de autovalidación por el proxy.
La rama local contiene producción, tests y documentación sin publicar.
