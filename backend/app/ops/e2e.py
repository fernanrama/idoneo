"""Pipeline de punta a punta del producto: del cliente a la entidad, pasando por todo lo que hay en medio.

Recorre la API real, en el mismo proceso y con un almacén en memoria:

1. Alta del cliente (sesión de texto y credencial de posesión).
2. Entrevista: cada turno pasa por el extractor y el verificador, como en producción.
3. Perfil: completo, con cada dato citado literalmente de un turno del cliente.
4. Alertas: la que el caso espera (p. ej. dice saber mucho y falla la comprobación).
5. Restricciones antes de validar: el agente de la entidad no puede usar el perfil todavía.
6. Validación por la entidad (credencial del cliente y de servicio).
7. Agente de la entidad por MCP: lee las restricciones y filtra su catálogo con ellas.
8. Trazas de la sesión: una por turno, sin texto del cliente.
9. Métricas y evaluaciones: el panel de LLMOps responde y las evaluaciones cumplen sus umbrales.

Dos modos:

- `simulado` (por defecto, sin clave): la entrevista es un guion y las respuestas de Claude están grabadas
  en el fixture. Todo lo demás es código real (guardas, rúbrica, validación, cálculos, MCP). Corre en la CI.
- `real` (con `ANTHROPIC_API_KEY`): el entrevistador real habla con un cliente simulado por Claude a partir
  de la ficha, y el extractor y el verificador son Claude. Mide el producto entero. Corre en la CI de evals.

Todo es ficticio (DATOS SIMULADOS): ni el cliente, ni la entidad, ni su catálogo existen.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from contextlib import ExitStack
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import anyio.from_thread

CARPETA = Path(__file__).resolve().parents[2] / "fixtures" / "e2e"
CLIENTE = CARPETA / "cliente-lucia.json"
ENTIDAD = CARPETA / "entidad-banco-ejemplo.json"
MAX_TURNOS_REAL = 30


@dataclass
class Paso:
    nombre: str
    ok: bool
    detalle: str
    segundos: float = 0.0
    datos: dict[str, Any] = field(default_factory=dict)


@dataclass
class Informe:
    modo: str
    cliente: str
    entidad: str
    pasos: list[Paso] = field(default_factory=list)
    duracion_s: float = 0.0
    coste_usd: float = 0.0

    @property
    def ok(self) -> bool:
        return bool(self.pasos) and all(p.ok for p in self.pasos)

    def metricas(self) -> dict[str, float]:
        return {"pasos_ok": round(sum(p.ok for p in self.pasos) / max(len(self.pasos), 1), 4),
                "duracion_s": round(self.duracion_s, 2), "coste_usd": round(self.coste_usd, 4)}

    def a_dict(self) -> dict[str, Any]:
        return {**asdict(self), "ok": self.ok, "metricas": self.metricas()}

    def markdown(self) -> str:
        filas = "\n".join(f"| {i} | {p.nombre} | {'✓' if p.ok else '✗'} | {p.detalle} | {p.segundos:.2f} s |"
                          for i, p in enumerate(self.pasos, 1))
        return (f"# Pipeline de punta a punta · modo {self.modo}\n\n"
                "DATOS SIMULADOS: cliente, entidad y catálogo ficticios.\n\n"
                f"- Cliente: {self.cliente}\n- Entidad: {self.entidad}\n"
                f"- Resultado: **{'todo bien' if self.ok else 'hay pasos que fallan'}** "
                f"({sum(p.ok for p in self.pasos)}/{len(self.pasos)} pasos)\n"
                f"- Duración: {self.duracion_s:.1f} s · coste estimado: {self.coste_usd:.3f} $\n\n"
                "| # | Paso | Bien | Detalle | Tiempo |\n|---|---|---|---|---|\n" + filas + "\n")


# ---------- Claude grabado (modo simulado) ----------

def _claude_grabado(guion: list[dict[str, Any]]):
    """Sustituto de `claude.estructurado` que devuelve las salidas grabadas en el fixture.

    Extractor: busca el último turno del cliente del mensaje y devuelve su `extraccion` con su turn_id real.
    Verificador: sin hallazgos (sus reglas fijas siguen funcionando). Cada llamada queda en las trazas.
    """
    from ..agentes import claude, extractor, verificador
    from . import trazas

    por_texto = {t["text"]: t.get("extraccion") for t in guion if t["speaker"] == "client"}

    async def estructurado(*, agente: str, sistema: str, mensaje: str, esquema, **_kw):
        inicio = time.perf_counter()
        if esquema is extractor.Extraccion:
            ultimo = None
            for linea in mensaje.splitlines():
                if linea.startswith("{"):
                    t = json.loads(linea)
                    if t.get("speaker") == "client":
                        ultimo = t
            grabado = (por_texto.get(ultimo["text"]) if ultimo else None) or {"datos": [], "conocimientos": [], "escenario": None}
            datos = json.loads(json.dumps(grabado))
            for d in datos.get("datos", []) + datos.get("conocimientos", []):
                d["turn_id"] = ultimo["turn_id"]
            if datos.get("escenario"):
                datos["escenario"]["turn_id"] = ultimo["turn_id"]
            salida = extractor.Extraccion.model_validate(datos)
        elif esquema is verificador.Revision:
            salida = verificador.Revision(hallazgos=[])
        else:
            raise RuntimeError(f"El modo simulado no tiene respuestas grabadas para {agente}")
        latencia = round(time.perf_counter() - inicio, 4)
        trazas.registrar_llamada(trazas.Llamada(agente=agente, modelo="grabado", prompt=trazas.version_prompt(sistema),
                                                inicio=trazas._ahora(), latencia_s=latencia))
        return salida, claude.Uso(agente=agente, modelo="grabado", tokens_entrada=0, tokens_salida=0, latencia_s=latencia)

    return estructurado


# ---------- utilidades ----------

def _filtrar_catalogo(restr: dict[str, Any], catalogo: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    """Lo que haría el agente de la entidad con las restricciones: qué productos puede proponer y por qué no el resto."""
    admitidos, descartados = [], {}
    q = restr.get("funds_query", {})
    tipos_activo = q.get("asset_type")
    tipos_activo = [tipos_activo] if isinstance(tipos_activo, str) else tipos_activo
    for p in catalogo:
        motivo = None
        if not restr.get("usable"):
            motivo = "perfil no usable"
        elif p["tipo"] in restr.get("blocked_searches", []):
            motivo = f"búsqueda bloqueada: {p['tipo']}"
        elif restr.get("appropriateness", {}).get(p["familia"], "not_evaluated") != "appropriate" and p["tipo"] == "funds":
            motivo = f"conveniencia de {p['familia']}: {restr.get('appropriateness', {}).get(p['familia'], 'sin evaluar')}"
        elif "max_risk" in q and p["sri"] > q["max_risk"]:
            motivo = f"SRI {p['sri']} > máximo {q['max_risk']}"
        elif tipos_activo and p["asset_type"] not in tipos_activo:
            motivo = f"tipo de activo {p['asset_type']} fuera de {', '.join(tipos_activo)}"
        elif q.get("currency") and p["currency"] != q["currency"]:
            motivo = f"divisa {p['currency']}"
        else:
            for f in restr.get("post_filters", []):
                v = p.get(f["field"])
                ok = (v is not None and ((f["op"] == "<=" and v <= f["value"]) or (f["op"] == ">=" and v >= f["value"])
                                         or (f["op"] == "in" and v in f["value"])
                                         or (f["op"] == "not_contains" and f["value"] not in str(v))))
                if not ok:
                    motivo = f"filtro {f['field']} {f['op']} {f['value']}"
                    break
        if motivo:
            descartados[p["id"]] = motivo
        else:
            admitidos.append(p["id"])
    return admitidos, descartados


def _cita_en_turnos(cita: str, turnos: list[dict[str, Any]]) -> bool:
    from ..agentes.normalizacion import cita_valida
    return any(t["speaker"] == "client" and cita_valida(cita, t["text"]) for t in turnos)


# ---------- pipeline ----------

def preparar_entorno(modo: str, fijar: Callable[[str, str], None] = os.environ.__setitem__) -> None:
    """Almacén en memoria y credenciales sintéticas de un solo uso, solo en este proceso."""
    valores = {"PERFIL_ALMACEN": "memoria", "DATA_PERSIST": "0", "DATABASE_URL": "", "LOAD_DEMO_FIXTURE": "0",
               "CLIENT_ACCESS_SECRET": secrets.token_hex(32), "ADMIN_TOKEN": secrets.token_hex(24),
               "CLIENT_ACCESS_TTL_S": "28800", "LIMITE_SESIONES_DIA": "0", "LIMITE_TURNOS_SESION": "0",
               "LIMITE_VOZ_DIA": "0"}
    if modo == "simulado":
        valores["ANTHROPIC_API_KEY"] = "clave-ficticia-del-modo-simulado"
        valores["VERIFICADOR_CLAUDE"] = "1"
    for clave, valor in valores.items():
        fijar(clave, valor)


def _entrevista_real(c, sid: str, cab: dict[str, str], ficha: str) -> list[dict[str, Any]]:
    """El cliente simulado corre en el mismo bucle que la API (`c.portal`): el cliente de Anthropic es único
    y sus conexiones no se pueden compartir entre bucles distintos (se colgaban hasta el timeout)."""
    from ..agentes import cliente_simulado
    from ..perfil.modelos import Turno

    turnos: list[Turno] = []
    texto = None
    for _ in range(MAX_TURNOS_REAL):
        r = c.post(f"/api/sessions/{sid}/chat", json={"text": texto} if texto else {}, headers=cab)
        r.raise_for_status()
        cuerpo = r.json()
        if cuerpo["client_turn"]:
            turnos.append(Turno(**cuerpo["client_turn"]))
        turnos.append(Turno(**cuerpo["agent_turn"]))
        if cuerpo["finished"]:
            break
        texto = c.portal.call(cliente_simulado.responder, ficha, list(turnos))
    return [t.model_dump() for t in turnos]


def ejecutar(modo: str = "simulado", parchear: Callable[[Any, str, Any], None] | None = None,
             fijar_entorno: Callable[[str, str], None] | None = None) -> Informe:
    """Ejecuta el pipeline entero. Los tests pasan `monkeypatch.setattr` y `monkeypatch.setenv` para que
    nada se quede cambiado; el script usa los valores por defecto (sustituye y restaura `claude`)."""
    if modo not in ("simulado", "real"):
        raise ValueError("modo debe ser 'simulado' o 'real'")
    preparar_entorno(modo, fijar_entorno or os.environ.__setitem__)

    from fastapi.testclient import TestClient
    from starlette.requests import Request

    from ..agentes import claude
    from ..main import app
    from ..mcp.servidor import mcp
    from ..perfil import store
    from ..perfil.modelos import OBLIGATORIOS
    from . import trazas

    cliente_fx = json.loads(CLIENTE.read_text("utf-8"))
    entidad_fx = json.loads(ENTIDAD.read_text("utf-8"))
    esperado = cliente_fx["esperado"]
    informe = Informe(modo=modo, cliente=cliente_fx["client_name"], entidad=entidad_fx["entidad"])
    restaurar: list[tuple[Any, str, Any]] = []

    def sustituir(obj, nombre, valor):
        if parchear is not None:
            parchear(obj, nombre, valor)
        else:
            restaurar.append((obj, nombre, getattr(obj, nombre)))
            setattr(obj, nombre, valor)

    if modo == "simulado":
        sustituir(claude, "estructurado", _claude_grabado(cliente_fx["turnos"]))
    elif not claude.disponible():
        raise RuntimeError("El modo real necesita ANTHROPIC_API_KEY")

    store.configurar("memoria")
    store.reiniciar()
    trazas.reiniciar()
    t_total = time.perf_counter()
    # Un solo bucle de eventos para todas las peticiones (sin arrancar el lifespan): TestClient abre uno nuevo
    # por petición si no tiene portal, y el cliente de Anthropic no puede saltar de un bucle a otro.
    pila = ExitStack()
    c = TestClient(app)
    c.portal = pila.enter_context(anyio.from_thread.start_blocking_portal(**c.async_backend))
    ctx: dict[str, Any] = {}

    def paso(nombre: str):
        def decorador(fn):
            t0 = time.perf_counter()
            try:
                ok, detalle, datos = fn()
            except Exception as e:  # un paso roto no corta el informe: se apunta y se sigue
                ok, detalle, datos = False, f"error: {type(e).__name__}: {str(e)[:200]}", {}
            informe.pasos.append(Paso(nombre, ok, detalle, round(time.perf_counter() - t0, 3), datos))
            return fn
        return decorador

    try:
        @paso("Alta del cliente")
        def _():
            r = c.post("/api/sessions", json={"channel": "text"})
            r.raise_for_status()
            alta = r.json()
            ctx.update(cid=alta["client_id"], sid=alta["session_id"],
                       cab={"Authorization": f"Bearer {alta['access_token']}"})
            return True, f"cliente {alta['client_id'][:16]}… con sesión de texto y credencial propia", {}

        @paso("Entrevista")
        def _():
            if modo == "simulado":
                for t in cliente_fx["turnos"]:
                    r = c.post(f"/api/sessions/{ctx['sid']}/turns", headers=ctx["cab"],
                               json={"speaker": t["speaker"], "text": t["text"], "t_start": 0, "t_end": 1})
                    r.raise_for_status()
            else:
                _entrevista_real(c, ctx["sid"], ctx["cab"], cliente_fx["ficha"])
            s = c.get(f"/api/sessions/{ctx['sid']}", headers=ctx["cab"]).json()
            ctx["turnos"] = s["turns"]
            cliente = sum(1 for t in s["turns"] if t["speaker"] == "client")
            rechazos = s.get("rejections", [])
            return True, f"{len(s['turns'])} turnos ({cliente} del cliente), {len(rechazos)} rechazos del procesamiento", \
                {"rechazos": [r.get("motivo") for r in rechazos][:10]}

        @paso("Perfil completo y con pruebas")
        def _():
            p = c.get(f"/api/clients/{ctx['cid']}/profile", headers=ctx["cab"]).json()
            ctx["perfil"] = p
            faltan = [r for r in OBLIGATORIOS if r not in p["mifid"]]
            sin_cita = [r for r, f in p["mifid"].items() if f["source"] != "calculated"
                        and not any(_cita_en_turnos(e["quote"], ctx["turnos"]) for e in f.get("evidence", []))]
            distintos = {} if modo == "real" else {
                r: p["mifid"].get(r, {}).get("value") for r, v in esperado["valores"].items()
                if p["mifid"].get(r, {}).get("value") != v}
            ok = p["status"] == esperado["status"] and not faltan and not sin_cita and not distintos
            return ok, (f"estado {p['status']}, {len(p['mifid'])} datos, faltan {faltan or 'ninguno'}, "
                        f"sin cita literal {sin_cita or 'ninguno'}"
                        + (f", distintos de lo esperado {distintos}" if distintos else "")), {}

        @paso("Alertas para el asesor")
        def _():
            abiertas = [a for a in ctx["perfil"]["alerts"] if a["status"] == "open"]
            faltan = [e for e in esperado["alertas"] if not any(a["path"] == e or a["flag"] == e for a in abiertas)]
            return not faltan, (f"{len(abiertas)} abiertas; esperadas {esperado['alertas']}: "
                                f"{'todas' if not faltan else 'faltan ' + ', '.join(faltan)}"), \
                {"alertas": [f"{a['flag']} · {a['path']} · {a['message']}" for a in abiertas]}

        @paso("Restricciones antes de validar")
        def _():
            r = c.get(f"/api/clients/{ctx['cid']}/constraints", headers=ctx["cab"]).json()
            return r["usable"] is False, f"usable={r['usable']}: el agente de la entidad aún no puede recomendar nada", {}

        @paso("Validación por la entidad")
        def _():
            cab = {**ctx["cab"], "X-Admin-Token": os.environ["ADMIN_TOKEN"]}
            r = c.post(f"/api/clients/{ctx['cid']}/validate", headers=cab, json={"advisor_id": entidad_fx["asesor_id"]})
            r.raise_for_status()
            p = r.json()
            return p["status"] == "active", f"{entidad_fx['asesor_id']} valida la versión {p['version']} → {p['status']}", {}

        @paso("Agente de la entidad por MCP")
        def _():
            peticion = Request({"type": "http", "headers": [(b"x-admin-token", os.environ["ADMIN_TOKEN"].encode())]})
            original = mcp.get_context
            mcp.get_context = lambda: SimpleNamespace(request_context=SimpleNamespace(request=peticion))
            try:
                res = c.portal.call(mcp.call_tool, "get_investment_constraints", {"client_id": ctx["cid"]})
            finally:
                mcp.get_context = original
            bloques = res[0] if isinstance(res, tuple) else res
            restr = json.loads(bloques[0].text)
            admitidos, descartados = _filtrar_catalogo(restr, entidad_fx["catalogo"])
            conv = {k: restr["appropriateness"].get(k) for k in esperado["conveniencia"]}
            exp = entidad_fx["esperado"]
            ok = (restr["usable"] and conv == esperado["conveniencia"]
                  and (modo == "real" or (set(exp["admitidos_incluyen"]) <= set(admitidos)
                                          and set(exp["descartados_incluyen"]) <= set(descartados))))
            return ok, (f"usable, SRI máximo {restr['funds_query'].get('max_risk')}, "
                        f"{len(admitidos)} de {len(entidad_fx['catalogo'])} productos del catálogo admitidos"), \
                {"admitidos": admitidos, "descartados": descartados, "rationale": restr.get("rationale", [])}

        @paso("Trazas de la sesión")
        def _():
            runs = c.get(f"/api/sessions/{ctx['sid']}/trace", headers=ctx["cab"]).json()["runs"]
            turnos_cliente = sum(1 for t in ctx["turnos"] if t["speaker"] == "client")
            procesados = [r for r in runs if r["tipo"] == "turno"]
            agentes = {ll["agente"] for r in procesados for ll in r["llamadas"]}
            texto = json.dumps(runs, ensure_ascii=False)
            fuga = [t["text"] for t in ctx["turnos"] if t["speaker"] == "client" and len(t["text"]) > 12 and t["text"] in texto]
            ok = len(procesados) == turnos_cliente and {"extractor", "verificador"} <= agentes and not fuga
            informe.coste_usd = sum(r["coste_usd"] for r in runs)
            return ok, (f"{len(procesados)} turnos procesados con {', '.join(sorted(agentes))}; "
                        f"{'sin texto del cliente' if not fuga else 'HAY TEXTO DEL CLIENTE'}"), {}

        @paso("Métricas y evaluaciones")
        def _():
            m = c.get("/api/ops/metrics").json()
            e = c.get("/api/ops/evals").json()
            hechas = {k: v["ok"] for k, v in e["componentes"].items() if v["ejecutada"] and k != "e2e"}
            # Este paso comprueba que el panel recibe métricas y evaluaciones, no que cada evaluación cumpla
            # sus umbrales: eso lo exige su propio script y la CI de evals, y aquí solo se informa.
            ok = m["totales"]["llamadas"] > 0 and bool(hechas)
            fallan = [k for k, v in hechas.items() if not v]
            return ok, (f"{m['totales']['llamadas']} llamadas trazadas; evaluaciones que cumplen: "
                        f"{sum(hechas.values())}/{len(hechas)}" + (f" (por debajo del umbral: {', '.join(fallan)})"
                                                                    if fallan else "")), {"evaluaciones": hechas}
    finally:
        pila.close()
        for obj, nombre, valor in reversed(restaurar):
            setattr(obj, nombre, valor)
        informe.duracion_s = round(time.perf_counter() - t_total, 2)
    return informe
