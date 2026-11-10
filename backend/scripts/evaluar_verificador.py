"""Evalúa el verificador con Claude real sobre tramos de entrevista difíciles (fixtures/verificacion/).

Uso (desde backend/, con ANTHROPIC_API_KEY en ../.env o en el entorno):

    python scripts/evaluar_verificador.py
    python scripts/evaluar_verificador.py --caso 05 --repeticiones 3
    python scripts/evaluar_verificador.py --informe ../docs/evaluacion-verificador.md

Ejecuta el verificador completo (reglas fijas + revisión con Claude) sobre el perfil y los turnos de cada
caso, sin extractor ni entrevistador, para medir solo al verificador. Imprime, por caso, las alertas
esperadas, las perdidas y las falsas alarmas, y al final detección, falsas alarmas, latencia y tokens.

Coste: una llamada a Claude por caso y repetición (8 casos). El código de salida es 1 si hay falsas alarmas.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import statistics
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ["PERFIL_ALMACEN"] = "memoria"
os.environ["DATA_PERSIST"] = "0"
os.environ["DATABASE_URL"] = ""

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ.parent / ".env")
load_dotenv(RAIZ / ".env")

from app.agentes import claude, verificador  # noqa: E402
from app.agentes import evaluacion_verificador as ev  # noqa: E402


def _alerta(a) -> str:
    return f"{a.flag.value} · {a.path or '—'} · {a.message}"


async def principal(args) -> int:
    if not claude.disponible():
        print("Falta ANTHROPIC_API_KEY (en ../.env o en el entorno).")
        return 2
    casos = [c for c in ev.casos() if not args.caso or c.nombre.startswith(args.caso)]
    if not casos:
        print("Ningún caso coincide.")
        return 2
    claude.reiniciar_metricas()
    resultados, latencias = [], []
    lineas_informe: list[str] = []
    for rep in range(1, args.repeticiones + 1):
        for caso in casos:
            inicio = time.perf_counter()
            alertas = await verificador.verificar(caso.perfil.model_copy(deep=True), caso.turnos, ev.SESION)
            latencias.append(time.perf_counter() - inicio)
            r = ev.puntuar(caso, alertas)
            resultados.append(r)
            marca = "✓" if r.ok else "✗"
            print(f"\n{marca} {caso.nombre} (rep. {rep}) — {caso.que_prueba}")
            for e in r.detectadas:
                print(f"   ✓ esperada {e.flag.value} en {e.rutas}")
            for e in r.perdidas:
                print(f"   · PERDIDA  {e.flag.value} en {e.rutas}")
            for a in r.falsas:
                print(f"   ‼ FALSA    {_alerta(a)}")
            for a in r.obtenidas:
                if a not in r.falsas:
                    print(f"     salió    {_alerta(a)}")
            lineas_informe.append(f"| {caso.nombre} | {rep} | {marca} | {len(r.detectadas)}/{len(r.detectadas) + len(r.perdidas)} | {len(r.falsas)} |")

    s = ev.resumen(resultados)
    m = claude.metricas().get("verificador", {})
    llamadas = int(m.get("llamadas", 0)) or 1
    mediana = statistics.median(latencias)
    p95 = sorted(latencias)[max(0, int(len(latencias) * 0.95) - 1)]
    print(f"\nModelo: {claude.modelo('verificador')} · esfuerzo {claude.esfuerzo('verificador', 'low')}")
    print(f"Casos bien: {s['casos_ok']}/{s['casos']} · detección {s['deteccion']:.0%} ({s['detectadas']}/{s['esperadas']})"
          f" · falsas alarmas {s['falsas_alarmas']}")
    print(f"Latencia por caso: mediana {mediana:.1f} s, p95 {p95:.1f} s · tokens por llamada:"
          f" entrada {m.get('tokens_entrada', 0) / llamadas:.0f} (caché {m.get('tokens_cache_leidos', 0) / llamadas:.0f}),"
          f" salida {m.get('tokens_salida', 0) / llamadas:.0f}")

    if args.informe:
        args.informe.write_text(
            f"# Evaluación del verificador · {date.today().isoformat()}\n\n"
            "DATOS SIMULADOS: casos de `backend/fixtures/verificacion/casos.json`.\n\n"
            f"- Modelo: `{claude.modelo('verificador')}`, esfuerzo `{claude.esfuerzo('verificador', 'low')}`\n"
            f"- Casos bien: {s['casos_ok']}/{s['casos']} · detección {s['deteccion']:.0%} · falsas alarmas {s['falsas_alarmas']}\n"
            f"- Latencia por caso: mediana {mediana:.1f} s, p95 {p95:.1f} s\n\n"
            "| Caso | Rep. | Bien | Detectadas | Falsas |\n|---|---|---|---|---|\n" + "\n".join(lineas_informe) + "\n",
            encoding="utf-8",
        )
        print(f"Informe: {args.informe}")
    return 1 if s["falsas_alarmas"] else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--caso", help="prefijo del caso (p. ej. 05)")
    p.add_argument("--repeticiones", type=int, default=1)
    p.add_argument("--informe", type=Path, help="escribe un informe en Markdown")
    p.add_argument("--detalle", action="store_true", help="muestra el log de cada llamada a Claude")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO if a.detalle else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(asyncio.run(principal(a)))
