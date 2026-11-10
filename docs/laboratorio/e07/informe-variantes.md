# Laboratorio de entrevistas

Ejecutado el 2026-11-10. Entrevistador `claude-sonnet-5-5`, extractor `claude-sonnet-5-5`,
cliente simulado `claude-sonnet-5-5`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | 99% (95/96) |
| Precisión | 99% |
| Datos prohibidos escritos | 0 |
| Recomendaciones del asistente (deben ser 0) | 0 |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
| v001-nuria-no-acepta | 0/0 | 0 | 2 | sí | sí | — | — | 12 |
| v002-andrés-no-acepta | 0/0 | 0 | 2 | sí | sí | — | — | 12 |
| v003-lola-37 | 11/11 | 0 | 20 | sí | sí | equity_funds | — | 7 |
| v004-rosa-42 | 11/11 | 0 | 17 | sí | sí | deposits_money_market, equity_funds | knowledge.equity_funds: sí | 3 |
| v005-antonio-74 | 10/10 | 0 | 20 | sí | sí | — | — | 1 |
| v006-nuria-no-acepta | 0/0 | 0 | 2 | sí | sí | — | — | 12 |
| v007-marta-72 | 10/11 | 0 | 14 | sí | sí | equity_funds | — | 0 |
| v008-luis-70 | 11/11 | 0 | 17 | sí | sí | equity_funds | — | 1 |
| v009-rosa-71 | 11/11 | 0 | 16 | sí | sí | equity_funds | knowledge.equity_funds: sí | 2 |
| v010-inés-38 | 9/9 | 0 | 26 | sí | sí | — | — | 0 |
| v011-luis-53 | 11/11 | 0 | 26 | sí | sí | equity_funds, fixed_income_funds | — | 0 |
| v012-íñigo-25 | 11/11 | 0 | 19 | sí | sí | equity_funds, fixed_income_funds | knowledge.equity_funds: sí | 1 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.7 s | 2.5 s | 169 |
| entrevistador | 2.2 s | 4.7 s | 181 |
| extractor | 1.8 s | 3.3 s | 169 |
| verificador | 1.8 s | 3.1 s | 169 |

Tokens medios por llamada: cliente_simulado 1743 entrada / 1044 caché / 78 salida, entrevistador 1847 entrada / 3538 caché / 154 salida, extractor 1159 entrada / 6431 caché / 203 salida, verificador 2395 entrada / 4590 caché / 102 salida.
