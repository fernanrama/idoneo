"""Pipeline de punta a punta: cliente de ejemplo → entrevista → perfil → entidad → MCP → trazas → evals.

Uso (desde backend/):

    python scripts/e2e.py                       # simulado: sin clave, guion y respuestas de Claude grabadas
    python scripts/e2e.py --real                # con ANTHROPIC_API_KEY: entrevistador, cliente y agentes reales
    python scripts/e2e.py --informe ../docs/evaluacion/e2e.md --json e2e.json
    python scripts/e2e.py --real --registrar    # guarda el resultado como evaluación «e2e»

Todo ocurre en este proceso, con un almacén en memoria y credenciales de un solo uso: no toca la base de
datos, ni la demo, ni ElevenLabs, ni MyInvestor. El paso a paso está en app/ops/e2e.py. Código de salida 1
si algún paso falla.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ["PERFIL_ALMACEN"] = "memoria"
os.environ["DATA_PERSIST"] = "0"
os.environ["DATABASE_URL"] = ""

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ.parent / ".env")
load_dotenv(RAIZ / ".env")

from app.ops import e2e, evaluaciones  # noqa: E402


def principal(a) -> int:
    modo = "real" if a.real else "simulado"
    if a.real and not os.getenv("ANTHROPIC_API_KEY", "").strip():
        print("El modo real necesita ANTHROPIC_API_KEY (en ../.env o en el entorno).")
        return 2
    informe = e2e.ejecutar(modo)
    print(f"\nPipeline de punta a punta · modo {modo} · {informe.cliente} → {informe.entidad}\n")
    for i, p in enumerate(informe.pasos, 1):
        print(f"{'✓' if p.ok else '✗'} {i}. {p.nombre}: {p.detalle}")
        for clave, valor in p.datos.items():
            if valor:
                print(f"     {clave}: {valor}")
    print(f"\n{'Todo bien' if informe.ok else 'HAY PASOS QUE FALLAN'} · {informe.duracion_s:.1f} s · "
          f"coste estimado {informe.coste_usd:.3f} $")
    if a.informe:
        a.informe.parent.mkdir(parents=True, exist_ok=True)
        a.informe.write_text(informe.markdown(), encoding="utf-8")
        print(f"Informe: {a.informe}")
    if a.json:
        a.json.write_text(json.dumps(informe.a_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    if a.registrar:
        filas = evaluaciones.registrar("e2e", informe.metricas(), prueba=a.prueba, modelo=modo,
                                       casos=len(informe.pasos), detalle=f"{informe.cliente} → {informe.entidad}")
        if not evaluaciones.imprimir_comprobaciones("e2e", filas):
            return 1
    return 0 if informe.ok else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--real", action="store_true", help="usa Claude de verdad (necesita ANTHROPIC_API_KEY)")
    p.add_argument("--informe", type=Path, help="escribe un informe en Markdown")
    p.add_argument("--json", type=Path, help="escribe el resultado en JSON")
    p.add_argument("--registrar", action="store_true",
                   help="guarda el resultado en app/ops/ultimas_evaluaciones.json y falla si no cumple los umbrales")
    p.add_argument("--prueba", default="manual", help="identificador de la ejecución")
    p.add_argument("--detalle", action="store_true", help="muestra los logs del backend")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO if args.detalle else logging.ERROR)
    sys.exit(principal(args))
