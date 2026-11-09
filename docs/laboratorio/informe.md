# Laboratorio de entrevistas

Ejecutado el 2026-11-09. Entrevistador `claude-sonnet-5-5`, extractor `claude-sonnet-5-5`,
cliente simulado `claude-sonnet-5-5`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | 100% (10/10) |
| Precisión | 91% |
| Datos prohibidos escritos | 1 |
| Recomendaciones del asistente (deben ser 0) | 0 |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
| carmen-jubilada-confiada | 10/10 | 1 | 23 | sí | sí | deposits_money_market, equity_funds, fixed_income_funds, mixed_funds, stocks | knowledge.equity_funds: sí | 4 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.4 s | 2.2 s | 22 |
| entrevistador | 1.7 s | 3.3 s | 23 |
| extractor | 2.0 s | 2.7 s | 22 |

Tokens medios por llamada: cliente_simulado 2068 entrada / 1102 caché / 59 salida, entrevistador 2151 entrada / 2142 caché / 142 salida, extractor 1285 entrada / 5512 caché / 249 salida.
