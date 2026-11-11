"""Microentrevista de revisión pedida por el cliente («Ha cambiado algo») y antes/después para la entidad.

Contrato: se ejecuta con cada almacén. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import pytest

from app.agentes import chat, extractor
from app.perfil import revision, store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche
from tests.soporte_acceso import cliente_autorizado

C = "carmen-68"
INGRESOS, ESTABILIDAD, GASTOS = ("financial.net_monthly_income_eur", "financial.income_stability",
                                 "financial.fixed_monthly_costs_eur")


def ev(cita: str) -> list[Evidencia]:
    return [Evidencia(session_id="s-rev", turn_id="t-002", t=(1.0, 2.0), quote=cita)]


def extraer(ruta, valor, cita):
    return store.aplicar(C, [Parche(path=ruta, value=valor, source="declared", confidence=0.9, evidence=ev(cita))],
                         "extractor · s-rev", "agent:extractor")


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


def test_catalogo_de_motivos_para_el_cliente():
    codigos = [o["code"] for o in revision.opciones()]
    assert codigos[0] == "income_change" and "goal_change" in codigos and len(codigos) == len(set(codigos))
    assert all(o["titulo"] and o["detalle"] and o["icono"] for o in revision.opciones())


def test_subida_de_sueldo_pregunta_solo_lo_necesario(validada):
    previa = revision.previsualizar(C, ["income_change"])
    assert [q.path for q in previa.preguntas] == [INGRESOS, ESTABILIDAD, GASTOS]
    assert [q.tipo.value for q in previa.preguntas] == ["repreguntar", "repreguntar", "confirmar"]
    assert previa.preguntas[2].valor_vigente == validada.mifid[GASTOS].value  # se confirma leyendo lo que consta
    assert store.perfil(C).version == validada.version  # previsualizar no escribe

    r = revision.abrir(C, ["income_change"])
    p = store.perfil(C)
    assert p.version == validada.version + 1 and p.status == EstadoPerfil.draft
    assert p.reason == "review_requested:income_change"
    assert {r: f.value for r, f in p.mifid.items()} == {r: f.value for r, f in validada.mifid.items()}
    assert r.desde_version == p.version and len(r.pendientes) == 3
    # Los consumidores siguen con el perfil validado y sin aviso: aún no ha cambiado nada.
    c = store.restricciones_para_consumidor(C)
    assert c.profile_version == validada.version and c.usable and c.pending_review is None
    # El entrevistador solo pide lo de la revisión, en frases y sin rutas.
    assert chat.pendientes(p, r) == [INGRESOS, ESTABILIDAD, GASTOS]
    guion = chat.guion_revision(r)
    assert "me han subido o bajado el sueldo" in guion and "consta" in guion and "financial." not in guion


def test_respuestas_y_confirmaciones_cierran_preguntas(validada):
    revision.abrir(C, ["income_change"])
    extraer(INGRESOS, 2600, "Ahora cobro unos 2.600 al mes")
    r = revision.en_curso(C)
    assert [q.respondida for q in r.preguntas] == [True, False, False]
    # Confirmar el mismo valor: el extractor lo deja pasar solo dentro de la revisión.
    actual = store.perfil(C).mifid[GASTOS]
    p = Parche(path=GASTOS, value=actual.value, source="declared", confidence=actual.confidence, evidence=ev("Sí, sigue igual"))
    assert extractor._protegido(actual, p) is True
    assert extractor._protegido(actual, p, frozenset({GASTOS})) is False
    store.aplicar(C, [p], "extractor · s-rev", "agent:extractor")
    assert [q.respondida for q in revision.en_curso(C).preguntas] == [True, False, True]
    # Pending_review avisa del ingreso cambiado, no de la confirmación.
    assert store.restricciones_para_consumidor(C).pending_review.paths == [INGRESOS]


def test_comparacion_antes_despues_y_efectos(validada):
    assert revision.comparar(C) is None
    revision.abrir(C, ["goal_change"])
    extraer("objectives.o1.horizon_years", 1, "Lo necesitaré el año que viene")
    c = revision.comparar(C)
    assert c.desde_version == validada.version and c.hasta_version == store.perfil(C).version
    assert [(x.path, x.antes, x.ahora) for x in c.cambios] == [
        ("objectives.o1.horizon_years", validada.mifid["objectives.o1.horizon_years"].value, 1)]
    assert c.cambios[0].cita == "Lo necesitaré el año que viene"
    # Carmen ya era CONSERVADOR (tolerancia 1); a 1 año aparece el filtro de renta fija a corto plazo.
    assert (c.perfil_antes, c.perfil_ahora) == ("CONSERVADOR", "CONSERVADOR")
    assert c.efectos == ["Cambia el filtro de renta fija a corto plazo (plazo)"]


def test_validar_cierra_la_revision(validada):
    revision.abrir(C, ["income_change"])
    extraer(INGRESOS, 2600, "Ahora cobro unos 2.600 al mes")
    store.validar(C, "asesor-07", [])
    assert revision.en_curso(C) is None and revision.comparar(C) is None


def test_ampliar_una_revision_abierta_suma_motivos(validada):
    revision.abrir(C, ["income_change"])
    r = revision.abrir(C, ["planned_expense", "income_change"])
    assert [m.value for m in r.motivos] == ["income_change", "planned_expense"]
    assert r.desde_version == validada.version + 1  # las respuestas cuentan desde la primera petición


def test_errores_claros(carmen):
    with pytest.raises(store.DatoInvalido):
        revision.previsualizar(C, ["next_review_due"])  # motivo interno, no del cliente
    with pytest.raises(store.DatoInvalido):
        revision.previsualizar(C, [])
    store.crear("cliente-a1b2c3d4e5f6")
    with pytest.raises(store.Conflicto, match="termina la entrevista"):
        revision.abrir("cliente-a1b2c3d4e5f6", ["income_change"])


# ---------- API ----------

def test_api_de_punta_a_punta(validada):
    c = cliente_autorizado()
    assert c.get("/api/review-reasons").json()[0]["code"] == "income_change"
    assert c.get(f"/api/clients/{C}/review").json() == {"open": False}
    previa = c.post(f"/api/clients/{C}/review/preview", json={"reasons": ["income_change"]}).json()
    assert previa["open"] and previa["remaining"] == 3 and previa["reasons"][0]["icono"] == "sueldo"
    assert c.post(f"/api/clients/{C}/review", json={"reasons": ["nada"]}).status_code == 422
    abierta = c.post(f"/api/clients/{C}/review", json={"reasons": ["income_change"]})
    assert abierta.status_code == 201 and abierta.json()["questions"][0]["path"] == INGRESOS
    assert c.get(f"/api/clients/{C}/review").json()["open"] is True
    assert c.get(f"/api/clients/{C}/changes").json() is None  # aún no ha cambiado ningún dato
    extraer(INGRESOS, 2600, "Ahora cobro unos 2.600 al mes")
    cambios = c.get(f"/api/clients/{C}/changes").json()
    assert cambios["cambios"][0]["path"] == INGRESOS and cambios["cambios"][0]["ahora"] == 2600


def test_api_exige_al_cliente(validada):
    from fastapi.testclient import TestClient

    from app.main import app
    anonimo = TestClient(app)
    for metodo, ruta in (("get", "review"), ("post", "review"), ("get", "changes")):
        r = getattr(anonimo, metodo)(f"/api/clients/{C}/{ruta}", **({"json": {"reasons": ["income_change"]}} if metodo == "post" else {}))
        assert r.status_code in (401, 404)
