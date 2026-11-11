# Perfil (rol A) · persistencia, versionado y validación del contrato 04

`store.py` es la puerta única del perfil. Su API pública es la de la PR #7 y la usan la API
(`main.py`), los agentes y el MCP. Por debajo, el almacén es intercambiable:

```
PERFIL_ALMACEN=memoria   (por defecto) en memoria, con volcado a JSON en backend/data/
PERFIL_ALMACEN=bd        base de datos: DATABASE_URL de Supabase (Postgres) o sqlite:///...
```

```
store.py          algoritmo de escritura (una vez para ambos almacenes) y estados
validacion.py     validación estricta de entrada: rutas, tipos, autoría, evidencia, marcas
personal.py       capa personal separada, con consentimiento propio (RGPD)
calculos.py       lógica financiera de la PR #7 (sin cambios): idoneidad, conveniencia, restricciones
modelos.py        modelos del contrato 04 (PR #7) + trazabilidad de alertas (opcional)
eventos.py        bus de eventos para el SSE del panel en vivo
almacenes/        memoria.py y bd.py, con la misma interfaz (base.py)
persistencia/     tablas, motor (Postgres/SQLite) y aplicador de migraciones
../../migraciones/  SQL numerado para Postgres/Supabase
```

## Garantías

- **Nada se sobrescribe.** Cada cambio es una versión nueva con motivo y autor. En base de datos, la
  propia base bloquea `UPDATE`, `DELETE` y `TRUNCATE` del registro y de la transcripción. El reinicio de
  la demo añade una versión (no borra el historial) y el consumidor deja de servir activos anteriores.
- **Validación estricta.** Rutas de `modelos.CAMPOS` con su tipo (422 si no); nadie escribe datos
  calculados (409); solo la entidad escribe `source=advisor`; un dato de un agente lleva evidencia.
- **Estados.** Se valida desde `draft`, `pending_validation` o `review_due` (D2: tras una microentrevista, sin
  otra entrevista completa); con `version_esperada`, solo si nadie ha escrito desde que la entidad lo revisó.
  Abrir una revisión del cliente no cambia el estado (R1). Al validar se cierran las alertas abiertas (regla de la PR #7) y queda quién lo hizo.
- **Capa personal aparte.** Se une al perfil al leerlo; sin consentimiento no se guarda nada; se puede
  borrar sin tocar el registro MiFID.
- **Concurrencia optimista**: si otra escritura (de este u otro proceso) se adelanta, se relee y reintenta.

## Seguridad de la API (main.py)

- `ADMIN_TOKEN`: si se define, `POST /validate` y `POST /api/demo/reset` exigen la cabecera
  `X-Admin-Token`. Sin definir (desarrollo), no se pide, para no romper el front.
- `DEMO_ENDPOINTS=0` desactiva `/api/demo/reset` (para un despliegue público).

## Base de datos

```bash
cd backend
D="--env-file ../.env --destino host:5432/base"          # destino explícito: nunca se lee el .env solo
python -m app.perfil.persistencia.verificar previo $D    # solo lectura
python -m app.perfil.persistencia.verificar ensayo $D    # aplica y deshace (ROLLBACK)
python -m app.perfil.persistencia.migrar $D              # plan: no cambia nada
python -m app.perfil.persistencia.migrar $D --aplicar    # aplica (con autorización del responsable)
python -m app.perfil.persistencia.verificar posterior $D --prueba-escritura
```

Procedimiento completo, qué esperar y qué hacer si falla: [backend/migraciones/README.md](../../migraciones/README.md).

## Tests

```bash
cd backend && python -m pytest -q
```

Los tests arrancan sin credenciales de pago ni red externa (`tests/aislamiento/`). Los de contrato (API, MCP
y store), validación, memoria personal y concurrencia entre procesos se repiten con cada almacén. Para añadir
un Postgres **local y desechable** (nunca Supabase; se vacía en cada test, debe llevar `test` en el nombre y
estar marcado: `COMMENT ON DATABASE perfil_test IS 'idoneo:base-desechable-de-pruebas'`):
`TEST_POSTGRES_URL=postgresql://usuario@127.0.0.1:5432/perfil_test python -m pytest -q`
