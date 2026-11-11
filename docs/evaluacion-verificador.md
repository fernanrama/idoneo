# Evaluación del verificador · 2026-11-10

DATOS SIMULADOS: casos de `backend/fixtures/verificacion/casos.json`.

- Modelo: `claude-sonnet-5-5`, esfuerzo `low`
- Casos bien: 21/24 · detección 83% · falsas alarmas 0
- Latencia por caso: mediana 1.9 s, p95 3.2 s

| Caso | Rep. | Bien | Detectadas | Falsas |
|---|---|---|---|---|
| 01-plazo-frente-a-liquidez | 1 | ✓ | 1/1 | 0 |
| 02-correccion-no-es-contradiccion | 1 | ✓ | 0/0 | 0 |
| 03-presion-de-terceros | 1 | ✓ | 1/1 | 0 |
| 04-quiere-saltarse-el-test | 1 | ✓ | 1/1 | 0 |
| 05-deudas-que-aparecen | 1 | ✗ | 0/1 | 0 |
| 06-ingresos-de-otra-persona | 1 | ✓ | 1/1 | 0 |
| 07-posible-vulnerabilidad | 1 | ✓ | 1/1 | 0 |
| 08-cliente-coherente | 1 | ✓ | 0/0 | 0 |
| 01-plazo-frente-a-liquidez | 2 | ✓ | 1/1 | 0 |
| 02-correccion-no-es-contradiccion | 2 | ✓ | 0/0 | 0 |
| 03-presion-de-terceros | 2 | ✓ | 1/1 | 0 |
| 04-quiere-saltarse-el-test | 2 | ✓ | 1/1 | 0 |
| 05-deudas-que-aparecen | 2 | ✗ | 0/1 | 0 |
| 06-ingresos-de-otra-persona | 2 | ✓ | 1/1 | 0 |
| 07-posible-vulnerabilidad | 2 | ✓ | 1/1 | 0 |
| 08-cliente-coherente | 2 | ✓ | 0/0 | 0 |
| 01-plazo-frente-a-liquidez | 3 | ✓ | 1/1 | 0 |
| 02-correccion-no-es-contradiccion | 3 | ✓ | 0/0 | 0 |
| 03-presion-de-terceros | 3 | ✓ | 1/1 | 0 |
| 04-quiere-saltarse-el-test | 3 | ✓ | 1/1 | 0 |
| 05-deudas-que-aparecen | 3 | ✗ | 0/1 | 0 |
| 06-ingresos-de-otra-persona | 3 | ✓ | 1/1 | 0 |
| 07-posible-vulnerabilidad | 3 | ✓ | 1/1 | 0 |
| 08-cliente-coherente | 3 | ✓ | 0/0 | 0 |
