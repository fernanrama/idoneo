"""Resultados de las evaluaciones frente a sus umbrales de calidad.

- `ultimas_evaluaciones.json`: la última ejecución con la API real de cada evaluación (extractor, verificador,
  laboratorio, juez y calibración del juez). Lo escriben los scripts de `backend/scripts/` con `--registrar`.
- `umbrales.json`: lo mínimo (o máximo) aceptable para publicar una versión. La CI de evals falla si una
  métrica no los cumple, así una mejora en un sitio no puede romper otro sin que se vea.
"""

from __future__ import annotations

import json
import threading
from datetime import date
from pathlib import Path
from typing import Any

CARPETA = Path(__file__).resolve().parent
ULTIMAS = CARPETA / "ultimas_evaluaciones.json"
UMBRALES = CARPETA / "umbrales.json"
_candado = threading.Lock()


def _leer(ruta: Path) -> dict[str, Any]:
    try:
        return json.loads(ruta.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def umbrales() -> dict[str, Any]:
    return {k: v for k, v in _leer(UMBRALES).items() if not k.startswith("_")}


def comprobar(componente: str, metricas: dict[str, float]) -> list[dict[str, Any]]:
    """Una fila por umbral del componente: valor, límite y si lo cumple. Una métrica ausente no cumple."""
    filas = []
    for clave, regla in umbrales().get(componente, {}).items():
        valor = metricas.get(clave)
        if "min" in regla:
            ok = valor is not None and valor >= regla["min"]
            limite = {"tipo": "min", "valor": regla["min"]}
        else:
            ok = valor is not None and valor <= regla["max"]
            limite = {"tipo": "max", "valor": regla["max"]}
        filas.append({"metrica": clave, "etiqueta": regla.get("etiqueta", clave), "valor": valor,
                      "limite": limite, "ok": ok})
    return filas


def estado() -> dict[str, Any]:
    datos = {k: v for k, v in _leer(ULTIMAS).items() if not k.startswith("_")}
    componentes = {}
    for nombre in umbrales():
        d = datos.get(nombre)
        if d is None:
            componentes[nombre] = {"ejecutada": False, "comprobaciones": [], "ok": None}
            continue
        filas = comprobar(nombre, d.get("metricas", {}))
        componentes[nombre] = {**d, "ejecutada": True, "comprobaciones": filas, "ok": all(f["ok"] for f in filas)}
    hechas = [c for c in componentes.values() if c["ejecutada"]]
    return {
        "componentes": componentes,
        "ok": bool(hechas) and all(c["ok"] for c in hechas),
        "aviso": "Clientes simulados. Muestras pequeñas: cada evaluación indica cuántos casos tiene.",
    }


def registrar(componente: str, metricas: dict[str, float], *, prueba: str, modelo: str, casos: int,
              detalle: str = "", ruta: Path = ULTIMAS) -> list[dict[str, Any]]:
    """Guarda la ejecución como la última de `componente` y devuelve sus comprobaciones de umbral."""
    with _candado:
        datos = _leer(ruta)
        datos[componente] = {"prueba": prueba, "fecha": date.today().isoformat(), "modelo": modelo, "casos": casos,
                             "detalle": detalle, "metricas": {k: round(v, 4) if isinstance(v, float) else v
                                                              for k, v in metricas.items()}}
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return comprobar(componente, metricas)


def imprimir_comprobaciones(componente: str, filas: list[dict[str, Any]]) -> bool:
    """Imprime los umbrales de un componente y devuelve True si los cumple todos."""
    print(f"\nUmbrales de {componente}:")
    for f in filas:
        signo = "≥" if f["limite"]["tipo"] == "min" else "≤"
        print(f"  {'✓' if f['ok'] else '✗'} {f['etiqueta']}: {f['valor']} (debe ser {signo} {f['limite']['valor']})")
    return all(f["ok"] for f in filas)
