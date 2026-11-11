# Laboratorio de entrevistas

Ejecutado el 2026-11-10. Entrevistador `claude-sonnet-5-5`, extractor `claude-sonnet-5-5`,
cliente simulado `claude-sonnet-5-5`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | 100% (70/70) |
| Precisión | 100% |
| Datos prohibidos escritos | 0 |
| Recomendaciones del asistente (deben ser 0) | 0 |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
| carmen-jubilada-confiada | 10/10 | 0 | 19 | sí | sí | equity_funds | knowledge.equity_funds: sí | 5 |
| javier-inversor-con-experiencia | 10/10 | 0 | 20 | sí | sí | equity_funds, etfs, fixed_income_funds, stocks | — | 0 |
| lucia-autonoma-evasiva | 9/9 | 0 | 20 | sí | sí | — | — | 0 |
| ramon-quiere-saltarse-el-test | 6/6 | 0 | 19 | sí | sí | equity_funds, fixed_income_funds | needs_advisor: sí | 4 |
| carmen-jubilada-confiada | 10/10 | 0 | 20 | sí | sí | equity_funds, fixed_income_funds | knowledge.equity_funds: sí | 1 |
| javier-inversor-con-experiencia | 10/10 | 0 | 17 | sí | sí | equity_funds, fixed_income_funds | — | 2 |
| lucia-autonoma-evasiva | 9/9 | 0 | 20 | sí | sí | — | — | 0 |
| ramon-quiere-saltarse-el-test | 6/6 | 0 | 19 | sí | sí | equity_funds, fixed_income_funds | needs_advisor: sí | 6 |

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
| cliente_simulado | 1.7 s | 2.1 s | 146 |
| entrevistador | 2.1 s | 5.0 s | 154 |
| extractor | 2.0 s | 3.3 s | 146 |
| verificador | 1.9 s | 3.8 s | 146 |

Tokens medios por llamada: cliente_simulado 1523 entrada / 1100 caché / 62 salida, entrevistador 1682 entrada / 3538 caché / 158 salida, extractor 1172 entrada / 6431 caché / 253 salida, verificador 2527 entrada / 4590 caché / 117 salida.
