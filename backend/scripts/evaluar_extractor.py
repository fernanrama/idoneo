"""Evalúa el extractor con Claude real sobre las entrevistas de casos difíciles (fixtures/evaluacion/).

Uso (desde backend/, con ANTHROPIC_API_KEY en ../.env o en el entorno):

    python scripts/evaluar_extractor.py
    python scripts/evaluar_extractor.py --caso 03 --repeticiones 3
    python scripts/evaluar_extractor.py --informe ../docs/evaluacion-extractor.md

Reproduce el flujo real (cada turno del cliente se procesa al llegar, con extractor y verificador) en un
almacén en memoria que no escribe en disco. Imprime, por caso, cada campo esperado o prohibido, y al
final cobertura, precisión, latencia (mediana y p95) y tokens. Con --repeticiones mide la estabilidad:
el modelo no es determinista y un caso que pasa una vez puede fallar otra.

Coste: unas 30 llamadas por repetición. El código de salida es 1 si se escribió algún dato prohibido.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import statistics
import sys
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

from app import main  # noqa: E402
from app.agentes import claude, evaluacion  # noqa: E402
from app.perfil import store  # noqa: E402

SIMBOLO = {"ok": "✓", "mal": "✗", "falta": "·", "prohibido": "‼"}


def _corto(v, n: int = 28) -> str:
    texto = "—" if v is None else str(v)
    return texto if len(texto) <= n else texto[: n - 1] + "…"


async def ejecutar_caso(caso: evaluacion.Caso) -> evaluacion.Resultado:
    store.reiniciar()
    sid = store.crear_sesion("evaluacion", "text")["session_id"]
    for turno in caso.turnos:
        store.anadir_turno(sid, turno)
        if turno.speaker == "client":
            await main._procesar_turno(sid)
    resultado = evaluacion.puntuar(caso, store.perfil("evaluacion").mifid)
    resultado.rechazos = [f"{r.origen} · {r.path}: {r.motivo}" for r in store.rechazos(sid)]
    return resultado


def imprimir(resultado: evaluacion.Resultado, que_prueba: str) -> None:
    print(f"\n■ {resultado.caso} — {que_prueba}")
    for li in resultado.lineas:
        detalle = f"  ({li.detalle})" if li.detalle else ""
        print(f"  {SIMBOLO[li.estado]} {li.ruta:42} esperado {_corto(li.esperado):28} obtenido {_corto(li.obtenido)}{detalle}")
    for r in resultado.rechazos:
        print(f"  rechazo: {r}")


def informe(ruta: Path, resultados: list[evaluacion.Resultado], r: dict, latencias: list[float], m: dict) -> None:
    filas = "\n".join(
        f"| {x.caso} | {x.cuenta('ok')}/{x.esperados} | {x.cuenta('mal')} | {x.cuenta('falta')} | {x.cuenta('prohibido')} |"
        for x in resultados
    )
    fallos = "\n".join(
        f"- **{x.caso}** · `{li.ruta}`: {li.estado}, esperado {li.esperado}, obtenido {li.obtenido} {li.detalle}".rstrip()
        for x in resultados for li in x.lineas if li.estado != "ok"
    ) or "- Ninguno."
    ruta.write_text(f"""# Evaluación del extractor

Ejecutada el {date.today().isoformat()} con `{claude.modelo('extractor')}` (esfuerzo `{claude.esfuerzo('extractor', 'low')}`)
sobre {len({x.caso for x in resultados})} entrevistas **simuladas** de `backend/fixtures/evaluacion/`, {len(resultados)} ejecuciones.
Regenerar: `python scripts/evaluar_extractor.py --informe <ruta>`.

| Métrica | Valor |
|---|---|
| Cobertura (datos esperados que acaban en el perfil) | {r['cobertura']:.0%} ({r['aciertos']}/{r['esperados']}) |
| Precisión (de lo escrito, cuánto es correcto) | {r['precision']:.0%} |
| Datos prohibidos escritos (terceros, evasivas, manipulación) | {r['prohibidos']} |
| Latencia por turno, mediana / p95 | {statistics.median(latencias):.1f} s / {_p95(latencias):.1f} s |
| Tokens por llamada (entrada / desde caché / salida) | {m['entrada']:.0f} / {m['cache']:.0f} / {m['salida']:.0f} |

| Caso | Aciertos | Erróneos | Faltan | Prohibidos |
|---|---|---|---|---|
{filas}

## Fallos

{fallos}
""", encoding="utf-8")
    print(f"\nInforme escrito en {ruta}")


def _p95(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))] if xs else 0.0


async def principal(a) -> int:
    if not claude.disponible():
        print("Falta ANTHROPIC_API_KEY (en .env o en el entorno).")
        return 2
    if not a.detalle:
        logging.disable(logging.INFO)  # sin el log de cada llamada; los rechazos se imprimen por caso
    todos = [c for c in evaluacion.casos() if not a.caso or c.nombre.startswith(a.caso)]
    if not todos:
        print(f"No hay casos que empiecen por {a.caso!r} en {evaluacion.CARPETA}")
        return 2
    for c in todos:
        errores = evaluacion.comprobar_caso(c)
        if errores:
            print(f"Caso mal formado {c.nombre}: {errores}")
            return 2

    latencias: list[float] = []
    registrar = claude._registrar

    def medir(uso: claude.Uso) -> None:
        if uso.agente == "extractor":
            latencias.append(uso.latencia_s)
        registrar(uso)

    claude._registrar = medir
    claude.reiniciar_metricas()

    resultados = []
    for i in range(a.repeticiones):
        for caso in todos:
            r = await ejecutar_caso(caso)
            imprimir(r, caso.que_prueba + (f" [repetición {i + 1}]" if a.repeticiones > 1 else ""))
            resultados.append(r)

    r = evaluacion.resumen(resultados)
    m = claude.metricas().get("extractor", {})
    n = max(m.get("llamadas", 0), 1)
    medias = {"entrada": m.get("tokens_entrada", 0) / n, "cache": m.get("tokens_cache_leidos", 0) / n,
              "salida": m.get("tokens_salida", 0) / n}
    print(f"\nModelo: {claude.modelo('extractor')} · esfuerzo {claude.esfuerzo('extractor', 'low')}")
    print(f"Cobertura {r['cobertura']:.0%} ({r['aciertos']}/{r['esperados']}) · precisión {r['precision']:.0%} · "
          f"erróneos {r['erroneos']} · prohibidos escritos {r['prohibidos']}")
    if latencias:
        print(f"Latencia del extractor: mediana {statistics.median(latencias):.1f} s · p95 {_p95(latencias):.1f} s · "
              f"{len(latencias)} llamadas")
    print(f"Tokens por llamada: {medias['entrada']:.0f} entrada · {medias['cache']:.0f} desde caché · {medias['salida']:.0f} salida")
    if a.informe:
        informe(a.informe, resultados, r, latencias or [0.0], medias)
    return 1 if r["prohibidos"] else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--caso", help="prefijo del caso (p. ej. 03)")
    p.add_argument("--repeticiones", type=int, default=1)
    p.add_argument("--informe", type=Path, help="escribe un informe en Markdown")
    p.add_argument("--detalle", action="store_true", help="muestra el log de cada llamada a Claude")
    sys.exit(asyncio.run(principal(p.parse_args())))
