"""Aceptación parcial de lo que proponen los agentes y errores visibles (main._procesar_turno).

Se simulan el extractor y el verificador (sus ficheros no se tocan). Cada test se ejecuta con todos los
almacenes. Reglas que se comprueban:
- cada parche y cada alerta se valida por separado: los válidos se guardan, los inválidos se rechazan;
- los requisitos del contrato 04 se mantienen (evidencia, rutas, tipos, nada calculado);
- todo rechazo y todo fallo de un agente queda visible en GET /api/sessions/{id} con su motivo;
- si un agente falla, el otro se ejecuta igualmente.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app
from tests.soporte_acceso import cliente_autorizado
from app.perfil import store
from app.perfil.modelos import Alerta, Evidencia, Flag, Parche, Turno

C = "carmen-68"
EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="Estudié FP y trabajé de maestra.")]
EV_JSON = [e.model_dump(mode="json") for e in EV]


@pytest.fixture
def entorno(monkeypatch):
    """API con Carmen cargada, una sesión con un turno del cliente y agentes simulables."""
    store.reiniciar()
    store.cargar_fixture(C)
    api = cliente_autorizado()
    sid = api.post("/api/sessions", json={"client_id": C}).json()["session_id"]
    store.anadir_turno(sid, Turno(speaker="client", text="Estudié FP", t_start=0, t_end=1))

    def agentes(extraer=None, verificar=None):
        async def vacio(*_):
            return []
        monkeypatch.setattr(main.extractor, "extraer", extraer or vacio)
        monkeypatch.setattr(main.verificador, "verificar", verificar or vacio)

    def procesar():
        asyncio.run(main._procesar_turno(sid))
        return api.get(f"/api/sessions/{sid}").json()["rejections"]

    return api, sid, agentes, procesar


def devuelve(valor):
    async def agente(*_):
        return valor
    return agente


def falla(mensaje):
    async def agente(*_):
        raise RuntimeError(mensaje)
    return agente


# ---------- aceptación parcial de parches ----------

def test_parches_validos_se_guardan_y_los_invalidos_se_ven(entorno):
    api, sid, agentes, procesar = entorno
    v0 = store.perfil(C).version
    agentes(extraer=devuelve([
        Parche(path="experience.education", value="FP", source="declared", evidence=EV),          # válido
        {"path": "experience.profession", "value": "maestra", "source": "declared", "evidence": EV_JSON},  # válido (dict)
        Parche(path="salud.diagnostico", value="x", source="declared", evidence=EV),               # ruta inexistente
        Parche(path="financial.debts_eur", value=1, source="declared"),                            # sin evidencia
        Parche(path="financial.loss_capacity_eur", value=1, source="declared", evidence=EV),       # calculado
        Parche(path="financial.debts_eur", value="mucho", source="declared", evidence=EV),         # tipo
        Parche(path="financial.debts_eur", value=1, source="advisor", evidence=EV),                # autoría
        {"path": "knowledge.etfs"},                                                                # mal formado
        "texto suelto",                                                                            # no es un parche
    ]))
    rechazos = procesar()

    p = store.perfil(C)
    assert p.version == v0 + 1  # los dos válidos, en una sola versión
    assert p.mifid["experience.education"].value == "FP" and p.mifid["experience.profession"].value == "maestra"
    assert p.mifid["financial.debts_eur"].value == 0  # ninguno de los inválidos llegó al perfil
    assert "salud.diagnostico" not in p.mifid
    assert [h["reason"] for h in store.versiones(C)][-1] == f"extractor · {sid}"

    assert len(rechazos) == 7 and all(r["origen"] == "extractor" and r["tipo"] == "parche" for r in rechazos)
    motivos = {(r["path"], r["motivo"]) for r in rechazos}
    assert any(path == "salud.diagnostico" and "desconocida" in m for path, m in motivos)
    assert any(path == "financial.debts_eur" and "evidencia" in m for path, m in motivos)
    assert any(path == "financial.loss_capacity_eur" and "calculado" in m for path, m in motivos)
    assert any(path == "financial.debts_eur" and "advisor" in m for path, m in motivos)
    assert any(path == "knowledge.etfs" and "no es un parche válido" in m for path, m in motivos)
    assert any(path is None and "no es un parche válido" in m for path, m in motivos)


def test_sin_errores_no_hay_rechazos(entorno):
    _, _, agentes, procesar = entorno
    agentes(extraer=devuelve([Parche(path="experience.education", value="FP", source="declared", evidence=EV)]))
    assert procesar() == []
    assert store.perfil(C).mifid["experience.education"].value == "FP"


def test_todos_invalidos_no_crea_version(entorno):
    _, _, agentes, procesar = entorno
    v0 = store.perfil(C).version
    agentes(extraer=devuelve([Parche(path="financial.debts_eur", value=1, source="declared")]))
    assert len(procesar()) == 1 and store.perfil(C).version == v0


# ---------- aceptación parcial de alertas ----------

def test_alertas_validas_se_guardan_y_las_invalidas_se_ven(entorno):
    _, _, agentes, procesar = entorno
    agentes(verificar=devuelve([
        Alerta(id="a-ok", path="objectives.o1.goal", flag=Flag.inconsistent, message="Revisar el objetivo"),
        {"id": "a-ok2", "path": None, "flag": "needs_advisor", "message": "Que lo mire una persona"},
        Alerta(id="a-mal", path="no.existe", flag=Flag.inconsistent, message="m"),
        {"id": "a-sin-flag", "path": "objectives.o1.goal", "message": "m"},
        Alerta(id="a-vacia", path=None, flag=Flag.inconsistent, message="   "),
    ]))
    rechazos = procesar()
    ids = {a.id for a in store.perfil(C).alerts}
    assert {"a-ok", "a-ok2"} <= ids and not {"a-mal", "a-sin-flag", "a-vacia"} & ids
    assert {(r["origen"], r["tipo"]) for r in rechazos} == {("verificador", "alerta")} and len(rechazos) == 3
    assert any(r["path"] == "no.existe" and "desconocida" in r["motivo"] for r in rechazos)
    assert any("no es una alerta válida" in r["motivo"] for r in rechazos)
    assert next(a for a in store.perfil(C).alerts if a.id == "a-ok").created_by == "agent:verifier"


# ---------- fallos de los agentes: visibles y aislados ----------

def test_si_falla_el_extractor_el_verificador_sigue(entorno):
    _, _, agentes, procesar = entorno
    agentes(extraer=falla("el modelo no respondió"),
            verificar=devuelve([Alerta(id="a-v", path="objectives.o1.goal", flag=Flag.inconsistent, message="m")]))
    rechazos = procesar()
    assert "a-v" in {a.id for a in store.perfil(C).alerts}
    assert [(r["origen"], r["tipo"]) for r in rechazos] == [("extractor", "error")]
    assert "el modelo no respondió" in rechazos[0]["motivo"]


def test_si_falla_el_verificador_los_parches_se_guardan(entorno):
    _, _, agentes, procesar = entorno
    agentes(extraer=devuelve([Parche(path="experience.education", value="FP", source="declared", evidence=EV)]),
            verificar=falla("tiempo agotado"))
    rechazos = procesar()
    assert store.perfil(C).mifid["experience.education"].value == "FP"
    assert [(r["origen"], r["tipo"]) for r in rechazos] == [("verificador", "error")]


def test_respuestas_que_no_son_listas(entorno):
    _, _, agentes, procesar = entorno
    agentes(extraer=devuelve({"path": "experience.education"}), verificar=devuelve("nada"))
    rechazos = procesar()
    assert [(r["origen"], r["tipo"]) for r in rechazos] == [("extractor", "error"), ("verificador", "error")]
    assert "en vez de una lista" in rechazos[0]["motivo"]


def test_fallo_al_guardar_queda_visible(entorno, monkeypatch):
    _, _, agentes, procesar = entorno
    agentes(extraer=devuelve([Parche(path="experience.education", value="FP", source="declared", evidence=EV)]))

    def aplicar_roto(*_, **__):
        raise store.Conflicto("demasiadas escrituras simultáneas")

    monkeypatch.setattr(store, "aplicar", aplicar_roto)
    rechazos = procesar()
    assert [(r["origen"], r["tipo"], r["path"]) for r in rechazos] == [("backend", "parche", "experience.education")]
    assert "demasiadas escrituras" in rechazos[0]["motivo"]


# ---------- visibilidad ----------

def test_los_rechazos_se_publican_en_el_bus_y_son_por_sesion(entorno):
    api, sid, agentes, procesar = entorno
    cola = store.bus.suscribir(C)
    try:
        agentes(extraer=devuelve([Parche(path="salud.x", value=1, source="declared", evidence=EV)]))
        procesar()
        eventos = []
        while not cola.empty():
            eventos.append(cola.get_nowait())
        assert [e.tipo for e in eventos] == ["item.rejected"] and eventos[0].datos["path"] == "salud.x"
    finally:
        store.bus.cancelar(C, cola)
    otra = api.post("/api/sessions", json={"client_id": C}).json()["session_id"]
    assert api.get(f"/api/sessions/{otra}").json()["rejections"] == []


def test_turno_de_sesion_inexistente_no_revienta(entorno):
    asyncio.run(main._procesar_turno("s-no-existe"))
