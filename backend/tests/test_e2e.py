"""El pipeline de punta a punta en modo simulado (app/ops/e2e.py): cliente → perfil → entidad → MCP → trazas."""

from __future__ import annotations

from app.ops import e2e


def test_el_producto_entero_funciona_de_punta_a_punta(monkeypatch):
    informe = e2e.ejecutar("simulado", parchear=monkeypatch.setattr, fijar_entorno=monkeypatch.setenv)
    fallos = [f"{p.nombre}: {p.detalle}" for p in informe.pasos if not p.ok]
    assert not fallos, fallos
    assert [p.nombre for p in informe.pasos][0] == "Alta del cliente" and len(informe.pasos) == 9
    mcp = next(p for p in informe.pasos if p.nombre == "Agente de la entidad por MCP")
    # Dice saber mucho de renta variable y falla la comprobación: el banco no puede ofrecerle ese fondo.
    assert "BE-RVG" in mcp.datos["descartados"] and "not_appropriate" in mcp.datos["descartados"]["BE-RVG"]
    assert informe.metricas()["pasos_ok"] == 1.0
    assert "| 9 | Métricas y evaluaciones | ✓ |" in informe.markdown()


def test_el_catalogo_se_filtra_con_cada_restriccion():
    restr = {"usable": True, "blocked_searches": ["etfs"], "appropriateness": {"fixed_income_funds": "appropriate"},
             "funds_query": {"max_risk": 3, "asset_type": ["Renta Fija"], "currency": "EUR"},
             "post_filters": [{"field": "min_initial", "op": "<=", "value": 1000}]}
    base = {"tipo": "funds", "familia": "fixed_income_funds", "asset_type": "Renta Fija", "sri": 2, "currency": "EUR",
            "min_initial": 100}
    catalogo = [{"id": "ok", **base}, {"id": "sri", **base, "sri": 5}, {"id": "etf", **base, "tipo": "etfs"},
                {"id": "min", **base, "min_initial": 5000}, {"id": "usd", **base, "currency": "USD"},
                {"id": "fam", **base, "familia": "equity_funds"}]
    admitidos, descartados = e2e._filtrar_catalogo(restr, catalogo)
    assert admitidos == ["ok"] and set(descartados) == {"sri", "etf", "min", "usd", "fam"}
    assert e2e._filtrar_catalogo({**restr, "usable": False}, catalogo)[0] == []
