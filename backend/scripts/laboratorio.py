"""Laboratorio: entrevistas completas por texto entre el entrevistador real y clientes simulados por Claude.

Uso (desde backend/, con ANTHROPIC_API_KEY en ../.env o en el entorno):

    python scripts/laboratorio.py --persona carmen
    python scripts/laboratorio.py --variantes 20 --semilla 7 --repeticiones 2 --sin-fijas
    python scripts/laboratorio.py --transcripciones ../docs/laboratorio --informe ../docs/laboratorio/informe.md

Cada persona (fixtures/laboratorio/*.json) tiene una ficha oculta que solo ve el cliente simulado. Mide el
sistema entero: lo que el entrevistador pregunta y comprueba, y lo que el extractor apunta. Sin voz
(ElevenLabs) ni MyInvestor. Almacén en memoria: no escribe en la base de datos.

Coste: unas 3 llamadas a Claude por turno (entrevistador, cliente simulado y extractor), unos 15-25 turnos
por persona. Empieza con una persona (--persona) para ver el gasto en la consola de Anthropic.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import statistics
import sys
from collections import defaultdict
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
from app.agentes import claude, evaluacion, laboratorio, variantes  # noqa: E402
from app.perfil import store  # noqa: E402

CLIENTE = "laboratorio"
SIMBOLO = {"ok": "✓", "mal": "✗", "falta": "·", "prohibido": "‼"}


def _si(v: bool) -> str:
    return "sí" if v else "NO"


async def ejecutar(persona: laboratorio.Persona, max_turnos: int) -> laboratorio.Informe:
    store.reiniciar()
    return await laboratorio.entrevistar(
        persona,
        sesion_nueva=lambda: store.crear_sesion(CLIENTE, "text")["session_id"],
        anadir_turno=store.anadir_turno,
        procesar_turno=main._procesar_turno,
        perfil=lambda: store.perfil(CLIENTE),
        max_turnos=max_turnos,
    )


def imprimir(i: laboratorio.Informe, que_prueba: str) -> None:
    print(f"\n■ {i.persona} — {que_prueba}")
    print(f"  {i.intervenciones} intervenciones del asistente · terminada {_si(i.terminada)} · "
          f"aviso de IA al inicio {_si(i.aviso_ia_al_inicio)} · preguntas dobles {i.preguntas_dobles} · "
          f"recomendaciones {i.recomendaciones}")
    print(f"  Conocimientos comprobados: {', '.join(i.comprobados) or 'ninguno'}")
    for ruta, ok in i.alertas_esperadas.items():
        print(f"  Alerta esperada en {ruta}: {_si(ok)}")
    for li in i.resultado.lineas:
        detalle = f"  ({li.detalle})" if li.detalle else ""
        print(f"  {SIMBOLO[li.estado]} {li.ruta:42} esperado {str(li.esperado)[:26]:26} obtenido {str(li.obtenido)[:30]}{detalle}")
    if i.pendientes:
        print(f"  Pendiente al terminar: {', '.join(i.pendientes)}")


def escribir_informe(ruta: Path, informes: list[laboratorio.Informe], r: dict, latencias: dict, medias: dict) -> None:
    filas = "\n".join(
        f"| {i.persona} | {i.resultado.cuenta('ok')}/{i.resultado.esperados} | {i.resultado.cuenta('prohibido')} | "
        f"{i.intervenciones} | {_si(i.terminada)} | {_si(i.aviso_ia_al_inicio)} | {', '.join(i.comprobados) or '—'} | "
        f"{', '.join(f'{k}: {_si(v)}' for k, v in i.alertas_esperadas.items()) or '—'} | {len(i.pendientes)} |"
        for i in informes
    )
    lat = "\n".join(f"| {a} | {statistics.median(xs):.1f} s | {_p95(xs):.1f} s | {len(xs)} |" for a, xs in sorted(latencias.items()))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(f"""# Laboratorio de entrevistas

Ejecutado el {date.today().isoformat()}. Entrevistador `{claude.modelo('entrevistador')}`, extractor `{claude.modelo('extractor')}`,
cliente simulado `{claude.modelo('cliente_simulado')}`. Personas **simuladas** de `backend/fixtures/laboratorio/`; sin voz.

| Métrica | Valor |
|---|---|
| Cobertura del perfil frente a la ficha oculta | {r['cobertura']:.0%} ({r['aciertos']}/{r['esperados']}) |
| Precisión | {r['precision']:.0%} |
| Datos prohibidos escritos | {r['prohibidos']} |
| Recomendaciones del asistente (deben ser 0) | {sum(i.recomendaciones for i in informes)} |

| Persona | Aciertos | Prohibidos | Turnos asistente | Terminada | Aviso IA | Comprobados | Alerta esperada | Pendientes |
|---|---|---|---|---|---|---|---|---|
{filas}

| Agente | Mediana | p95 | Llamadas |
|---|---|---|---|
{lat}

Tokens medios por llamada: {', '.join(f"{a} {m['entrada']:.0f} entrada / {m['cache']:.0f} caché / {m['salida']:.0f} salida" for a, m in sorted(medias.items()))}.
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
        logging.disable(logging.INFO)
    fijas = [] if a.sin_fijas else laboratorio.personas()
    elegidas = [p for p in fijas if not a.persona or p.caso.nombre.startswith(a.persona)]
    elegidas += variantes.generar(a.variantes, a.semilla) if a.variantes else []
    if not elegidas:
        print(f"No hay personas que empiecen por {a.persona!r} en {laboratorio.CARPETA}")
        return 2
    for p in elegidas:
        errores = evaluacion.comprobar_caso(p.caso, con_turnos=False)
        if errores:
            print(f"Persona mal formada {p.caso.nombre}: {errores}")
            return 2

    latencias: dict[str, list[float]] = defaultdict(list)
    registrar = claude._registrar

    def medir(uso: claude.Uso) -> None:
        latencias[uso.agente].append(uso.latencia_s)
        registrar(uso)

    claude._registrar = medir
    claude.reiniciar_metricas()

    informes = []
    fallidas: list[str] = []
    total = len(elegidas) * a.repeticiones
    for rep in range(a.repeticiones):
        for p in elegidas:
            try:
                i = await ejecutar(p, a.max_turnos)
            except Exception as e:  # una entrevista rota (red, límite de uso) no tira la tirada entera
                fallidas.append(f"{p.caso.nombre}: {type(e).__name__}: {str(e)[:200]}")
                print(f"\n✗ {p.caso.nombre} falló: {type(e).__name__}: {str(e)[:200]}")
                continue
            sufijo = f" [repetición {rep + 1}]" if a.repeticiones > 1 else ""
            print(f"\n({len(informes) + 1}/{total})", end="")
            imprimir(i, p.caso.que_prueba + sufijo)
            informes.append(i)
            if not a.transcripciones:
                continue
            a.transcripciones.mkdir(parents=True, exist_ok=True)
            nombre = i.persona + (f"-r{rep + 1}" if a.repeticiones > 1 else "")
            (a.transcripciones / f"{nombre}.txt").write_text(
                "TRANSCRIPCIÓN SIMULADA (cliente interpretado por Claude)\n\nFicha:\n" + p.ficha + "\n\n"
                + laboratorio.transcripcion(i) + "\n", encoding="utf-8")

    if fallidas:
        print(f"\n{len(fallidas)} entrevistas fallaron y no cuentan en las métricas:")
        for f in fallidas:
            print(f"  {f}")
    if not informes:
        return 2
    r = evaluacion.resumen([i.resultado for i in informes])
    medias = {}
    for agente, m in claude.metricas().items():
        n = max(m["llamadas"], 1)
        medias[agente] = {"entrada": m["tokens_entrada"] / n, "cache": m["tokens_cache_leidos"] / n,
                          "salida": m["tokens_salida"] / n}
    print(f"\nCobertura {r['cobertura']:.0%} ({r['aciertos']}/{r['esperados']}) · precisión {r['precision']:.0%} · "
          f"prohibidos escritos {r['prohibidos']} · recomendaciones {sum(i.recomendaciones for i in informes)}")
    for agente, xs in sorted(latencias.items()):
        m = claude.metricas()[agente]
        print(f"  {agente}: {len(xs)} llamadas · mediana {statistics.median(xs):.1f} s · p95 {_p95(xs):.1f} s · "
              f"{int(m['tokens_entrada'])} entrada + {int(m['tokens_cache_leidos'])} caché + {int(m['tokens_salida'])} salida")
    if a.transcripciones:
        print(f"Transcripciones en {a.transcripciones}")
    if a.informe:
        escribir_informe(a.informe, informes, r, latencias, medias)
    graves = r["prohibidos"] + sum(i.recomendaciones for i in informes) + len(fallidas)
    return 1 if graves else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--persona", help="prefijo de la persona (p. ej. carmen)")
    p.add_argument("--variantes", type=int, default=0, help="añade N clientes generados")
    p.add_argument("--semilla", type=int, default=1, help="semilla de las variantes (misma semilla, mismas personas)")
    p.add_argument("--sin-fijas", action="store_true", help="solo las variantes, sin las personas de fixtures/laboratorio")
    p.add_argument("--repeticiones", type=int, default=1)
    p.add_argument("--max-turnos", type=int, default=laboratorio.MAX_TURNOS)
    p.add_argument("--transcripciones", type=Path, help="carpeta donde guardar cada conversación")
    p.add_argument("--informe", type=Path, help="escribe un informe en Markdown")
    p.add_argument("--detalle", action="store_true", help="muestra el log de cada llamada a Claude")
    sys.exit(asyncio.run(principal(p.parse_args())))
