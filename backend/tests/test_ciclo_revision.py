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
