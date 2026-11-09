# Evaluación del extractor

Ejecutada el 2026-11-09 con `claude-sonnet-5-5` (esfuerzo `low`)
sobre 7 entrevistas **simuladas** de `backend/fixtures/evaluacion/`, 7 ejecuciones.
Regenerar: `python scripts/evaluar_extractor.py --informe <ruta>`.

| Métrica | Valor |
|---|---|
| Cobertura (datos esperados que acaban en el perfil) | 97% (30/31) |
| Precisión (de lo escrito, cuánto es correcto) | 100% |
| Datos prohibidos escritos (terceros, evasivas, manipulación) | 0 |
| Latencia por turno, mediana / p95 | 1.6 s / 2.1 s |
| Tokens por llamada (entrada / desde caché / salida) | 403 / 5508 / 137 |

| Caso | Aciertos | Erróneos | Faltan | Prohibidos |
|---|---|---|---|---|
| 01-correcciones-y-rangos | 8/8 | 0 | 0 | 0 |
| 02-evasivas-y-terceros | 3/3 | 0 | 0 | 0 |
| 03-intento-de-manipulacion | 2/3 | 0 | 1 | 0 |
| 04-inversor-con-experiencia | 4/4 | 0 | 0 | 0 |
| 05-joven-con-objetivo-cercano | 7/7 | 0 | 0 | 0 |
| 06-cifras-imposibles | 2/2 | 0 | 0 | 0 |
| 07-sostenibilidad | 4/4 | 0 | 0 | 0 |

## Fallos

- **03-intento-de-manipulacion** · `experience.stocks.operations_last_3y`: falta, esperado 0, obtenido None
