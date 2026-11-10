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
| carmen-jubilada-confiada | 10/10 | 0 | 16 | sí | sí | deposits_money_market, equity_funds, fixed_income_funds | knowledge.equity_funds: sí | 0 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.6 s | 2.0 s | 15 |
| entrevistador | 1.8 s | 2.6 s | 16 |
| extractor | 2.1 s | 3.3 s | 15 |

Tokens medios por llamada: cliente_simulado 1360 entrada / 1078 caché / 61 salida, entrevistador 1453 entrada / 2970 caché / 131 salida, extractor 1170 entrada / 6420 caché / 251 salida.
