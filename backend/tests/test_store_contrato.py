"""Contrato de `store` (API pública de la PR #7 + correcciones de la revisión).

Cada test se ejecuta con todos los almacenes (memoria, SQLite y, si está configurado, Postgres local):
el comportamiento tiene que ser idéntico.
"""

from __future__ import annotations

import threading

import pytest

from app.perfil import calculos, store
from app.perfil.modelos import Alerta, EstadoAlerta, EstadoPerfil, Evidencia, Flag, Fuente, Parche, Turno

C = "carmen-68"
EV = [Evidencia(session_id="s-1", turn_id="t-001", t=(1.0, 2.0), quote="lo que dijo")]


def parche(ruta, valor, fuente="declared", **extra):
    return Parche(path=ruta, value=valor, source=fuente, evidence=EV, **extra)


# ---------- lo que la PR #7 ya hacía (resultados financieros intactos) ----------

def test_carmen_igual_que_en_la_pr7(carmen):
    s = carmen.assessments.suitability
    assert carmen.version == 1 and carmen.status == EstadoPerfil.pending_validation
    assert s.complete and s.risk_profile.value == "CONSERVADOR" and s.max_sri == 3
    r = calculos.restricciones(store.perfil_para_consumidor(C))
    assert r.portfolios_query == {"profile": "CONSERVADOR", "risk_max": 1}
    assert r.appropriateness["equity_funds"].value == "not_appropriate" and not r.usable


# ---------- validación estricta ----------

def test_entrada_invalida_no_escribe_nada(carmen):
    for malos, error in [
        ([parche("salud.diagnostico", "x")], store.DatoInvalido),
        ([parche("financial.debts_eur", "muchísimo")], store.DatoInvalido),
        ([parche("knowledge.etfs", "experto")], store.DatoInvalido),
        ([Parche(path="financial.debts_eur", value=1, source="declared")], store.DatoInvalido),  # sin evidencia
        ([parche("financial.debts_eur", 1, "advisor")], store.DatoInvalido),
        ([parche("financial.debts_eur", 1), parche("financial.loss_capacity_eur", 1)], store.Conflicto),
    ]:
        with pytest.raises(error):
            store.aplicar(C, malos, "x", "agent:extractor")
    assert store.perfil(C).version == carmen.version  # todo o nada


def test_reescribir_lo_mismo_no_crea_version(carmen):
    p = store.aplicar(C, [parche("experience.education", "FP")], "x", "agent:extractor")
    assert store.aplicar(C, [parche("experience.education", "FP")], "repetido", "agent:extractor").version == p.version


def test_marca_declarado_frente_a_demostrado(carmen):
    p = store.aplicar(C, [parche("knowledge.etfs", "none", "demonstrated", declared="high")], "x", "agent:extractor")
    assert p.mifid["knowledge.etfs"].flags == [Flag.declared_vs_demonstrated]


def test_alertas_sin_duplicados_y_con_autor(carmen):
    a = Alerta(id="a-test-1", path="objectives.o1.goal", flag=Flag.inconsistent, message="m")
    p1 = store.anadir_alertas(C, [a])
    assert p1.version == carmen.version + 1
    p2 = store.anadir_alertas(C, [a.model_copy(update={"id": "a-test-2"})])  # mismo flag y dato
    assert p2.version == p1.version
    assert store.anadir_alertas(C, [a]).version == p1.version  # mismo id
    nueva = next(x for x in p1.alerts if x.id == "a-test-1")
    assert nueva.created_by == "agent:verifier"
    assert Flag.inconsistent in p1.mifid["objectives.o1.goal"].flags
    with pytest.raises(store.DatoInvalido):
        store.anadir_alertas(C, [Alerta(id="a-3", path="no.existe", flag=Flag.inconsistent, message="m")])


# ---------- estados y validación del asesor ----------

def test_validar_registra_quien_cierra_las_alertas(carmen):
    p = store.validar(C, "asesor-07", [])
    assert p.status == EstadoPerfil.active and p.review.validated_by == "asesor-07"
    assert all(a.status == EstadoAlerta.resolved and a.resolved_by == "advisor:asesor-07" for a in p.alerts)


def test_no_se_revalida_un_activo(carmen):
    store.validar(C, "asesor-07", [])
    with pytest.raises(store.Conflicto):
        store.validar(C, "asesor-08", [])


def test_review_due_exige_reentrevista(carmen):
    store.validar(C, "asesor-07", [])
    p = store.aplicar(C, [parche("financial.debts_eur", 5000)], "nuevo préstamo", "agent:extractor")
    assert p.status == EstadoPerfil.review_due
    with pytest.raises(store.Conflicto):
        store.validar(C, "asesor-07", [])
    store.crear_sesion(C)  # empieza la entrevista corta
    p = store.perfil(C)
    assert p.status == EstadoPerfil.draft and p.reason == "reassessment_started"


def test_validar_no_modifica_la_entrada(carmen):
    cambio = Parche(path="financial.debts_eur", value=10, source="declared")
    store.validar(C, "asesor-07", [cambio])
    assert cambio.source == Fuente.declared
    assert store.perfil(C).mifid["financial.debts_eur"].source == Fuente.advisor


def test_validar_con_id_de_asesor_invalido(carmen):
    with pytest.raises(store.DatoInvalido):
        store.validar(C, "", [])


# ---------- versiones: nada se sobrescribe ----------

def test_versiones_anteriores_intactas(carmen):
    antes = store.perfil(C, 1).model_dump()
    store.aplicar(C, [parche("financial.debts_eur", 1000)], "cambio", "agent:extractor")
    store.validar(C, "asesor-07", [])
    assert store.perfil(C, 1).model_dump() == antes
    h = store.versiones(C)
    assert [v["version"] for v in h] == [1, 2, 3] and h[1]["author"] == "agent:extractor"


def test_reinicio_de_demo_no_borra_historial_ni_sirve_activos_viejos(carmen):
    store.validar(C, "asesor-07", [])
    assert calculos.restricciones(store.perfil_para_consumidor(C)).usable
    p = store.cargar_fixture(C)  # /api/demo/reset
    assert p.version == 3 and p.reason.startswith("demo_reset") and p.status == EstadoPerfil.pending_validation
    assert len(store.versiones(C)) == 3
    consumidor = store.perfil_para_consumidor(C)
    assert consumidor.version == 3 and not calculos.restricciones(consumidor).usable


def test_asegurar_fixture_no_pisa_datos(carmen):
    store.validar(C, "asesor-07", [])
    assert store.asegurar_fixture(C).status == EstadoPerfil.active


def test_nombres_y_ids_peligrosos():
    for nombre in ("../modelos", "carmen-68.json", "", "/etc/passwd"):
        with pytest.raises((store.DatoInvalido, store.NoEncontrado)):
            store.cargar_fixture(nombre)
    with pytest.raises(store.DatoInvalido):
        store.crear("../../fuera")
    with pytest.raises(store.NoEncontrado):
        store.perfil("nadie")


def test_escrituras_simultaneas_no_se_pierden(carmen):
    rutas = {"financial.debts_eur": 1, "financial.other_assets_eur": 2, "experience.education": "FP",
             "risk_tolerance.past_behaviour": "no vendió", "objectives.o1.amount_eur": 3000,
             "experience.profession": "maestra"}
    errores = []

    def escribir(r, v):
        try:
            store.aplicar(C, [parche(r, v)], f"hilo {r}", "agent:extractor")
        except Exception as e:  # pragma: no cover
            errores.append(e)

    hilos = [threading.Thread(target=escribir, args=rv) for rv in rutas.items()]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    p = store.perfil(C)
    assert not errores and p.version == 1 + len(rutas)
    assert all(p.mifid[r].value is not None for r in rutas)


# ---------- capa personal separada ----------

def test_capa_personal_separada_con_consentimiento(carmen):
    store.guardar_personal(C, {"exclusions": ["armas", "tabaco"]}, True, "advisor:asesor-07")
    p = store.perfil(C)
    assert p.personal["consent"]["given"] is True and p.personal["exclusions"] == ["armas", "tabaco"]
    filtros = {f.field for f in calculos.restricciones(store.perfil_para_consumidor(C)).post_filters}
    assert "top_sectors" in filtros
    versiones = len(store.versiones(C))
    assert store.borrar_personal(C) == 1
    assert store.perfil(C).personal == {} and len(store.versiones(C)) == versiones  # MiFID intacto
    filtros = {f.field for f in calculos.restricciones(store.perfil_para_consumidor(C)).post_filters}
    assert "top_sectors" not in filtros


def test_capa_personal_sin_consentimiento_no_guarda_datos(carmen):
    with pytest.raises(store.DatoInvalido):
        store.guardar_personal(C, {"exclusions": ["armas"]}, False, "system")
    with pytest.raises(store.DatoInvalido):
        store.guardar_personal(C, {"salud": "x"}, True, "system")
    store.guardar_personal(C, {}, False, "system")
    assert store.perfil(C).personal == {}


def test_la_capa_personal_no_entra_en_las_versiones(carmen):
    store.guardar_personal(C, {"exclusions": ["armas"]}, True, "system")
    p = store.aplicar(C, [parche("experience.education", "FP")], "x", "agent:extractor")
    assert p.personal  # se ve al leer...
    store.borrar_personal(C)
    assert store.perfil(C, p.version).personal == {}  # ...pero la versión guardada no la contiene


# ---------- sesiones ----------

def test_turnos_idempotentes_y_numerados(carmen):
    s = store.crear_sesion(C, "text")
    sid = s["session_id"]
    assert s["channel"] == "text"
    assert store.anadir_turno(sid, Turno(speaker="agent", text="Hola", t_start=0, t_end=1)).turn_id == "t-001"
    t = Turno(turn_id="t-x", speaker="client", text="Hola", t_start=1, t_end=2)
    store.anadir_turno(sid, t)
    store.anadir_turno(sid, t)  # reenvío
    turnos = store.sesion(sid)["turns"]
    assert [x.turn_id for x in turnos] == ["t-001", "t-x"]
    assert store.anadir_turno(sid, Turno(speaker="client", text="otra", t_start=3, t_end=4)).turn_id == "t-003"
    with pytest.raises(store.DatoInvalido):
        store.crear_sesion(C, "paloma")
    with pytest.raises(store.NoEncontrado):
        store.anadir_turno("s-nada", t)


def test_cierre_de_sesion_idempotente_y_vinculado_a_una_conversacion(carmen):
    sid = store.crear_sesion(C, "voice")["session_id"]
    assert store.finalizar_sesion(sid, "conv_una") is True
    assert store.finalizar_sesion(sid, "conv_una") is False
    sesion = store.sesion(sid)
    assert sesion["conversation_id"] == "conv_una" and sesion["ended_at"] is not None
    with pytest.raises(store.Conflicto):
        store.finalizar_sesion(sid, "conv_otra")
    with pytest.raises(store.Conflicto):
        store.anadir_turno(sid, Turno(speaker="client", text="tarde", t_start=1, t_end=2))


# ---------- eventos ----------

def test_eventos_para_el_panel(carmen):
    cola = store.bus.suscribir(C)
    try:
        store.aplicar(C, [parche("experience.education", "FP")], "x", "agent:extractor")
        tipos = []
        while not cola.empty():
            tipos.append(cola.get_nowait().tipo)
        assert tipos == ["profile.patch", "profile.status"]
    finally:
        store.bus.cancelar(C, cola)
