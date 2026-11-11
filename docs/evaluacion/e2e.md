# Pipeline de punta a punta · modo simulado

DATOS SIMULADOS: cliente, entidad y catálogo ficticios.

- Cliente: Lucía (ficticia)
- Entidad: Banco Ejemplo (ficticio)
- Resultado: **todo bien** (9/9 pasos)
- Duración: 0.2 s · coste estimado: 0.000 $

| # | Paso | Bien | Detalle | Tiempo |
|---|---|---|---|---|
| 1 | Alta del cliente | ✓ | cliente cliente-482dccc8… con sesión de texto y credencial propia | 0.03 s |
| 2 | Entrevista | ✓ | 25 turnos (12 del cliente), 0 rechazos del procesamiento | 0.18 s |
| 3 | Perfil completo y con pruebas | ✓ | estado pending_validation, 17 datos, faltan ninguno, sin cita literal ninguno | 0.01 s |
| 4 | Alertas para el asesor | ✓ | 1 abiertas; esperadas ['knowledge.equity_funds']: todas | 0.00 s |
| 5 | Restricciones antes de validar | ✓ | usable=False: el agente de la entidad aún no puede recomendar nada | 0.01 s |
| 6 | Validación por la entidad | ✓ | asesora-ejemplo valida la versión 15 → active | 0.01 s |
| 7 | Agente de la entidad por MCP | ✓ | usable, SRI máximo 4, 2 de 8 productos del catálogo admitidos | 0.00 s |
| 8 | Trazas de la sesión | ✓ | 12 turnos procesados con extractor, verificador; sin texto del cliente | 0.01 s |
| 9 | Métricas y evaluaciones | ✓ | 24 llamadas trazadas; evaluaciones que cumplen: 3/3 | 0.01 s |
