# Laboratorio de entrevistas

Ejecutado el 2026-11-10. Entrevistador `claude-sonnet-5-5`, extractor `claude-sonnet-5-5`,
cliente simulado `claude-sonnet-5-5`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | 90% (9/10) |
| Precisión | 90% |
| Datos prohibidos escritos | 0 |
| Recomendaciones del asistente (deben ser 0) | 0 |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
| carmen-jubilada-confiada | 9/10 | 0 | 20 | sí | sí | deposits_money_market, equity_funds | knowledge.equity_funds: sí | 1 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.7 s | 2.5 s | 19 |
| entrevistador | 1.8 s | 2.7 s | 20 |
| extractor | 2.2 s | 3.5 s | 19 |

Tokens medios por llamada: cliente_simulado 1537 entrada / 1094 caché / 54 salida, entrevistador 1640 entrada / 2934 caché / 130 salida, extractor 1123 entrada / 6258 caché / 262 salida.
