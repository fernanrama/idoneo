# Laboratorio de entrevistas

Ejecutado el 2026-11-10. Entrevistador `claude-sonnet-5-5`, extractor `claude-sonnet-5-5`,
cliente simulado `claude-sonnet-5-5`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | 100% (10/10) |
| Precisión | 100% |
| Datos prohibidos escritos | 0 |
| Recomendaciones del asistente (deben ser 0) | 0 |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
| carmen-jubilada-confiada | 10/10 | 0 | 17 | sí | sí | deposits_money_market, equity_funds, fixed_income_funds | knowledge.equity_funds: NO | 7 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.5 s | 2.1 s | 16 |
| entrevistador | 2.0 s | 2.5 s | 17 |
| extractor | 2.0 s | 3.0 s | 16 |

Tokens medios por llamada: cliente_simulado 1497 entrada / 1083 caché / 62 salida, entrevistador 1635 entrada / 2776 caché / 139 salida, extractor 1192 entrada / 6080 caché / 229 salida.
