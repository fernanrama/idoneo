"""Finalizar la revisión del inversor (sesión) frente a validar el perfil MiFID (entidad).

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Sin Claude ni
ElevenLabs: las escrituras simulan lo que haría el extractor. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import itertools

import pytest

from app.perfil import store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
AHORRO, PLAZO = "financial.liquid_savings_eur", "objectives.o1.horizon_years"
_turnos = itertools.count(1)


def decir(ruta: str, valor, texto: str = "DATOS SIMULADOS"):
    f = store.perfil(C).mifid.get(ruta)
    misma = f is not None and f.value == valor
    p = Parche(path=ruta, value=valor, source=f.source if misma else "declared",
               confidence=f.confidence if misma else None,
               evidence=[Evidencia(session_id="s-cierre", turn_id=f"t-{next(_turnos):03d}", t=(1.0, 2.0), quote=texto)])
    return store.aplicar(C, [p], "extractor · s-cierre", "agent:extractor")


def huella(p):
    """Lo que no debe cambiar al cerrar: datos, evidencias, resultados, alertas y estado."""
    return ({r: (f.value, f.declared, len(f.evidence), f.confirmed_at) for r, f in p.mifid.items()},
            p.assessments.model_dump(), [(a.id, a.status) for a in p.alerts], p.status)


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


# ---------- store.cerrar_revision ----------

def test_cerrar_no_toca_datos_ni_estado(validada):
    p = decir(AHORRO, 80000, "Los ahorros siguen igual")  # confirmación: sigue active
    c = store.cerrar_revision(C, "review_closed:sin_cambios", p.version)
    assert c.version == p.version + 1 and c.reason == "review_closed:sin_cambios" and c.author == "system"
    assert huella(c) == huella(p) and c.status == EstadoPerfil.active


def test_cerrar_con_cambios_no_reactiva(validada):
    p = decir(PLAZO, 1, "Lo necesitaré el año que viene")
    c = store.cerrar_revision(C, "review_closed:pendiente_de_validacion", p.version)
    assert c.status == EstadoPerfil.review_due and huella(c) == huella(p)
    assert store.revision_pendiente(C).paths == [PLAZO]  # GPTadvisor sigue avisado


def test_cerrar_con_version_obsoleta_no_escribe(validada):
    p = decir(AHORRO, 80000, "Los ahorros siguen igual")
    decir(PLAZO, 1, "Lo necesitaré el año que viene")  # otra respuesta se adelanta
    antes = store.versiones(C)
    with pytest.raises(store.Conflicto, match="ha cambiado"):
        store.cerrar_revision(C, "review_closed:sin_cambios", p.version)
    assert store.versiones(C) == antes


def test_cerrar_exige_motivo(validada):
    with pytest.raises(store.DatoInvalido):
        store.cerrar_revision(C, " ", validada.version)


# ---------- revision.cerrar: finalizar la sesión del inversor ----------

LIQUIDEZ = "objectives.o1.liquidity_need"


def abrir():
    from app.perfil import revision

    return revision.abrir(C, ["planned_expense"])  # pregunta liquidez, confirma ahorro y plazo


def responder_todo(liquidez="low"):
    decir(LIQUIDEZ, liquidez, "Sobre la liquidez")
    decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    decir(PLAZO, 10, "Sigue siendo a diez años")


def test_solo_confirmaciones_se_finaliza_y_sigue_active(validada):
    from app.perfil import revision

    abrir()
    responder_todo()
    antes = store.perfil(C)
    assert antes.status == EstadoPerfil.active and revision.vista(revision.en_curso(C))["can_finish"] is True
    r = revision.cerrar(C)
    assert r["result"] == "sin_cambios" and r["status"] == "active" and r["pending_validation"] is False
    assert revision.en_curso(C) is None and huella(store.perfil(C)) == huella(antes)  # «Mi perfil» ya no la ve a medias


def test_con_cambios_se_finaliza_pero_espera_a_la_entidad(validada):
    from app.perfil import revision

    abrir()
    responder_todo(liquidez="high")
    r = revision.cerrar(C)
    assert r["result"] == "pendiente_de_validacion" and r["status"] == "review_due" and r["pending_validation"]
    assert revision.en_curso(C) is None
    assert store.revision_pendiente(C).paths == [LIQUIDEZ]  # GPTadvisor sigue avisado
    assert [x.path for x in revision.comparar(C).cambios if x.antes != x.ahora] == [LIQUIDEZ]  # la entidad lo ve
    assert store.validar(C, "asesor-07", []).status == EstadoPerfil.active  # y lo valida después (D2)


def test_no_se_finaliza_con_preguntas_pendientes(validada):
    from app.perfil import revision

    abrir()
    decir(LIQUIDEZ, "high", "Necesito 6.000 € en tres meses")  # faltan ahorro y plazo
    v = revision.vista(revision.en_curso(C))
    assert v["can_finish"] is False and v["blocking"] == [AHORRO, PLAZO]
    antes = store.versiones(C)
    with pytest.raises(store.Conflicto, match="faltan"):
        revision.cerrar(C)
    assert store.versiones(C) == antes and revision.en_curso(C) is not None


def test_una_revision_abandonada_se_retoma(validada):
    from app.perfil import revision

    abrir()
    decir(LIQUIDEZ, "low", "No, sigo sin necesitar el dinero")  # y se va
    r = revision.en_curso(C)
    assert r is not None and [q.path for q in r.pendientes] == [AHORRO, PLAZO]  # al volver, sigue donde lo dejó
    decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    decir(PLAZO, 10, "Sigue siendo a diez años")
    assert revision.cerrar(C)["result"] == "sin_cambios"


def test_finalizar_es_idempotente(validada):
    from app.perfil import revision

    abrir()
    responder_todo()
    primera = revision.cerrar(C)
    versiones = store.versiones(C)
    segunda = revision.cerrar(C)
    assert segunda["already_closed"] is True and segunda["version"] == primera["version"]
    assert store.versiones(C) == versiones  # no escribe otra vez


def test_sin_revision_abierta_no_escribe(validada):
    from app.perfil import revision

    r = revision.cerrar(C)
    assert r["already_closed"] is True and store.perfil(C).version == validada.version


def test_tras_finalizar_se_puede_abrir_otra(validada):
    from app.perfil import revision

    abrir()
    responder_todo()
    revision.cerrar(C)
    nueva = revision.abrir(C, ["windfall"])
    assert nueva.motivos == [revision.Motivo.windfall]  # no arrastra los motivos de la anterior


def test_finalizar_no_reactiva_un_perfil_ya_en_revision(validada):
    from app.perfil import revision

    decir(PLAZO, 3, "Lo quiero para dentro de tres años")  # cambio previo: review_due
    abrir()
    decir(LIQUIDEZ, "low", "No, sigo sin necesitar el dinero")
    decir(AHORRO, 80000, "Los ahorros siguen en ochenta mil")
    decir(PLAZO, 3, "Sí, a tres años")  # confirma el plazo ya cambiado
    r = revision.cerrar(C)
    assert r["result"] == "pendiente_de_validacion" and r["status"] == "review_due"
    assert store.revision_pendiente(C).paths == [PLAZO]  # el cambio previo sigue avisado


def test_dos_cierres_a_la_vez_escriben_un_solo_cierre(validada):
    import threading

    from app.perfil import revision

    abrir()
    responder_todo()
    barrera, resultados = threading.Barrier(2), []

    def cerrar():
        barrera.wait(10)
        resultados.append(revision.cerrar(C))

    hilos = [threading.Thread(target=cerrar) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(30)
    assert len(resultados) == 2 and all(r["closed"] for r in resultados)
    cierres = [v for v in store.versiones(C) if v["reason"].startswith("review_closed:")]
    assert len(cierres) == 1


# ---------- API ----------

def test_api_finalizar_la_revision(validada):
    from fastapi.testclient import TestClient

    from app.main import app
    from tests.soporte_acceso import cliente_autorizado

    ruta = f"/api/clients/{C}/review/close"
    assert TestClient(app).post(ruta).status_code == 401  # sin credencial del cliente, no
    c = cliente_autorizado(C)
    assert c.post(f"/api/clients/{C}/review", json={"reasons": ["planned_expense"]}).status_code == 201
    assert c.get(f"/api/clients/{C}/review").json()["can_finish"] is False
    pendiente = c.post(ruta)
    assert pendiente.status_code == 409 and "faltan" in pendiente.json()["detail"]
    responder_todo()
    vista = c.get(f"/api/clients/{C}/review").json()
    assert vista["can_finish"] is True and vista["blocking"] == []
    r = c.post(ruta)
    assert r.status_code == 200 and r.json()["result"] == "sin_cambios" and r.json()["status"] == "active"
    assert c.get(f"/api/clients/{C}/review").json() == {"open": False}
    otra = c.post(ruta)
    assert otra.status_code == 200 and otra.json()["already_closed"] is True
    assert c.get(f"/api/clients/{C}/constraints").json()["usable"] is True
