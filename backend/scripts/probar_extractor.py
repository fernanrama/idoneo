"""Prueba el extractor con la API real de Claude sobre la entrevista simulada de Carmen.

Uso (desde backend/, con ANTHROPIC_API_KEY en ../.env o en el entorno):

    python scripts/probar_extractor.py
    python scripts/probar_extractor.py --entrevista fixtures/entrevistas/carmen-68.json --esperado fixtures/carmen-68.json

Reproduce el flujo real: cada turno del cliente se procesa al llegar (extractor + verificador, ventana de
6 turnos), en un almacén en memoria que no escribe en disco. Al final compara con el perfil esperado
(el fixture) y muestra aciertos por campo, alertas, tokens y latencia. Cuesta unas pocas llamadas a Claude.
"""

from __future__ import annotations

import argparse
import asyncio
import json
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

from app import main  # noqa: E402
from app.agentes import claude  # noqa: E402
from app.perfil import store  # noqa: E402
from app.agentes.normalizacion import cita_valida  # noqa: E402
from app.perfil.modelos import Turno  # noqa: E402


def _igual(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().casefold() == b.strip().casefold()
    return a == b


async def ejecutar(entrevista: Path, esperado: Path) -> int:
    if not claude.disponible():
        print("Falta ANTHROPIC_API_KEY (en .env o en el entorno).")
        return 2
    datos = json.loads(entrevista.read_text("utf-8"))
    referencia = json.loads(esperado.read_text("utf-8"))["mifid"]
    cid = "prueba-extractor"

    store.reiniciar()
    sid = store.crear_sesion(cid, "text")["session_id"]
    for t in datos["turns"]:
        turno = Turno(**t)
        store.anadir_turno(sid, turno)
        if turno.speaker == "client":
            print(f"· {turno.turn_id}: {turno.text}")
            await main._procesar_turno(sid)

    perfil = store.perfil(cid)
    print(f"\nModelo extractor: {claude.modelo('extractor')} · esfuerzo {claude.esfuerzo('extractor', 'low')}\n")
    print(f"{'campo':45} {'esperado':>24} {'obtenido':>24}  fuente        conf")
    textos_cliente = [t["text"] for t in datos["turns"] if t["speaker"] == "client"]

    def en_entrevista(ref: dict) -> bool:
        """El fixture puede venir de una entrevista más larga: si su cita no está en esta, no se puede acertar."""
        citas = [e.get("quote", "") for e in ref.get("evidence") or []]
        return not citas or any(cita_valida(c, t) for c in citas for t in textos_cliente)

    aciertos = comparados = fuera = 0
    for ruta, ref in sorted(referencia.items()):
        f = perfil.mifid.get(ruta)
        if f is not None and f.source.value == "calculated":
            continue
        ok = f is not None and _igual(f.value, ref.get("value"))
        if not ok and not en_entrevista(ref):
            fuera += 1
            marca = "·"
        else:
            comparados += 1
            aciertos += ok
            marca = "✓" if ok else "✗"
        obtenido = "—" if f is None else json.dumps(f.value, ensure_ascii=False)
        extra = "" if f is None else f"{f.source.value:12}  {f.confidence if f.confidence is not None else '—'}"
        print(f"{marca} {ruta:43} {json.dumps(ref.get('value'), ensure_ascii=False)[:24]:>24} {obtenido[:24]:>24}  {extra}")
    extra = sorted(set(perfil.mifid) - set(referencia))
    print(f"\nAciertos: {aciertos}/{comparados}"
          + (f" · {fuera} esperados cuya cita no está en esta entrevista (·)" if fuera else "")
          + (f" · campos extra: {', '.join(extra)}" if extra else ""))

    print("\nAlertas:")
    for a in perfil.alerts:
        print(f"  [{a.flag.value}] {a.path}: {a.message}")
    clave = any(a.flag.value == "declared_vs_demonstrated" and a.path == "knowledge.equity_funds" for a in perfil.alerts)
    print(f"  Alerta clave (renta variable declarado ≠ demostrado): {'sí' if clave else 'NO'}")

    rechazos = store.rechazos(sid)
    if rechazos:
        print("\nRechazos:")
        for r in rechazos:
            print(f"  {r.origen} · {r.tipo} · {r.path}: {r.motivo}")

    print("\nUso de Claude:")
    for agente, m in claude.metricas().items():
        media = m["latencia_total_s"] / max(m["llamadas"], 1)
        print(f"  {agente}: {int(m['llamadas'])} llamadas · {int(m['tokens_entrada'])} tokens de entrada · "
              f"{int(m['tokens_cache_leidos'])} desde caché · {int(m['tokens_salida'])} de salida · {media:.1f} s de media")
    return 0 if clave else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrevista", type=Path, default=RAIZ / "fixtures" / "entrevistas" / "carmen-68.json")
    p.add_argument("--esperado", type=Path, default=RAIZ / "fixtures" / "carmen-68.json")
    a = p.parse_args()
    sys.exit(asyncio.run(ejecutar(a.entrevista, a.esperado)))
