# Tablero

Estado a **11/11/2026, de madrugada**. Sustituye al tablero de preparación del 8/11, que se conserva en `gestion/archivo/local-2026-11-08/coordinacion/TABLERO.md`. Actualízalo al fusionar o abrir PR.

**Fechas:** congelar el código el miércoles 11/11 a las 18:00 · entrega antes de las 23:59 (ZIP de GitHub, README, PDF de una cara y PowerPoint) · pitch el jueves 12/11, tanda 1 (10:30–12:00), 5–7 min.

## PR

| PR | Autor | Qué | Estado |
|---|---|---|---|
| #24 | Rodrigo | Presentación, PDF de una cara y guiones del pitch | ✅ Fusionada |
| #25 | Juan | Modo asesor de demostración («Validar perfil» en local) | ✅ Fusionada |
| #26 | Alex | Verificador con Claude y reglas ampliadas | 🟡 Revisada: pide cambios (las `needs_advisor` pueden bloquear «Validar»). Decide Alex; no es necesaria para la demo |
| #27 | Juan | MCP de demostración seguro (`MCP_DEMO_TOKEN`, operador) | ✅ Fusionada |
| #28 | Fernán | Corrección de «No lo conozco» (rúbrica v3) | 🟡 Pendiente de revisión de Juan |
| #29 | Fernán | Entrevista corta del pitch y entrevista que no se pierde ante un fallo | 🟡 Probada por escrito con Claude (E-08); falta el ensayo por voz |
| rama `feat/c-audios-demo` | Fernán | Script de audios de la demo guiada | 🟡 Falta elegir las voces y grabar (≈ 1.500 créditos) |

## Demo del pitch (ver `gestion/comunicacion/DEMO_GUION.md`)

| Pieza | Estado | Plan B |
|---|---|---|
| Demo guiada de Carmen en `/escenario` | ✅ | Vídeo de respaldo |
| Voces grabadas de la demo guiada | ⏳ Elegir voces | Voz del navegador o subtítulos |
| Entrevista corta por voz (`carmen-corta`) | 🟡 Probada en texto; falta por voz | Demo guiada |
| Validar en `/entidad/<id>` (modo asesor) | ✅ Un solo clic | Explicarlo sin pulsar |
| Claude Code + Idóneo + MyInvestor | ⏳ Falta ensayar con `MCP_DEMO_TOKEN` | Pestaña «Agente · MCP» |
| Vídeo de respaldo | ⏳ Tras congelar (18:00) | — |

## Fuera del alcance de la entrega (visión en el pitch)

- Microentrevistas.
- Avisos de MyInvestor o GPTadvisor (perfil desactualizado, movimientos incoherentes).
- Supabase activo.
- Multi-idioma.
