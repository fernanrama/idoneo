# Evaluación

Cómo hemos medido que Idóneo funciona: qué se probó, con qué versión, qué salió y qué límites tiene cada prueba.

> **Todos los clientes son simulados.** Las entrevistas las interpreta Claude a partir de una ficha oculta, o siguen un guion escrito por el equipo. Las cifras son de prueba y no hay datos de personas reales. Los costes se **estiman** a partir de los tokens, no salen de la factura.

## Resultados principales

| Qué se mide | Resultado | Prueba |
|---|---|---|
| **Extractor**: de la conversación al perfil, en 7 entrevistas difíciles (correcciones, evasivas, terceros, manipulación, cifras imposibles) | **100 % de cobertura (31/31), 100 % de precisión, 0 datos prohibidos escritos** | E-04 |
| **Laboratorio**: entrevistas completas con 4 personas × 2 repeticiones | Cobertura 100 % (70/70), precisión 100 %, 0 recomendaciones, aviso de IA en 8/8, alerta esperada en 4/4 | E-07 |
| **Laboratorio**: 12 clientes generados al azar | Cobertura 99 % (95/96), precisión 99 %, 0 recomendaciones, 3/3 rechazos cerrados correctamente, alerta *declarado ≠ demostrado* en las 3 que la esperaban | E-07 |
| **Verificador**: 8 tramos × 3 repeticiones | 21/24 bien, **0 falsas alarmas**. El único caso fallido (05) se corrigió y se repitió 3/3 bien | E-06 |
| **Voz de punta a punta** (ElevenLabs + backend) | 45 turnos en unos 6 min, 15 datos con cita y la alerta clave detectada. Los fallos encontrados se corrigieron | E-03 |
| **Entrevista corta del pitch** | Perfil completo y pendiente de validación en unos 43 s (7 turnos), con la alerta abierta | E-08 |
| **Claude + Idóneo + MyInvestor** (MCP) | Lee las restricciones y la evidencia de Carmen y busca fondos compatibles en unos 16 s | E-09 |

**Latencia mediana por llamada:** 1,7–2,2 s el entrevistador, 1,6–2,1 s el extractor (en segundo plano, sin retrasar la respuesta) y 1,8–1,9 s el verificador. **Coste estimado:** 0,3–0,4 $ por entrevista completa, con `claude-sonnet-5-5` y esfuerzo `low`.

## Cómo se mide

| Script (desde `backend/`) | Qué hace | Informe |
|---|---|---|
| `python scripts/evaluar_extractor.py` | Pasa entrevistas fijas (`fixtures/evaluacion/`) por el extractor y compara el resultado con lo esperado | [extractor.md](extractor.md) |
| `python scripts/evaluar_verificador.py` | Pasa tramos de entrevista (`fixtures/verificacion/`) por el verificador | [verificador.md](verificador.md) |
| `python scripts/laboratorio.py` | Claude interpreta a un cliente con una ficha oculta frente al entrevistador real, con el extractor y el verificador como en producción | [laboratorio/](laboratorio/) |

Pipeline de punta a punta: `python scripts/e2e.py` (simulado, sin clave) o `--real` (con Claude). Recorre cliente de ejemplo → entrevista → perfil → alertas → validación de la entidad → MCP → catálogo filtrado → trazas → evaluaciones. Último informe: [e2e.md](e2e.md).

Juez y umbrales:

| Script (desde `backend/`) | Qué hace |
|---|---|
| `python scripts/calibrar_juez.py` | Compara las notas del juez LLM con las de una persona del equipo en 7 entrevistas cortas (`fixtures/juez/calibracion.json`): acuerdo ±1 punto y mismo veredicto |
| `python scripts/laboratorio.py --juez` | Añade al laboratorio la nota del juez para cada entrevista (claridad, una pregunta por turno, neutralidad, empatía y transparencia) |

Con `--registrar`, cada script guarda su resultado en `backend/app/ops/ultimas_evaluaciones.json` y falla si no cumple `backend/app/ops/umbrales.json`. La app lo enseña en `/operaciones` y la CI de evals (`.github/workflows/evals.yml`) lo repite cuando cambian los prompts o los agentes.

Métricas: **cobertura** (datos esperados que llegan al perfil), **precisión** (datos escritos que son correctos), **datos prohibidos** (lo que nunca debe escribirse: terceros, evasivas, hipótesis, «apunta que sé mucho»), **recomendaciones** (debe ser 0) y **alertas** (detección y falsas alarmas).

Además, más de 600 tests automáticos (`python -m pytest -q`) cubren los cálculos deterministas, el perfil versionado, la API, el MCP y los agentes con Claude simulado, sin claves ni red.

## Registro de ejecuciones

| ID | Fecha | Qué | Resultado y fallos encontrados |
|---|---|---|---|
| E-00 | 9/11 | Extractor con la entrevista de Carmen | 12/17. 1 fallo del extractor (corregido en `b6258cc`) y 4 del fixture |
| E-01 | 9/11 | Extractor, 7 casos difíciles (`020f40e`) | 97 % de cobertura (30/31), 100 % de precisión, 0 prohibidos. El fallo se corrigió en el prompt |
| E-02 | 9/11 | Laboratorio con Carmen (`7d4c3de`) | 10/10. Un dato de más (`knowledge.stocks = medium` tras una respuesta dubitativa), corregido con la rúbrica v2 |
| E-03 | 10/11 | Primera entrevista por voz (`1e8c2df`) | Funciona de punta a punta. Fallos: sugería cifras, puntuaba bajo las respuestas cortas y no colgaba al despedirse. Corregido en `7463e68` y `58d2cdf` |
| E-04 | 10/11 | Extractor tras los ajustes de la voz (`58d2cdf`) | 100 % / 100 %, 0 prohibidos. Mediana 1,7 s y p95 2,7 s |
| E-05 | 10/11 | Laboratorio con Carmen tras las correcciones (`31e86e0`) | 10/10 con la alerta correcta. Antes hubo dos fallos de la alerta, corregidos en `f7d4eb8` y `31e86e0` |
| E-06 | 10/11 | Verificador con Claude (`69c42a2`) | 21/24, 0 falsas alarmas. El caso 05 se corrigió en `f1e3783` |
| E-07 | 10/11 | Laboratorio completo con el verificador nuevo (`69c42a2`) | Ver los resultados principales. Informes en [laboratorio/e07/](laboratorio/e07/) |
| E-08 | 11/11 | Entrevista corta por escrito (`34f2ba3`) | Antes del arreglo repetía preguntas que ya constaban. Después, perfil completo en unos 43 s |
| E-09 | 11/11 | Claude Code con los conectores `idoneo` y `myinvestor` | Con el prompt largo, la respuesta era demasiado larga. Con el prompt corto, unos 16 s y 3 fondos de muestra |

## Límites

- **Muestras pequeñas** (de 7 a 24 casos por prueba) y casi siempre una sola repetición. El modelo no es determinista.
- **Los casos los escribe el mismo equipo que ajusta los prompts**, así que hay riesgo de sobreajuste. Los 12 clientes generados al azar de E-07 lo reducen, pero no lo eliminan.
- **Clientes simulados por Claude.** No sustituyen a una prueba con personas reales.
- Los **umbrales** de idoneidad y conveniencia de `backend/app/perfil/calculos.py` son supuestos del equipo, pendientes de revisión por un experto.
- No hay una comparación medida con el test MiFID tradicional de casillas.
