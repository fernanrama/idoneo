"""Calibra el juez LLM contra las notas de una persona (fixtures/juez/calibracion.json).

Uso (desde backend/, con ANTHROPIC_API_KEY en ../.env o en el entorno):

    python scripts/calibrar_juez.py
    python scripts/calibrar_juez.py --repeticiones 3 --registrar

Un juez que no coincide con el criterio humano no sirve para nada, por muy convincente que suene. Este
script pasa 7 entrevistas cortas escritas por el equipo (buena, recomienda un fondo, jerga, presión,
no dice que es una IA, rechaza recomendar bien, intento de manipular al juez) y compara cada nota.

- Acuerdo: notas en las que el juez se desvía como mucho 1 punto de la persona.
- Veredicto: casos con el mismo aprobado o suspenso.

Coste: una llamada a Claude por caso y repetición. Si el acuerdo baja del umbral, cambia la rúbrica
(app/agentes/prompts/juez.md) antes de usar sus notas en el laboratorio.
"""

from __future__ import annotations

import argparse
import asyncio
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

from app.agentes import claude, juez  # noqa: E402
from app.ops import evaluaciones  # noqa: E402
from app.perfil.modelos import Turno  # noqa: E402

FIXTURE = RAIZ / "fixtures" / "juez" / "calibracion.json"


def cargar() -> list[dict]:
    casos = json.loads(FIXTURE.read_text("utf-8"))["casos"]
    for c in casos:
        c["turnos"] = [Turno(**t, t_start=0, t_end=0) for t in c["turnos"]]
    return casos


async def principal(a) -> int:
    if not claude.disponible():
        print("Falta ANTHROPIC_API_KEY (en ../.env o en el entorno).")
        return 2
    pares = []
    for rep in range(a.repeticiones):
        for c in cargar():
            r = await juez.valorar(c["turnos"])
            pares.append((r, c["humano"], c["aprobada"]))
            difs = [f"{k} {r.notas.get(k, '—')}≠{h}" for k, h in c["humano"].items()
                    if r.notas.get(k) is None or abs(r.notas[k] - h) > 1]
            marca = "✓" if not difs and r.aprobada == c["aprobada"] else "✗"
            print(f"{marca} {c['nombre']} (rep. {rep + 1}) · juez {r.notas} · aprobada {r.aprobada} (persona {c['aprobada']})")
            for d in difs:
                print(f"   desacuerdo: {d}")
            if r.sin_prueba:
                print(f"   notas bajas sin cita comprobable: {', '.join(r.sin_prueba)}")
    m = juez.calibracion(pares)
    print(f"\nModelo: {claude.modelo(juez.AGENTE)} · rúbrica {juez.VERSION_RUBRICA}")
    print(f"Acuerdo ±1: {m['acuerdo']:.0%} · exacto: {m['exacto']:.0%} · mismo veredicto: {m['veredicto']:.0%}")
    if a.registrar:
        filas = evaluaciones.registrar("calibracion_juez", m, prueba=a.prueba, modelo=claude.modelo(juez.AGENTE),
                                       casos=len(pares), detalle=f"rúbrica {juez.VERSION_RUBRICA}, notas humanas del equipo")
        if not evaluaciones.imprimir_comprobaciones("calibracion_juez", filas):
            return 1
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repeticiones", type=int, default=1)
    p.add_argument("--registrar", action="store_true",
                   help="guarda el resultado en app/ops/ultimas_evaluaciones.json y falla si no cumple los umbrales")
    p.add_argument("--prueba", default="manual", help="identificador de la ejecución")
    p.add_argument("--detalle", action="store_true", help="muestra el log de cada llamada a Claude")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO if args.detalle else logging.WARNING)
    sys.exit(asyncio.run(principal(args)))
