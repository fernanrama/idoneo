"""Umbrales de calidad y registro de evaluaciones (app/ops/evaluaciones.py, GET /api/ops/evals)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from app.ops import evaluaciones


def test_min_y_max():
    filas = {f["metrica"]: f for f in evaluaciones.comprobar(
        "extractor", {"cobertura": 0.9, "precision": 1.0, "prohibidos": 1})}
    assert not filas["cobertura"]["ok"] and filas["precision"]["ok"] and not filas["prohibidos"]["ok"]
    assert not filas["latencia_p95_s"]["ok"]  # una métrica que falta no cumple


def test_registrar_guarda_y_comprueba(tmp_path):
    ruta = tmp_path / "ultimas.json"
    filas = evaluaciones.registrar("verificador", {"deteccion": 0.9, "falsas_alarmas": 0, "latencia_p95_s": 2.0},
                                   prueba="ci-1", modelo="m", casos=8, ruta=ruta)
    assert all(f["ok"] for f in filas)
    d = json.loads(ruta.read_text("utf-8"))
    assert d["verificador"]["prueba"] == "ci-1" and d["verificador"]["metricas"]["deteccion"] == 0.9


def test_las_evaluaciones_registradas_cumplen_sus_umbrales():
    e = TestClient(app).get("/api/ops/evals").json()
    for nombre in ("extractor", "verificador", "laboratorio"):
        c = e["componentes"][nombre]
        assert c["ejecutada"] and c["ok"], (nombre, c["comprobaciones"])
    assert e["componentes"]["juez"]["ejecutada"] in (True, False)
