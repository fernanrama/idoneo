"""Herramientas MCP (rol D): mismas reglas que la API, sobre el perfil simulado de Carmen."""

import asyncio
import json
import os

os.environ["DATA_PERSIST"] = "0"

from app.mcp.servidor import mcp  # noqa: E402
from app.perfil import store  # noqa: E402

CID = "carmen-68"


def llamar(nombre: str, **args) -> dict:
    store.reiniciar()
    store.cargar_fixture(CID)
    return _llamar_sin_reiniciar(nombre, **args)


def _llamar_sin_reiniciar(nombre: str, **args) -> dict:
    res = asyncio.run(mcp.call_tool(nombre, args))
    bloques = res[0] if isinstance(res, tuple) else res
    return json.loads(bloques[0].text)


def test_expone_las_cuatro_herramientas():
    nombres = {t.name for t in asyncio.run(mcp.list_tools())}
    assert nombres == {"get_client_profile", "get_investment_constraints", "get_evidence", "get_client_context"}


def test_restricciones_sin_validar_no_son_usables():
    r = llamar("get_investment_constraints", client_id=CID)
    assert r["status"] == "pending_validation" and r["usable"] is False
    assert r["funds_query"]  # los parámetros existen aunque no se puedan usar todavía


def test_restricciones_tras_validar():
    store.reiniciar()
    store.cargar_fixture(CID)
    store.validar(CID, "asesor-demo", [])
    r = _llamar_sin_reiniciar("get_investment_constraints", client_id=CID)
    assert r["usable"] is True and r["status"] == "active"
    assert r["appropriateness"]["equity_funds"] == "not_appropriate"


def test_perfil_y_evidencia():
    p = llamar("get_client_profile", client_id=CID)
    assert p["client_id"] == CID and p["usable"] is False
    e = _llamar_sin_reiniciar("get_evidence", client_id=CID, field="knowledge.equity_funds")
    assert e["source"] == "demonstrated" and e["evidence"] and "quote" in e["evidence"][0]


def test_errores_legibles():
    assert llamar("get_client_profile", client_id="nadie")["error"] == "not_found"
    e = _llamar_sin_reiniciar("get_evidence", client_id=CID, field="no.existe")
    assert e["error"] == "unknown_field" and "knowledge.equity_funds" in e["available_fields"]


def test_contexto():
    c = llamar("get_client_context", client_id=CID)
    assert c["text"] and len(c["text"].split()) <= 150


def test_instrucciones_explican_listas_y_limites():
    texto = mcp.instructions or ""
    assert "una búsqueda por cada valor" in texto
    assert "límites, no una selección" in texto
