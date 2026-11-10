"""Regresión de derivados financieros al retirar datos de origen.

Solo memoria aislada y SQLite temporal; no usa servidores, APIs externas ni
migraciones. Comprueba invalidación, historial, eventos y exportación REST/MCP.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import closing

import pytest
from tests.soporte_acceso import cliente_autorizado

from app.main import app
from app.mcp.servidor import mcp
from app.perfil import calculos, store
from app.perfil.modelos import CALCULADOS, EstadoPerfil, Parche, PerfilRiesgo

pytestmark = pytest.mark.usefixtures("mcp_servicio")

C = "carmen-68"  # fixture ficticia en el proceso de pytest, nunca la demo viva
AHORRO = "financial.liquid_savings_eur"
GASTOS = "financial.fixed_monthly_costs_eur"
DEUDAS = "financial.debts_eur"
COLCHON = "financial.emergency_fund_months"
CAPACIDAD = "financial.loss_capacity_eur"
ORIGENES = [AHORRO, GASTOS, DEUDAS]
AUTOR = "advisor:asesor-calculos"


@pytest.fixture(params=["memoria", "sqlite"])
def perfil_inicial(almacen, request, tmp_path):
    if request.param == "sqlite":
        store.configurar("bd", f"sqlite:///{tmp_path / 'calculos.db'}")
    return store.cargar_fixture(C)


def cambiar(ruta, valor):
    return store.aplicar(C, [Parche(path=ruta, value=valor, source="advisor")],
                         "DATOS SIMULADOS: revisar origen financiero", AUTOR)


def sin_derivados_heredados(perfil):
    """Oráculo: mismos datos actuales, sin resultados de versiones anteriores.

    Reutiliza las fórmulas y reglas vigentes; no inventa otra política de riesgo.
    """
    limpio = perfil.model_copy(deep=True)
    for ruta in CALCULADOS:
        limpio.mifid.pop(ruta, None)
    calculos.recalcular(limpio)
    return limpio


def preparar_capacidad_decisiva():
    # 80.000 - 6*900 - 65.000 = 9.600: capacidad MODERADO frente a
    # tolerancia y plazo MUY_AGRESIVO. Evita que Carmen enmascare el defecto.
    return store.aplicar(C, [
        Parche(path="risk_tolerance.scenario_score", value=5, source="advisor"),
        Parche(path="objectives.o1.horizon_years", value=15, source="advisor"),
        Parche(path=DEUDAS, value=65000, source="advisor"),
    ], "DATOS SIMULADOS: capacidad determinante", AUTOR)


@pytest.mark.parametrize("origen", ORIGENES)
def test_retirar_origen_elimina_todos_sus_derivados(perfil_inicial, origen):
    assert perfil_inicial.mifid[COLCHON].value == 88.9
    assert perfil_inicial.mifid[CAPACIDAD].value == 74600

    nuevo = cambiar(origen, None)

    assert origen not in nuevo.mifid
    invalidos = {CAPACIDAD} if origen == DEUDAS else {COLCHON, CAPACIDAD}
    persistidos = store.perfil(C)
    restantes = invalidos.intersection(persistidos.mifid)
    assert not restantes, f"Derivados obsoletos tras retirar {origen}: {sorted(restantes)}"


@pytest.mark.parametrize("origen", ORIGENES)
def test_retirada_actualiza_completitud_y_conserva_historial(perfil_inicial, origen):
    anterior = store.perfil(C, perfil_inicial.version).model_dump(mode="json")
    historial = store.versiones(C)

    nuevo = cambiar(origen, None)

    assert nuevo.status == EstadoPerfil.draft
    assert not nuevo.assessments.suitability.complete
    assert origen in nuevo.assessments.suitability.missing
    assert nuevo.version == perfil_inicial.version + 1
    assert store.versiones(C)[:-1] == historial
    assert store.perfil(C, perfil_inicial.version).model_dump(mode="json") == anterior
    assert nuevo.assessments.appropriateness == perfil_inicial.assessments.appropriateness
    assert not calculos.restricciones(nuevo).usable


def test_sin_deudas_el_colchon_sigue_siendo_calculable(perfil_inicial):
    nuevo = cambiar(DEUDAS, None)
    assert nuevo.mifid[COLCHON].value == calculos.meses_colchon(80000, 900)
    assert nuevo.mifid[COLCHON].inputs == [AHORRO, GASTOS]


@pytest.mark.parametrize("origen,valor,colchon,capacidad", [
    (AHORRO, 8000, 8.9, 2600),
    (GASTOS, 1000, 80, 74000),
    (DEUDAS, 1000, 88.9, 73600),
])
@pytest.mark.parametrize("retirar_antes", [False, True], ids=["sustituir", "reponer"])
def test_origen_valido_recalcula_y_no_altera_versiones_previas(
        perfil_inicial, origen, valor, colchon, capacidad, retirar_antes):
    if retirar_antes:
        cambiar(origen, None)
    anterior = store.perfil(C)
    instantanea = anterior.model_dump(mode="json")

    nuevo = cambiar(origen, valor)

    assert nuevo.mifid[COLCHON].value == colchon
    assert nuevo.mifid[CAPACIDAD].value == capacidad
    assert nuevo.assessments.suitability.complete
    assert nuevo.status == EstadoPerfil.pending_validation
    assert store.perfil(C, anterior.version).model_dump(mode="json") == instantanea


@pytest.mark.parametrize("origen", ORIGENES)
def test_idoneidad_solo_depende_de_los_datos_actuales(perfil_inicial, origen):
    preparado = preparar_capacidad_decisiva()
    assert preparado.assessments.suitability.risk_profile == PerfilRiesgo.MODERADO

    nuevo = cambiar(origen, None)
    limpio = sin_derivados_heredados(nuevo)

    assert not nuevo.assessments.suitability.complete
    assert limpio.assessments.suitability.risk_profile == PerfilRiesgo.MUY_AGRESIVO
    assert nuevo.assessments == limpio.assessments, "Idoneidad usa capacidad de una versión anterior"


@pytest.mark.parametrize("origen", ORIGENES)
def test_api_restricciones_no_usa_derivados_heredados(perfil_inicial, origen):
    preparar_capacidad_decisiva()
    nuevo = cambiar(origen, None)
    esperado = calculos.restricciones(sin_derivados_heredados(nuevo))

    # No ejecutar lifespan ni abrir puertos: solo la API en este proceso.
    with closing(cliente_autorizado()) as api:
        perfil = api.get(f"/api/clients/{C}/profile")
        respuesta = api.get(f"/api/clients/{C}/constraints")
    assert perfil.status_code == respuesta.status_code == 200
    assert perfil.json()["version"] == nuevo.version
    actual = respuesta.json()
    assert actual["profile_version"] == nuevo.version
    assert actual["usable"] is False  # no se mezcla aquí la selección de activos anteriores
    assert actual == esperado.model_dump(mode="json"), "La API exporta restricciones basadas en datos obsoletos"


@pytest.mark.parametrize("origen", ORIGENES)
def test_eventos_anuncian_la_eliminacion_de_derivados(perfil_inicial, origen):
    cola = store.bus.suscribir(C)
    try:
        nuevo = cambiar(origen, None)
        eventos = []
        while not cola.empty():
            eventos.append(cola.get_nowait())
        eliminados = {e.datos["path"] for e in eventos
                      if e.tipo == "profile.patch" and e.datos["fact"] is None}
        invalidos = {CAPACIDAD} if origen == DEUDAS else {COLCHON, CAPACIDAD}
        assert origen in eliminados
        assert all(e.version == nuevo.version for e in eventos)
        assert invalidos <= eliminados, "El panel no recibe la retirada de resultados obsoletos"
    finally:
        store.bus.cancelar(C, cola)


@pytest.mark.parametrize("origen,colchon,capacidad", [
    (AHORRO, 0, 0),
    (GASTOS, 0, 80000),
    (DEUDAS, 88.9, 74600),
])
def test_cero_es_una_entrada_valida_y_conserva_las_formulas(
        perfil_inicial, origen, colchon, capacidad):
    nuevo = cambiar(origen, 0)
    assert nuevo.mifid[COLCHON].value == colchon
    assert nuevo.mifid[CAPACIDAD].value == capacidad
    assert nuevo.assessments.suitability.complete


@pytest.mark.parametrize("origen", ORIGENES)
def test_mcp_exporta_datos_actuales_y_conserva_el_historico(perfil_inicial, origen):
    anterior = preparar_capacidad_decisiva()
    instantanea = anterior.model_dump(mode="json")
    nuevo = cambiar(origen, None)

    async def consultar():
        async def llamar(nombre, **argumentos):
            resultado = await mcp.call_tool(nombre, {"client_id": C, **argumentos})
            bloques = resultado[0] if isinstance(resultado, tuple) else resultado
            return json.loads(bloques[0].text)

        return (
            await llamar("get_client_profile"),
            await llamar("get_investment_constraints"),
            await llamar("get_evidence", field=CAPACIDAD),
            await llamar("get_client_profile", version=anterior.version),
        )

    perfil, restricciones, evidencia, historico = asyncio.run(consultar())
    invalidos = {CAPACIDAD} if origen == DEUDAS else {COLCHON, CAPACIDAD}
    assert not invalidos.intersection(perfil["mifid"])
    assert perfil["version"] == restricciones["profile_version"] == nuevo.version
    assert perfil["assessments"] == nuevo.assessments.model_dump(mode="json")
    assert perfil["assessments"]["suitability"]["complete"] is False
    assert restricciones == calculos.restricciones(nuevo).model_dump(mode="json")
    assert restricciones["funds_query"]["max_risk"] == 7  # riesgo provisional vigente
    assert restricciones["usable"] is perfil["usable"] is False
    assert CAPACIDAD not in restricciones["evidence_refs"]
    assert all("Capacidad de pérdida" not in texto for texto in restricciones["rationale"])
    assert evidencia["error"] == "unknown_field"
    assert CAPACIDAD not in evidencia["available_fields"]
    historico.pop("usable")
    assert historico == instantanea
