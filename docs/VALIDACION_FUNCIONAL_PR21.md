# Validación funcional local de #21 · 10/11/2026

Base comprobada en remoto: `7729a81aa6d68fbff95b823e9048597e756db1a0`.
Validación realizada en el worktree aislado antes de publicar. El usuario ha revisado y autorizado
incorporar las dos correcciones y sus pruebas a #21 mediante push normal, sin merge a main.
No se modifican los servidores de
la demo en 8000/3000. Backend de prueba en 18021, frontend en 13021, solo datos ficticios y
`PERFIL_ALMACEN=memoria`, `DATA_PERSIST=0`, sin DATABASE_URL ni claves de proveedores.

## Método y límites

El navegador integrado no estuvo disponible. Se utilizó Chrome headless instalado con un perfil
temporal independiente y Playwright ya disponible en el entorno. Se bloquearon destinos externos
en las peticiones de página. El build utilizó las fuentes reales de Figtree, Outfit y JetBrains Mono
ya presentes en la caché local, sin descargarlas. No se instalaron dependencias de producción.

- Escritorio: viewport 1440 × 1000.
- Móvil: viewport 390 × 844, touch y modo móvil emulados en Chrome.
- Se ejecutaron clics, navegación, selectores y formularios reales, con JavaScript hidratado.
- Las capturas corresponden al navegador real y se inspeccionaron visualmente; no son mockups.
- Esto no es una prueba en un teléfono físico, Safari/iOS ni una revisión manual de audio.
- Carmen se reprodujo sin sonido, avanzando con sus controles. No se inició una conversación
  real con Claude/ElevenLabs ni se sincronizó una cuenta remota.

## Defectos reproducidos y corregidos

1. **Respuesta del perfil anterior tras restaurar sesión.** Retrasar 800–1000 ms el GET público de
   Carmen permitía que sus 80.000 € sustituyeran visualmente el perfil vacío del propietario actual.
   La API no concedía acceso a otro cliente: era una carrera de estado en `usePerfil.ts`.
   Ahora cada vista se vincula a su client_id, se invalidan respuestas anteriores al cambio y se
   retiran datos visibles si la petición vigente falla. Una petición pendiente por cliente evita
   solapar el sondeo. Se comprobó también una latencia de 3500 ms con intervalo de 3000 ms para
   evitar que la protección descartase indefinidamente todas las respuestas lentas.
2. **Fin de demo al saltar en pausa.** Pausar y saltar todos los turnos dejaba la pantalla en
   «19 de 19», sin mostrar el final. La comprobación de fin ahora precede a la de pausa.

Las reproducciones fallaron antes de las correcciones. El script de navegador conserva ambas,
incluido el caso de sondeo lento añadido al endurecer el tratamiento de respuestas antiguas.
No cambian contratos públicos, backend, permisos, persistencia ni harness de ElevenLabs.

## Cobertura automatizada

El script `frontend/scripts/test-navegador-local.mjs` comprueba:

- Cambio/restauración de cliente y respuestas retrasadas; sondeo más lento que su intervalo.
- Navegación desde portada a entrevista en escritorio y móvil.
- Carmen: pausa, salto de turnos, seis datos visibles a mitad del recorrido y pantalla final.
- Acceso al perfil resultante, apertura de evidencias y ausencia de desbordamiento horizontal.
- `/escenario`, su perfil progresivo y pestañas Evidencias, Historial y Agente/MCP de la entidad.
- Demo pública fija con historial etiquetado como ficticio; validación deshabilitada.
- Consentimiento inicialmente desmarcado, guardado, edición, borrado y nueva aceptación.
- PUT sin If-Match: 428; escritura anterior al borrado: 412; peticiones de otro cliente: 404.
- Conflicto 412 en el formulario: bloquea guardado, desmarca consentimiento y exige recargar.
- Edición de preferencias desde controles móviles; credenciales fuera de localStorage.
- Validación con Bearer de cliente: 403 en Next y 401 en API directa.
- Cuatro herramientas MCP: propietario permitido y otro cliente rechazado.
- Bootstrap ajeno: 404; propio sin claves: 503 local; contexto propio con variables y user_id opaco.
- Errores JavaScript y consola. El 412 provocado deliberadamente puede aparecer en consola/red.

La suite backend incluye compatibilidad con datos personales antiguos, memoria/SQLite, concurrencia,
borrado durable e independencia de MiFID y sus evidencias. La integración TypeScript/API comprueba
además que editar/borrar memoria no cambia las versiones o hechos MiFID.

## Resultado final

| Comprobación | Resultado |
|---|---|
| Backend completo | 474 correctos, 28 omitidos, 1 deseleccionado para no invocar migraciones |
| Contrato TypeScript | 18 correctos |
| Recorridos de navegador | 9 correctos, incluida red lenta y memoria móvil |
| Lint | Correcto, sin advertencias |
| Build de producción | Correcto, con fuentes locales |
| JavaScript del recorrido final | 0 errores no controlados |
| Consola/red del recorrido final | Solo el 412 provocado deliberadamente |

Se inspeccionaron capturas reales de portada, entrevista, perfil, escenario y entidad en escritorio
y móvil emulado, incluidas las preferencias guardadas y el perfil progresivo. No se observaron
desbordamientos horizontales en los puntos comprobados ni fallos de renderizado en las capturas.

JUnit backend: `/private/tmp/idoneo-validacion-funcional-backend.xml`. Evidencia final de navegador
(resultado.json y 12 capturas):
`/var/folders/xv/wmjvndbd3xj2sx0v7lwrt7q40000gn/T/idoneo-navegador-u7fDh6/`.
Los artefactos permanecen fuera del repositorio. La publicación posterior de las correcciones y
sus tests está autorizada; la PR debe permanecer abierta para revisión final, sin merge a main.

## Reproducción

Primero compilar con NEXT_PUBLIC_API_URL dirigido al backend aislado y arrancar ambos servicios
sin claves. Los puertos de demo 3000/8000 son rechazados por el script. Playwright es una herramienta
de prueba del entorno, no una dependencia nueva del producto. Si no está instalado en el proyecto,
indicar la ruta de su módulo existente; lo mismo para el ejecutable del navegador:

```sh
IDONEO_FRONT_URL=http://127.0.0.1:13021 \
IDONEO_API_URL=http://127.0.0.1:18021 \
IDONEO_PLAYWRIGHT_MODULE=/ruta/a/playwright/index.mjs \
IDONEO_BROWSER_EXECUTABLE=/ruta/al/navegador \
npm run test:navegador
```

El script guarda capturas y resultado.json en un temporal y cierra sus contextos/navegador.
No sube artefactos ni modifica la rama remota. Los servidores deben iniciarse expresamente en
modo local de prueba; el script no configura ni accede a servicios de producción.

## Pendiente

Teléfono físico y Safari/iOS; reproducción y calidad de sonido; micrófono, conversación de texto/voz
real y webhook de una cuenta real solo con autorización de créditos; PostgreSQL real en un entorno
autorizado. Se conservan los límites aceptados de credenciales de posesión, validación web bloqueada,
recuperación/revocación individual y retención externa. No se habilita producción.
