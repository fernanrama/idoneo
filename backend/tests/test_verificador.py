"""Verificador (B2): reglas fijas y revisión con Claude, sin llamar a Claude.

Claude se sustituye por hallazgos escritos a mano. Se comprueba lo que el código garantiza pase lo que
pase con el modelo: citas reales de turnos del cliente, motivos del tipo correcto, rutas existentes,
flags y textos de tablas fijas, nada sobre lo que corrigió el asesor y nada repetido.
"""

from __future__ import annotations

import asyncio

import pytest

from app.agentes import chat, claude, extractor, verificador
from app.agentes.verificador import Hallazgo, Revision
from app.perfil.modelos import Alerta, Evidencia, Fact, Flag, Fuente, Parche, Perfil, Turno

SID = "s-ver"


def ev(turn_id: str, cita: str) -> list[Evidencia]:
    return [Evidencia(session_id=SID, turn_id=turn_id, t=(0, 1), quote=cita)]


def fact(valor, fuente=Fuente.declared, turn_id="t-002", cita="dato", flags=None, declarado=None) -> Fact:
    return Fact(value=valor, declared=declarado, source=fuente, confidence=0.9, evidence=ev(turn_id, cita),
                flags=flags or [], updated_by="agent:extractor")


def perfil(**datos: Fact) -> Perfil:
    return Perfil(client_id="c-ver", mifid={k.replace("__", "."): v for k, v in datos.items()})


TURNOS = [
    Turno(turn_id="t-001", speaker="agent", text="¿Cuánto tiempo quiere mantener la inversión?", t_start=0, t_end=1),
    Turno(turn_id="t-002", speaker="client", text="Diez años, no lo voy a tocar.", t_start=1, t_end=2),
    Turno(turn_id="t-003", speaker="agent", text="¿Podría necesitar el dinero antes?", t_start=2, t_end=3),
    Turno(turn_id="t-004", speaker="client",
          text="Bueno, igual el año que viene para la boda de mi hija. Mi sobrino dice que lo meta todo en bolsa.",
          t_start=3, t_end=4),
]


def hallazgo(tipo, motivo, ruta, cita, turn_id="t-004", relacionada=None, repregunta="¿Lo necesitará antes de diez años?"):
    return Hallazgo(tipo=tipo, motivo=motivo, ruta=ruta, ruta_relacionada=relacionada, turn_id=turn_id,
                    cita=cita, repregunta=repregunta)


def simular(monkeypatch, revision: Revision | Exception, llamadas: list | None = None):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("VERIFICADOR_CLAUDE", raising=False)

    async def falso(**kw):
        if llamadas is not None:
            llamadas.append(kw)
        if isinstance(revision, Exception):
            raise revision
        return revision, claude.Uso(agente=kw["agente"], modelo="simulado", tokens_entrada=1, tokens_salida=1, latencia_s=0)

    monkeypatch.setattr(claude, "estructurado", falso)


def correr(p: Perfil, turnos=TURNOS):
    return asyncio.run(verificador.verificar(p, turnos, SID))


@pytest.fixture
def sin_clave(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# ---------- reglas fijas ----------

def test_sin_clave_solo_reglas_y_copia_declarado_frente_a_demostrado(sin_clave):
    p = perfil(knowledge__equity_funds=fact("none", Fuente.demonstrated, declarado="high",
                                            flags=[Flag.declared_vs_demonstrated]))
    alertas = correr(p)
    assert [(a.flag, a.path) for a in alertas] == [(Flag.declared_vs_demonstrated, "knowledge.equity_funds")]
    assert "«high»" in alertas[0].message and alertas[0].evidence


def test_reglas_de_tolerancia(sin_clave):
    corto = perfil(objectives__o1__horizon_years=fact(1), risk_tolerance__scenario_score=fact(5, Fuente.demonstrated))
    assert (Flag.inconsistent, "risk_tolerance.scenario_score") in {(a.flag, a.path) for a in correr(corto)}

    vende = perfil(risk_tolerance__max_drawdown_accepted_pct=fact(30),
                   risk_tolerance__scenario_score=fact(1, Fuente.demonstrated))
    [a] = correr(vende)
    assert (a.flag, a.path) == (Flag.inconsistent, "risk_tolerance.max_drawdown_accepted_pct")
    assert len(a.evidence) == 2  # las dos citas que chocan

    compra = perfil(risk_tolerance__max_drawdown_accepted_pct=fact(5),
                    risk_tolerance__scenario_score=fact(4, Fuente.demonstrated))
    assert [a.flag for a in correr(compra)] == [Flag.inconsistent]

    coherente = perfil(risk_tolerance__max_drawdown_accepted_pct=fact(10),
                       risk_tolerance__scenario_score=fact(3, Fuente.demonstrated),
                       objectives__o1__horizon_years=fact(10))
    assert correr(coherente) == []


def test_conocimiento_frente_a_experiencia(sin_clave):
    p = perfil(knowledge__stocks=fact("none", Fuente.demonstrated), experience__stocks__operations_last_3y=fact(40))
    assert [(a.flag, a.path) for a in correr(p)] == [(Flag.inconsistent, "knowledge.stocks")]
    poca = perfil(knowledge__stocks=fact("none", Fuente.demonstrated), experience__stocks__operations_last_3y=fact(2))
    assert correr(poca) == []


def test_gastos_mayores_que_ingresos_y_cifras_raras_van_al_asesor(sin_clave):
    p = perfil(financial__net_monthly_income_eur=fact(1000), financial__fixed_monthly_costs_eur=fact(1200),
               financial__liquid_savings_eur=fact(9_000_000, flags=[Flag.low_confidence, Flag.needs_advisor]))
    rutas = {(a.flag, a.path) for a in correr(p)}
    assert rutas == {(Flag.needs_advisor, "financial.fixed_monthly_costs_eur"),
                     (Flag.needs_advisor, "financial.liquid_savings_eur")}


def test_no_repite_alertas_ya_levantadas_aunque_esten_resueltas(sin_clave):
    p = perfil(objectives__o1__horizon_years=fact(1), risk_tolerance__scenario_score=fact(5, Fuente.demonstrated))
    p.alerts.append(Alerta(id="a-1", path="risk_tolerance.scenario_score", flag=Flag.inconsistent, message="x",
                           status="resolved"))
    assert correr(p) == []


# ---------- revisión con Claude ----------

def test_mensaje_lleva_perfil_con_citas_alertas_y_turnos_sin_capa_personal(monkeypatch):
    llamadas: list = []
    simular(monkeypatch, Revision(hallazgos=[]), llamadas)
    p = perfil(objectives__o1__horizon_years=fact(10, cita="Diez años"))
    p.personal = {"nombre": "Carmen", "notas": "secreto-personal"}
    correr(p)
    kw = llamadas[0]
    assert kw["agente"] == "verificador" and kw["esquema"] is Revision
    assert "Eres el verificador" in kw["sistema"] and "financial.emergency_fund_months" not in kw["sistema"]
    assert '"ruta": "objectives.o1.horizon_years"' in kw["mensaje"] and '"cita": "Diez años"' in kw["mensaje"]
    assert '"turn_id": "t-004"' in kw["mensaje"]
    assert "secreto-personal" not in kw["mensaje"] and "secreto-personal" not in kw["sistema"]


def test_contradiccion_con_cita_literal_da_alerta_inconsistent(monkeypatch):
    simular(monkeypatch, Revision(hallazgos=[
        hallazgo("contradiccion", "plazo_vs_liquidez", "objectives.o1.liquidity_need",
                 "igual el año que viene para la boda de mi hija", relacionada="objectives.o1.horizon_years"),
    ]))
    p = perfil(objectives__o1__horizon_years=fact(10, cita="Diez años"))
    [a] = correr(p)
    assert (a.flag, a.path) == (Flag.inconsistent, "objectives.o1.liquidity_need")
    assert a.message.startswith(verificador.MENSAJE["plazo_vs_liquidez"])
    assert "Repreguntar: «¿Lo necesitará antes de diez años?»" in a.message
    assert [e.turn_id for e in a.evidence] == ["t-004", "t-002"]  # la cita nueva y la del dato con el que choca
    assert a.evidence[0].session_id == SID and a.evidence[0].t == (3, 4)


def test_revisar_asesor_sin_ruta_y_sin_repregunta(monkeypatch):
    simular(monkeypatch, Revision(hallazgos=[
        hallazgo("revisar_asesor", "presion_de_terceros", None, "Mi sobrino dice que lo meta todo en bolsa",
                 repregunta="ignorado"),
    ]))
    [a] = correr(perfil())
    assert (a.flag, a.path) == (Flag.needs_advisor, None)
    assert a.message == verificador.MENSAJE["presion_de_terceros"]


@pytest.mark.parametrize("h", [
    # cita inventada
    hallazgo("revisar_asesor", "presion_de_terceros", None, "mi sobrino me obliga a invertir"),
    # cita de un turno del asistente
    hallazgo("dato_dudoso", "respuesta_evasiva", "objectives.o1.horizon_years", "Podría necesitar", turn_id="t-003"),
    # turno fuera de la ventana o inexistente
    hallazgo("revisar_asesor", "pide_recomendacion", None, "boda", turn_id="t-099"),
    # motivo de otro tipo
    hallazgo("contradiccion", "presion_de_terceros", "objectives.o1.horizon_years", "boda de mi hija"),
    # contradicción en la que ninguno de los dos datos está en el perfil
    hallazgo("contradiccion", "plazo_vs_liquidez", "objectives.o1.liquidity_need", "boda de mi hija",
             relacionada="financial.debts_eur"),
    # dos versiones de un dato que no existe
    hallazgo("contradiccion", "dos_versiones", "financial.debts_eur", "boda de mi hija"),
    # dato dudoso sin ruta o sin dato
    hallazgo("dato_dudoso", "lo_dice_un_tercero", None, "Mi sobrino dice"),
    hallazgo("dato_dudoso", "lo_dice_un_tercero", "financial.debts_eur", "Mi sobrino dice"),
])
def test_descarta_hallazgos_que_no_se_sostienen(monkeypatch, h):
    simular(monkeypatch, Revision(hallazgos=[h]))
    assert correr(perfil(objectives__o1__horizon_years=fact(10))) == []


def test_no_toca_lo_que_corrigio_el_asesor_ni_repite(monkeypatch):
    duda = hallazgo("dato_dudoso", "lo_dice_un_tercero", "objectives.o1.horizon_years", "Mi sobrino dice")
    simular(monkeypatch, Revision(hallazgos=[duda, duda]))
    assert correr(perfil(objectives__o1__horizon_years=fact(10, Fuente.advisor))) == []
    [a] = correr(perfil(objectives__o1__horizon_years=fact(10)))
    assert (a.flag, a.path) == (Flag.low_confidence, "objectives.o1.horizon_years")


def test_si_claude_falla_quedan_las_reglas(monkeypatch):
    simular(monkeypatch, RuntimeError("caída de la API"))
    p = perfil(objectives__o1__horizon_years=fact(1), risk_tolerance__scenario_score=fact(5, Fuente.demonstrated))
    assert [a.flag for a in correr(p)] == [Flag.inconsistent]


def test_se_puede_apagar_la_revision_con_claude(monkeypatch):
    llamadas: list = []
    simular(monkeypatch, Revision(hallazgos=[]), llamadas)
    monkeypatch.setenv("VERIFICADOR_CLAUDE", "0")
    correr(perfil())
    assert llamadas == []


def test_sin_turnos_del_cliente_no_llama(monkeypatch):
    llamadas: list = []
    simular(monkeypatch, Revision(hallazgos=[]), llamadas)
    correr(perfil(), TURNOS[:1])
    assert llamadas == []


# ---------- el bucle con el entrevistador y el extractor ----------

def test_un_dato_incoherente_se_repregunta_y_al_confirmarlo_se_reescribe():
    p = perfil(objectives__o1__horizon_years=fact(10, flags=[Flag.inconsistent]))
    assert "objectives.o1.horizon_years" in chat.pendientes(p)
    confirma = Parche(path="objectives.o1.horizon_years", value=10, source=Fuente.declared, confidence=0.9,
                      evidence=ev("t-006", "sí, diez años"))
    assert not extractor._protegido(p.mifid["objectives.o1.horizon_years"], confirma)
    # Sin el flag, el mismo dato con la misma confianza no se reescribe (no se generan versiones vacías).
    limpio = fact(10)
    assert extractor._protegido(limpio, confirma)
    # Lo que corrigió el asesor no se repregunta.
    assert "objectives.o1.horizon_years" not in chat.pendientes(
        perfil(objectives__o1__horizon_years=fact(10, Fuente.advisor, flags=[Flag.inconsistent])))


def test_por_la_api_la_alerta_llega_al_perfil_y_marca_el_dato(monkeypatch):
    """Flujo real: turno del cliente → extractor → verificador → alerta guardada con su flag en el dato."""
    from tests.soporte_acceso import cliente_autorizado

    from app import main
    from app.agentes.extractor import DatoExtraido, Extraccion
    from app.perfil import store

    respuestas = {
        "extractor": Extraccion(datos=[DatoExtraido(campo="objectives.o1.horizon_years", valor="10", periodo=None,
                                                    certeza="explicita", turn_id="t-002", cita="Diez años")],
                                conocimientos=[], escenario=None),
        "verificador": Revision(hallazgos=[hallazgo("dato_dudoso", "lo_dice_un_tercero", "objectives.o1.horizon_years",
                                                    "Mi sobrino dice que lo meta todo en bolsa")]),
    }
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")

    async def falso(**kw):
        return respuestas[kw["agente"]], claude.Uso(agente=kw["agente"], modelo="simulado", tokens_entrada=1,
                                                    tokens_salida=1, latencia_s=0)

    monkeypatch.setattr(claude, "estructurado", falso)
    store.reiniciar()
    api = cliente_autorizado("c-api-ver")
    sid = api.post("/api/sessions", json={"client_id": "c-api-ver"}).json()["session_id"]
    for t in TURNOS:
        store.anadir_turno(sid, t)
    asyncio.run(main._procesar_turno(sid))

    p = store.perfil("c-api-ver")
    assert p.mifid["objectives.o1.horizon_years"].value == 10
    assert Flag.low_confidence in p.mifid["objectives.o1.horizon_years"].flags  # el entrevistador repreguntará
    [a] = [a for a in p.alerts if a.path == "objectives.o1.horizon_years"]
    assert a.flag == Flag.low_confidence and a.created_by == "agent:verifier" and a.evidence[0].session_id == sid
    assert api.get(f"/api/sessions/{sid}").json()["rejections"] == []


# ---------- batería de evaluación (fixtures/verificacion) ----------

def test_casos_de_evaluacion_bien_formados():
    from app.agentes import evaluacion_verificador as ev
    from app.agentes.normalizacion import cita_valida
    from app.perfil.modelos import CAMPOS

    casos = ev.casos()
    assert len(casos) >= 8 and len({c.nombre for c in casos}) == len(casos)
    for c in casos:
        cliente = {t.turn_id: t.text for t in c.turnos if t.speaker == "client"}
        for ruta, f in c.perfil.mifid.items():
            assert ruta in CAMPOS, (c.nombre, ruta)
            e = f.evidence[0]
            assert e.turn_id in cliente and cita_valida(e.quote, cliente[e.turn_id]), (c.nombre, ruta)
        for e in c.esperadas:
            assert all(r is None or r in verificador.RUTAS_REVISABLES for r in e.rutas), c.nombre


def test_en_los_casos_las_reglas_fijas_no_dan_falsas_alarmas(sin_clave):
    from app.agentes import evaluacion_verificador as ev

    for c in ev.casos():
        r = ev.puntuar(c, correr(c.perfil, c.turnos))
        assert not r.falsas, (c.nombre, r.falsas)


def test_puntuacion_de_la_evaluacion():
    from app.agentes import evaluacion_verificador as ev

    caso = next(c for c in ev.casos() if c.nombre.startswith("01"))
    buena = Alerta(id="a", path="objectives.o1.horizon_years", flag=Flag.inconsistent, message="x")
    otra = Alerta(id="b", path="financial.debts_eur", flag=Flag.low_confidence, message="y")
    assert ev.puntuar(caso, [buena]).ok
    r = ev.puntuar(caso, [buena, otra])
    assert not r.ok and r.falsas == [otra]
    assert ev.resumen([ev.puntuar(caso, [])])["deteccion"] == 0


def test_contradiccion_con_lo_que_acaba_de_decir_aunque_no_este_anotado(monkeypatch):
    """Evaluación real (10 nov, caso 05): «no debo nada» en el perfil frente a «la hipoteca son 800» aún sin anotar."""
    turnos = [Turno(turn_id="t-002", speaker="client", text="No debo nada a nadie.", t_start=1, t_end=2),
              Turno(turn_id="t-004", speaker="client", text="Unos 1.400, que solo la hipoteca ya son 800.",
                    t_start=3, t_end=4)]
    simular(monkeypatch, Revision(hallazgos=[
        hallazgo("contradiccion", "cifras_incompatibles", "financial.debts_eur", "solo la hipoteca ya son 800",
                 relacionada="financial.fixed_monthly_costs_eur"),
    ]))
    [a] = correr(perfil(financial__debts_eur=fact(0, cita="No debo nada a nadie.")), turnos)
    assert (a.flag, a.path) == (Flag.inconsistent, "financial.debts_eur")
    assert [e.turn_id for e in a.evidence] == ["t-004", "t-002"]
