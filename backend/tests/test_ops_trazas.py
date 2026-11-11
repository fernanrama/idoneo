"""Trazas y métricas de LLMOps (app/ops/trazas.py, GET /api/ops/metrics, GET /api/sessions/{id}/trace)."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from app.agentes import chat, claude
from app.agentes.extractor import Extraccion
from app.ops import trazas
from app.perfil import store
from tests.soporte_acceso import cliente_autorizado


class _Salida(SimpleNamespace):
    pass


def _cliente_falso(respuestas):
    """Imita `AsyncAnthropic().messages.parse`: devuelve las respuestas en orden (o lanza si es una excepción)."""
    cola = list(respuestas)

    async def parse(**_kw):
        r = cola.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    return SimpleNamespace(messages=SimpleNamespace(parse=parse))


def _respuesta(stop="end_turn", salida="ok", entrada=100, leidos=900, escritos=0, out=50):
    return SimpleNamespace(
        stop_reason=stop, parsed_output=salida,
        usage=SimpleNamespace(input_tokens=entrada, output_tokens=out, cache_read_input_tokens=leidos,
                              cache_creation_input_tokens=escritos))


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    trazas.reiniciar()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("TRAZAS_ARCHIVO", raising=False)
    yield
    trazas.reiniciar()


def test_cada_llamada_queda_trazada_con_version_de_prompt_y_coste(monkeypatch):
    falso = _cliente_falso([_respuesta(), _respuesta(stop="refusal")])
    monkeypatch.setattr(claude, "_cliente_async", lambda: falso)
    monkeypatch.setenv("MODEL_EXTRACTOR", "claude-sonnet-5-5")

    async def dos_llamadas():
        with trazas.ejecucion("turno", "s-1"):
            await claude.estructurado(agente="extractor", sistema="prompt v1", mensaje="m", esquema=Extraccion)
            with pytest.raises(claude.RespuestaNoUtil):
                await claude.estructurado(agente="extractor", sistema="prompt v1", mensaje="m", esquema=Extraccion)

    asyncio.run(dos_llamadas())
    [run] = trazas.de_sesion("s-1")
    assert run["tipo"] == "turno" and run["estado"] == "ok"
    ok, rechazo = run["llamadas"]
    assert ok["resultado"] == "ok" and rechazo["resultado"] == "rechazo"
    assert ok["prompt"] == trazas.version_prompt("prompt v1") and len(ok["prompt"]) == 10
    # 100 × 2 $ + 900 × 0,10 $ + 50 × 10 $ por millón
    assert ok["coste_usd"] == pytest.approx((100 * 2 + 900 * 0.10 + 50 * 10) / 1e6)
    assert run["coste_usd"] == pytest.approx(2 * ok["coste_usd"])


def test_un_error_de_red_tambien_se_traza(monkeypatch):
    monkeypatch.setattr(claude, "_cliente_async", lambda: _cliente_falso([ConnectionError("sin red")]))
    with pytest.raises(ConnectionError):
        asyncio.run(claude.estructurado(agente="verificador", sistema="s", mensaje="m", esquema=Extraccion))
    r = trazas.resumen()
    assert r["por_agente"]["verificador"]["fallos"] == 1
    assert r["por_agente"]["verificador"]["tasa_fallo"] == 1.0


def test_resumen_agrega_percentiles_cache_y_versiones():
    for i, lat in enumerate([1.0, 2.0, 3.0, 4.0, 10.0]):
        with trazas.ejecucion("turno", f"s-{i}"):
            trazas.registrar_llamada(trazas.Llamada(
                agente="extractor", modelo="claude-sonnet-5-5", prompt="a" if i < 3 else "b", inicio="t",
                latencia_s=lat, tokens_entrada=100, tokens_cache_leidos=900, tokens_salida=10, coste_usd=0.001))
    r = trazas.resumen()
    e = r["por_agente"]["extractor"]
    assert e["llamadas"] == 5 and e["latencia_p50_s"] == 3.0 and e["latencia_p95_s"] == 10.0
    assert e["tasa_cache"] == 0.9 and e["versiones_prompt"] == ["a", "b"]
    assert r["por_tipo"]["turno"]["ejecuciones"] == 5
    assert [v["version"] for v in r["por_version_prompt"]] == ["a", "b"]
    assert r["totales"]["coste_usd"] == pytest.approx(0.005)
    # Lo público no lleva identificadores de sesión.
    assert all("sesion" not in x for x in r["recientes"])


def test_el_archivo_de_trazas_no_guarda_texto(monkeypatch, tmp_path):
    ruta = tmp_path / "trazas.jsonl"
    monkeypatch.setenv("TRAZAS_ARCHIVO", str(ruta))
    monkeypatch.setattr(claude, "_cliente_async", lambda: _cliente_falso([_respuesta()]))

    async def una():
        with trazas.ejecucion("chat", "s-x"):
            await claude.estructurado(agente="entrevistador", sistema="secreto del sistema",
                                      mensaje="Cobro 1.800 euros al mes", esquema=Extraccion)

    asyncio.run(una())
    linea = ruta.read_text("utf-8").strip()
    d = json.loads(linea)
    assert d["tipo"] == "chat" and len(d["llamadas"]) == 1
    assert "1.800" not in linea and "secreto" not in linea


def test_coste_de_un_modelo_desconocido_usa_la_tarifa_por_defecto():
    assert trazas.coste_usd("otro", 1_000_000, 0, 0, 0) == trazas.PRECIO_DESCONOCIDO["entrada"]
    assert trazas.coste_usd("claude-opus-5-5", 0, 0, 0, 1_000_000) == 20.0


@pytest.fixture
def api(monkeypatch):
    store.reiniciar()

    async def falso(**kw):
        trazas.registrar_llamada(trazas.Llamada(agente=kw["agente"], modelo="simulado", prompt="p", inicio="t",
                                                latencia_s=0.5, tokens_entrada=10, tokens_salida=5, coste_usd=0.0001))
        if kw["esquema"] is chat.Respuesta:
            return chat.Respuesta(texto="¿Para qué quiere invertir?", terminada=False), None
        return Extraccion(datos=[], conocimientos=[], escenario=None), None

    monkeypatch.setattr(claude, "estructurado", falso)
    cliente = cliente_autorizado()
    sid = cliente.post("/api/sessions", json={"channel": "text"}).json()["session_id"]
    return cliente, sid


def test_la_sesion_ve_sus_trazas_y_el_panel_el_agregado(api):
    cliente, sid = api
    cliente.post(f"/api/sessions/{sid}/chat", json={})
    cliente.post(f"/api/sessions/{sid}/chat", json={"text": "Para la jubilación"})

    runs = cliente.get(f"/api/sessions/{sid}/trace").json()["runs"]
    tipos = [r["tipo"] for r in runs]
    assert tipos.count("chat") == 2 and "turno" in tipos
    turno = next(r for r in runs if r["tipo"] == "turno")
    assert set(turno["resultado"]) == {"parches", "alertas", "rechazos"}

    m = cliente.get("/api/ops/metrics").json()
    assert m["totales"]["ejecuciones"] >= 3 and "entrevistador" in m["por_agente"]
    assert sid not in json.dumps(m)


def test_las_trazas_de_una_sesion_piden_su_credencial(api):
    from fastapi.testclient import TestClient
    from app.main import app

    _, sid = api
    assert TestClient(app).get(f"/api/sessions/{sid}/trace").status_code in (401, 403)
