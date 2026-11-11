"""`pending_review` (§4.6 del diseño 06, opción B): se sirve el último `active` y se avisa de lo que está
en revisión. Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local).

Datos simulados: fixture carmen-68.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from tests.soporte_acceso import cliente_autorizado

from app.mcp.servidor import mcp
from app.perfil import store
from app.perfil.modelos import Alerta, EstadoPerfil, Evidencia, Flag, Parche

pytestmark = pytest.mark.usefixtures("mcp_servicio")

C = "carmen-68"
LIQUIDEZ, AHORRO, DEUDAS = "objectives.o1.liquidity_need", "financial.liquid_savings_eur", "financial.debts_eur"
EV = [Evidencia(session_id="s-1", turn_id="t-009", t=(3.0, 6.0),
                quote="Necesito 6.000 euros dentro de tres meses para una reforma")]


def extractor(ruta, valor):
    return store.aplicar(C, [Parche(path=ruta, value=valor, source="declared", evidence=EV)],
                         "extractor · s-1", "agent:extractor")


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def mcp_json(nombre: str, **args) -> dict:
    res = asyncio.run(mcp.call_tool(nombre, args))
    bloques = res[0] if isinstance(res, tuple) else res
    return json.loads(bloques[0].text)


# ---------- store ----------

def test_sin_revision_abierta_es_null(validada):
    r = store.restricciones_para_consumidor(C)
    assert r.usable and r.profile_version == validada.version and r.pending_review is None


def test_sin_perfil_activo_es_null(carmen):
    r = store.restricciones_para_consumidor(C)
    assert not r.usable and r.pending_review is None


def test_cambio_de_liquidez_se_sirve_el_activo_con_aviso(validada):
    nueva = extractor(LIQUIDEZ, "high")
    assert nueva.status == EstadoPerfil.review_due
    r = store.restricciones_para_consumidor(C)
    # Opción B: sigue siendo el perfil validado y usable, con sus filtros de antes…
    assert r.profile_version == validada.version and r.usable
    assert all(f.field != "redemption_lag_days" for f in r.post_filters)
    # …pero el consumidor sabe qué está en revisión y desde cuándo.
    p = r.pending_review
    assert p.paths == [LIQUIDEZ]
    assert (p.since_version, p.latest_version, p.latest_status) == (
        validada.version + 1, nueva.version, EstadoPerfil.review_due)
    assert p.opened_at == store.perfil(C, validada.version + 1).created_at


def test_una_confirmacion_no_abre_revision(validada):
    actual = store.perfil(C).mifid[AHORRO].value
    assert extractor(AHORRO, actual).status == EstadoPerfil.active  # D3: confirmación pura, sigue active
    assert store.restricciones_para_consumidor(C).pending_review is None  # mismo valor: nada en revisión


def test_los_calculados_no_aparecen(validada):
    extractor(AHORRO, 10000)
    assert store.restricciones_para_consumidor(C).pending_review.paths == [AHORRO]


def test_alertas_nuevas_y_orden_del_guion(validada):
    extractor(LIQUIDEZ, "high")
    store.anadir_alertas(C, [Alerta(id="a-deudas", path=DEUDAS, flag=Flag.inconsistent,
                                    message="DATOS SIMULADOS: dice no tener deudas y menciona un préstamo",
                                    evidence=EV)])
    assert store.revision_pendiente(C).paths == [DEUDAS, LIQUIDEZ]  # financial va antes que objectives


def test_sigue_durante_la_reentrevista_y_se_cierra_al_validar(validada):
    extractor(LIQUIDEZ, "high")
    store.crear_sesion(C)  # review_due → draft
    p = store.revision_pendiente(C)
    assert p.paths == [LIQUIDEZ] and p.latest_status == EstadoPerfil.draft
    revalidada = store.validar(C, "asesor-07", [])
    r = store.restricciones_para_consumidor(C)
    assert r.profile_version == revalidada.version and r.pending_review is None
    assert any(f.field == "redemption_lag_days" for f in r.post_filters)  # ahora sí, con la liquidez nueva


# ---------- API y MCP: todos ven lo mismo ----------

def test_api(validada):
    extractor(LIQUIDEZ, "high")
    c = cliente_autorizado(C)
    r = c.get(f"/api/clients/{C}/constraints").json()
    assert r["usable"] is True and r["pending_review"]["paths"] == [LIQUIDEZ]
    assert c.get(f"/api/clients/{C}/context").json()["pending_review"]["paths"] == [LIQUIDEZ]


def test_api_sin_revision(validada):
    c = cliente_autorizado(C)
    assert c.get(f"/api/clients/{C}/constraints").json()["pending_review"] is None
    assert c.get(f"/api/clients/{C}/context").json()["pending_review"] is None


def test_mcp(validada):
    extractor(LIQUIDEZ, "high")
    restricciones = mcp_json("get_investment_constraints", client_id=C)
    assert restricciones["usable"] is True and restricciones["pending_review"]["paths"] == [LIQUIDEZ]
    perfil = mcp_json("get_client_profile", client_id=C)
    assert perfil["version"] == validada.version and perfil["pending_review"]["paths"] == [LIQUIDEZ]
    assert mcp_json("get_client_context", client_id=C)["pending_review"]["paths"] == [LIQUIDEZ]
    # Con una versión concreta del historial no se calcula: es una lectura histórica.
    assert "pending_review" not in mcp_json("get_client_profile", client_id=C, version=validada.version)
