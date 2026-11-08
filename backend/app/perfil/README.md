# Perfil (rol A) · núcleo del contrato 04

Estado: **borrador** del contrato [04](../../../docs/proyecto/04_CONTRATO_PERFIL.md). Convive con el v0
(`modelos.py`, `store.py`, `calculos.py`), que sigue sirviendo la API actual hasta coordinar el cambio
con front (Fernán) y agentes (Hammad, Pablo).

```
dominio/        sin E/S: modelos, esquema de rutas, supuestos, cálculos, evaluaciones,
                restricciones (formato MyInvestor) y máquina de estados
persistencia/   tablas (SQLAlchemy), motor (Postgres/Supabase o SQLite), repositorio de solo añadir,
                aplicador de migraciones
servicios/      perfiles (única puerta de escritura), sesiones y bus de eventos
../../migraciones/  SQL numerado para Postgres/Supabase
```

## Reglas que garantiza el código

- Nada se sobrescribe: cada cambio es una versión nueva con motivo y autor. La base bloquea `UPDATE` y
  `DELETE` en `profile_versions` y `turns` (también para el rol `postgres`).
- Los números los calculan funciones deterministas; un agente no puede escribir un dato calculado.
- Un dato sacado de la conversación (`agent:*`) necesita evidencia.
- Solo `active` (validado por una persona) es usable para recomendar.
- La capa personal está aparte y se puede borrar (RGPD) sin tocar el registro MiFID.
- Todos los supuestos del equipo están en `dominio/supuestos.py`.

## Base de datos

- Sin `DATABASE_URL`: SQLite local en `backend/data/` (se crea sola).
- Con `DATABASE_URL` de Supabase: hay que aplicar antes las migraciones.

```bash
cd backend
python -m app.perfil.persistencia.migrar            # plan: no cambia nada
python -m app.perfil.persistencia.migrar --aplicar  # aplica (con autorización del responsable)
```

## Tests

```bash
cd backend && python -m pytest -q
```

Para repetirlos también contra un Postgres **local y desechable** (nunca Supabase: se borra entero):
`TEST_POSTGRES_URL=postgresql://usuario@127.0.0.1:5432/perfil_test python -m pytest -q`
