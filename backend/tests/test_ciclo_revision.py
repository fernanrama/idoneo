"""Ciclo de una microentrevista MiFID sobre un perfil validado (reglas R1–R6 del 11/11/2026).

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Sin Claude ni
ElevenLabs: las escrituras simulan lo que haría el extractor. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import itertools

import pytest

from app.perfil import revision, store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
AHORRO, GASTOS = "financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur"
PLAZO, LIQUIDEZ = "objectives.o1.horizon_years", "objectives.o1.liquidity_need"
_turnos = itertools.count(1)


def decir(ruta: str, valor, texto: str = "DATOS SIMULADOS") -> "store.Perfil":
    """Lo que escribiría el extractor: un dato nuevo o, con el mismo valor, una confirmación con su cita."""
    f = store.perfil(C).mifid.get(ruta)
    misma = f is not None and f.value == valor
    p = Parche(path=ruta, value=valor, source=f.source if misma else "declared",
               confidence=f.confidence if misma else None,
               evidence=[Evidencia(session_id="s-micro", turn_id=f"t-{next(_turnos):03d}", t=(1.0, 2.0), quote=texto)])
    return store.aplicar(C, [p], "extractor · s-micro", "agent:extractor")


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def test_la_comparacion_parte_de_la_ultima_validacion_de_la_entidad(validada):
    decir(GASTOS, 900, "Los gastos siguen en novecientos")  # confirmación pura: versión active sin validar
    assert store.perfil(C).status == EstadoPerfil.active and store.perfil(C).version == validada.version + 1
    decir(PLAZO, 1, "Lo necesitaré el año que viene")
    c = revision.comparar(C)
    assert c.desde_version == validada.version
    assert {x.path for x in c.cambios} == {GASTOS, PLAZO}  # la confirmación y el cambio, frente a lo validado


# ---------- D2: la entidad valida desde review_due ----------

def test_review_due_se_valida_sin_otra_entrevista_y_recalcula(validada):
    p = decir(AHORRO, 10000, "Ahora me quedan unos diez mil")
    assert p.status == EstadoPerfil.review_due
    assert p.mifid["financial.loss_capacity_eur"].value == 10000 - 6 * 900  # recalculado con la entrada nueva
    v = store.validar(C, "asesor-07", [], version_esperada=p.version)
    assert v.status == EstadoPerfil.active and v.reason == "validated" and v.version == p.version + 1
    assert v.mifid["financial.loss_capacity_eur"].value == p.mifid["financial.loss_capacity_eur"].value


def test_no_se_valida_una_version_distinta_de_la_revisada(validada):
    vista = decir(AHORRO, 10000, "Ahora me quedan unos diez mil")
    decir(LIQUIDEZ, "high", "Y necesito 6.000 € en tres meses")  # llega otra respuesta mientras revisa
    antes = store.versiones(C)
    with pytest.raises(store.Conflicto, match="ha cambiado"):
        store.validar(C, "asesor-07", [], version_esperada=vista.version)
    assert store.versiones(C) == antes  # no se escribe nada


def test_review_due_incompleto_no_se_valida(validada):
    store.aplicar(C, [Parche(path="financial.debts_eur", value=None, source="declared")], "lo retira", "agent:extractor")
    assert store.perfil(C).status == EstadoPerfil.review_due
    with pytest.raises(store.Conflicto, match="Faltan datos obligatorios"):
        store.validar(C, "asesor-07", [])


def test_un_perfil_active_no_se_vuelve_a_validar(validada):
    with pytest.raises(store.Conflicto, match="active"):
        store.validar(C, "asesor-07", [])


def test_dos_asesores_a_la_vez_sobre_review_due(validada):
    import threading

    p = decir(AHORRO, 10000, "Ahora me quedan unos diez mil")
    barrera, resultados = threading.Barrier(2), []

    def validar(quien: str) -> None:
        barrera.wait(10)
        try:
            resultados.append(("ok", store.validar(C, quien, [], version_esperada=p.version).version))
        except store.Conflicto as e:
            resultados.append(("conflicto", str(e)))

    hilos = [threading.Thread(target=validar, args=(f"asesor-{i}",)) for i in (1, 2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(30)
    assert sorted(r[0] for r in resultados) == ["conflicto", "ok"]
    historial = store.versiones(C)
    assert [h["version"] for h in historial] == list(range(1, len(historial) + 1))  # sin huecos ni duplicados
    assert [h["reason"] for h in historial if h["version"] > p.version] == ["validated"]


def test_api_valida_review_due_con_version_esperada_y_exige_permiso(validada):
    from fastapi.testclient import TestClient

    from app.main import app
    from tests.soporte_acceso import cabeceras_cliente, cliente_autorizado

    p = decir(AHORRO, 10000, "Ahora me quedan unos diez mil")
    ruta = f"/api/clients/{C}/validate"
    sin_servicio = TestClient(app, headers=cabeceras_cliente(C, servicio=False))
    assert sin_servicio.post(ruta, json={"advisor_id": "a-1"}).status_code in (401, 403)  # solo la entidad
    c = cliente_autorizado(C)
    assert c.post(ruta, json={"advisor_id": "a-1", "expected_version": p.version - 1}).status_code == 409
    r = c.post(ruta, json={"advisor_id": "a-1", "expected_version": p.version})
    assert r.status_code == 200 and r.json()["status"] == "active"


# ---------- R1–R6: la revisión del cliente («¿Ha cambiado algo?») ----------

def servido():
    return store.restricciones_para_consumidor(C)


def test_1_abrir_la_revision_no_cambia_el_estado_ni_los_datos(validada):
    revision.abrir(C, ["planned_expense"])
    p = store.perfil(C)
    assert p.status == EstadoPerfil.active and p.reason == "review_requested:planned_expense"
    assert {r: f.value for r, f in p.mifid.items()} == {r: f.value for r, f in validada.mifid.items()}
    assert p.assessments == validada.assessments
    assert servido().usable and servido().pending_review is None


def test_2_confirmar_en_la_revision_mantiene_active_con_evidencia_nueva(validada):
    revision.abrir(C, ["planned_expense"])
    antes = store.perfil(C).mifid[AHORRO]
    p = decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    assert p.status == EstadoPerfil.active and servido().pending_review is None
    assert len(p.mifid[AHORRO].evidence) == len(antes.evidence) + 1 and p.mifid[AHORRO].confirmed_at is not None


def test_3_cambiar_un_dato_en_la_revision_pasa_a_review_due(validada):
    revision.abrir(C, ["planned_expense"])
    p = decir(LIQUIDEZ, "high", "Necesito 6.000 € en tres meses")
    assert p.status == EstadoPerfil.review_due and servido().pending_review.paths == [LIQUIDEZ]


def test_4_validar_tras_la_microentrevista_cierra_la_revision(validada):
    revision.abrir(C, ["planned_expense"])
    p = decir(LIQUIDEZ, "high", "Necesito 6.000 € en tres meses")
    v = store.validar(C, "asesor-07", [], version_esperada=p.version)
    assert v.status == EstadoPerfil.active and revision.en_curso(C) is None and servido().pending_review is None


def test_5_abandonar_sin_responder_no_altera_el_perfil(validada):
    revision.abrir(C, ["planned_expense"])
    store.crear_sesion(C, "text")  # abre la microentrevista y la deja sin contestar
    p = store.perfil(C)
    assert p.status == EstadoPerfil.active and p.assessments == validada.assessments
    assert revision.en_curso(C) is not None  # la revisión queda abierta, pero no invalida nada
    assert servido().usable and servido().pending_review is None


def test_6_una_confirmacion_no_reactiva_un_perfil_ya_invalidado(validada):
    decir(PLAZO, 1, "Lo necesitaré el año que viene")  # cambio previo: review_due
    revision.abrir(C, ["planned_expense"])
    assert store.perfil(C).status == EstadoPerfil.review_due  # abrir no lo reactiva
    p = decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    assert p.status == EstadoPerfil.review_due and servido().pending_review.paths == [PLAZO]


def test_7_las_alertas_anteriores_no_desaparecen(validada):
    from app.perfil.modelos import Alerta, EstadoAlerta, Flag

    store.anadir_alertas(C, [Alerta(id="a-previa", path=GASTOS, flag=Flag.needs_advisor,
                                    message="DATOS SIMULADOS: revisar los gastos")])
    revision.abrir(C, ["planned_expense"])
    p = decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    abiertas = [a.id for a in p.alerts if a.status == EstadoAlerta.open]
    assert "a-previa" in abiertas  # ni abrir la revisión ni confirmar la cierran; solo la validación


def test_10_los_resultados_y_las_restricciones_se_actualizan_al_validar(validada):
    revision.abrir(C, ["goal_change"])
    p = decir(PLAZO, 1, "Lo necesitaré el año que viene")
    filtros = lambda r: {f.field for f in r.post_filters}  # noqa: E731
    assert "fixed_income_term" not in filtros(servido())  # se sirve lo validado, con aviso
    assert servido().pending_review.paths == [PLAZO]
    from app.perfil import calculos
    assert "fixed_income_term" in filtros(calculos.restricciones(p))  # la versión nueva ya está recalculada
    store.validar(C, "asesor-07", [], version_esperada=p.version)
    assert "fixed_income_term" in filtros(servido()) and servido().pending_review is None


# ---------- R6: lo que reciben los consumidores mientras hay un cambio pendiente ----------

def test_r6_un_cambio_material_se_identifica_y_se_avisa(validada):
    decir(PLAZO, 1, "Lo necesitaré el año que viene")
    r = servido()
    assert r.pending_review.material == ["filter:fixed_income_term"]
    aviso = r.rationale[-1]
    assert "pueden estar desactualizadas" in aviso and PLAZO in aviso and "filter:fixed_income_term" in aviso


def test_r6_un_cambio_no_material_tambien_se_avisa(validada):
    decir("financial.net_monthly_income_eur", 800, "Me han bajado la pensión a ochocientos")
    r = servido()
    assert r.pending_review.material == [] and "no altera estas restricciones" in r.rationale[-1]


def test_r6_sin_revision_pendiente_no_hay_aviso(validada):
    from app.perfil import calculos

    assert servido().rationale == calculos.restricciones(store.perfil_para_consumidor(C)).rationale


def test_r6_rest_y_mcp_ven_lo_mismo(validada, mcp_servicio):
    import asyncio
    import json

    from app.mcp.servidor import mcp
    from tests.soporte_acceso import cliente_autorizado

    decir(PLAZO, 1, "Lo necesitaré el año que viene")
    rest = cliente_autorizado(C).get(f"/api/clients/{C}/constraints").json()
    res = asyncio.run(mcp.call_tool("get_investment_constraints", {"client_id": C}))
    por_mcp = json.loads((res[0] if isinstance(res, tuple) else res)[0].text)
    assert rest["pending_review"]["material"] == por_mcp["pending_review"]["material"] == ["filter:fixed_income_term"]
    assert rest["rationale"] == por_mcp["rationale"]
