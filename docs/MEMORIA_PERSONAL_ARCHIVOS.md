# Inventario de la integración local de #21 y main

Rama de trabajo: `fix/perfil-memoria-atomicidad-propuesta`. HEAD de #21: `b1b182e`.
Integración local preparada con main `8b698b7`, sin commit ni publicación. Los conflictos de
README, página de perfil y hook se resolvieron manteniendo la interfaz actual.

La propuesta original de 55 archivos queda respaldada con SHA256 en
`/private/tmp/idoneo-pr21-respaldo-20261110-170247/` y en el stash local conservado.

Contrato y evidencia: [MEMORIA_PERSONAL_SEGURIDAD.md](MEMORIA_PERSONAL_SEGURIDAD.md).

## Diferencias respecto a main

Incluyen la aportación original de Pablo en #21 y las correcciones reutilizadas. No son todos
cambios nuevos de esta sesión. El harness original se conserva.

- [.env.example](../.env.example)
- [FLUJO_PRODUCTO_Y_AGENTES.md](../FLUJO_PRODUCTO_Y_AGENTES.md)
- [README.md](../README.md)
- [backend/app/acceso.py](../backend/app/acceso.py)
- [backend/app/agentes/README.md](../backend/app/agentes/README.md)
- [backend/app/agentes/chat.py](../backend/app/agentes/chat.py)
- [backend/app/agentes/memoria.py](../backend/app/agentes/memoria.py)
- [backend/app/agentes/prompts/entrevistador.md](../backend/app/agentes/prompts/entrevistador.md)
- [backend/app/main.py](../backend/app/main.py)
- [backend/app/mcp/servidor.py](../backend/app/mcp/servidor.py)
- [backend/app/perfil/almacenes/base.py](../backend/app/perfil/almacenes/base.py)
- [backend/app/perfil/almacenes/bd.py](../backend/app/perfil/almacenes/bd.py)
- [backend/app/perfil/almacenes/memoria.py](../backend/app/perfil/almacenes/memoria.py)
- [backend/app/perfil/personal.py](../backend/app/perfil/personal.py)
- [backend/app/perfil/store.py](../backend/app/perfil/store.py)
- [backend/app/voz.py](../backend/app/voz.py)
- [backend/scripts/sincronizar_voz.py](../backend/scripts/sincronizar_voz.py)
- [backend/tests/MEMORIA_PERSONAL_CONTRATO_PENDIENTE.md](../backend/tests/MEMORIA_PERSONAL_CONTRATO_PENDIENTE.md)
- [backend/tests/conftest.py](../backend/tests/conftest.py)
- [backend/tests/soporte_acceso.py](../backend/tests/soporte_acceso.py)
- [backend/tests/test_api.py](../backend/tests/test_api.py)
- [backend/tests/test_api_seguridad.py](../backend/tests/test_api_seguridad.py)
- [backend/tests/test_autorizacion_personal.py](../backend/tests/test_autorizacion_personal.py)
- [backend/tests/test_calculos_obsoletos.py](../backend/tests/test_calculos_obsoletos.py)
- [backend/tests/test_chat.py](../backend/tests/test_chat.py)
- [backend/tests/test_cliente_front_integracion.py](../backend/tests/test_cliente_front_integracion.py)
- [backend/tests/test_extractor.py](../backend/tests/test_extractor.py)
- [backend/tests/test_extractor_casos.py](../backend/tests/test_extractor_casos.py)
- [backend/tests/test_mcp.py](../backend/tests/test_mcp.py)
- [backend/tests/test_memoria_agente.py](../backend/tests/test_memoria_agente.py)
- [backend/tests/test_memoria_personal_reproduccion.py](../backend/tests/test_memoria_personal_reproduccion.py)
- [backend/tests/test_persistencia_bd.py](../backend/tests/test_persistencia_bd.py)
- [backend/tests/test_personal_transacciones.py](../backend/tests/test_personal_transacciones.py)
- [backend/tests/test_procesamiento_turnos.py](../backend/tests/test_procesamiento_turnos.py)
- [backend/tests/test_reinicio_servidor.py](../backend/tests/test_reinicio_servidor.py)
- [backend/tests/test_sincronizar_voz.py](../backend/tests/test_sincronizar_voz.py)
- [backend/tests/test_store_contrato.py](../backend/tests/test_store_contrato.py)
- [backend/tests/test_validar_atomicidad.py](../backend/tests/test_validar_atomicidad.py)
- [backend/tests/test_voz_memoria.py](../backend/tests/test_voz_memoria.py)
- [docs/CONTRATOS.md](../docs/CONTRATOS.md)
- [docs/MEMORIA_PERSONAL_ARCHIVOS.md](../docs/MEMORIA_PERSONAL_ARCHIVOS.md)
- [docs/MEMORIA_PERSONAL_SEGURIDAD.md](../docs/MEMORIA_PERSONAL_SEGURIDAD.md)
- [docs/claude-extractor-review.md](../docs/claude-extractor-review.md)
- [docs/diagrams/memoria-agente-workflow.png](../docs/diagrams/memoria-agente-workflow.png)
- [docs/diagrams/memoria-agente-workflow.svg](../docs/diagrams/memoria-agente-workflow.svg)
- [docs/diagrams/memoria-agente-workflow.vega.json](../docs/diagrams/memoria-agente-workflow.vega.json)
- [docs/research/MEMORIA_AGENTE_ELEVENLABS.md](../docs/research/MEMORIA_AGENTE_ELEVENLABS.md)
- [frontend/.env.example](../frontend/.env.example)
- [frontend/README.md](../frontend/README.md)
- [frontend/package.json](../frontend/package.json)
- [frontend/scripts/test-contrato.mjs](../frontend/scripts/test-contrato.mjs)
- [frontend/scripts/test-integracion-local.mjs](../frontend/scripts/test-integracion-local.mjs)
- [frontend/scripts/verificar-main.mjs](../frontend/scripts/verificar-main.mjs)
- [frontend/src/app/api/entidad/[cid]/validar/route.ts](../frontend/src/app/api/entidad/[cid]/validar/route.ts)
- [frontend/src/app/api/entidad/reset/route.ts](../frontend/src/app/api/entidad/reset/route.ts)
- [frontend/src/app/entidad/[cid]/VistaEntidad.tsx](../frontend/src/app/entidad/[cid]/VistaEntidad.tsx)
- [frontend/src/components/memoria-personal.module.css](../frontend/src/components/memoria-personal.module.css)
- [frontend/src/components/memoria-personal.tsx](../frontend/src/components/memoria-personal.tsx)
- [frontend/src/lib/api.ts](../frontend/src/lib/api.ts)
- [frontend/src/lib/credenciales.ts](../frontend/src/lib/credenciales.ts)
- [frontend/src/lib/iniciarVoz.ts](../frontend/src/lib/iniciarVoz.ts)
- [frontend/src/lib/onboarding.tsx](../frontend/src/lib/onboarding.tsx)
- [frontend/src/lib/servidor/entidad.ts](../frontend/src/lib/servidor/entidad.ts)
- [frontend/src/lib/tipos.ts](../frontend/src/lib/tipos.ts)
- [frontend/src/lib/useEntrevista.ts](../frontend/src/lib/useEntrevista.ts)
- [frontend/tests/contrato-cliente.mjs](../frontend/tests/contrato-cliente.mjs)
- [gestion/coordinacion/areas/03-producto.md](../gestion/coordinacion/areas/03-producto.md)

## Archivos incorporados de main sin cambios respecto a él

Estos archivos forman parte de la integración de #22/#23, no de la corrección de memoria.

- `frontend/public/demo/carmen/manifest.json`
- `frontend/src/app/_portada/AuraPreguntas.tsx`
- `frontend/src/app/_portada/Historia.tsx`
- `frontend/src/app/_portada/historia.module.css`
- `frontend/src/app/_portada/portada.module.css`
- `frontend/src/app/entidad/[cid]/entidad.module.css`
- `frontend/src/app/escenario/VistaEscenario.tsx`
- `frontend/src/app/escenario/escenario.module.css`
- `frontend/src/app/escenario/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/onboarding/entrevista/page.tsx`
- `frontend/src/app/onboarding/page.tsx`
- `frontend/src/app/onboarding/perfil/page.tsx`
- `frontend/src/app/onboarding/productos/page.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/components/BarraCliente.tsx`
- `frontend/src/components/Entrevista.tsx`
- `frontend/src/components/Esfera3D.tsx`
- `frontend/src/components/Formas.tsx`
- `frontend/src/components/PanelVivo.tsx`
- `frontend/src/components/Revela.tsx`
- `frontend/src/components/cliente.module.css`
- `frontend/src/components/entrevista.module.css`
- `frontend/src/components/formas.module.css`
- `frontend/src/components/panel.module.css`
- `frontend/src/components/ui.module.css`
- `frontend/src/components/ui.tsx`
- `frontend/src/components/visual.module.css`
- `frontend/src/components/visual.tsx`
- `frontend/src/lib/demo.ts`
- `frontend/src/lib/guion-carmen.json`
- `frontend/src/lib/guion.ts`
- `frontend/src/lib/usePerfil.ts`
- `frontend/src/tema/visual.css`
