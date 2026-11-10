"""Extractor (B1): la parte determinista y la integración con la API, sin llamar a Claude.

Claude se sustituye por una respuesta grabada a mano (`RESPUESTA_CARMEN`) sobre la entrevista simulada de
Carmen (fixtures/entrevistas/carmen-68.json). Se comprueba lo que el código garantiza pase lo que pase con
el modelo: citas reales, tiempos del turno, confianza de la rúbrica, datos protegidos y nada calculado.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from tests.soporte_acceso import cliente_autorizado

from app import main
from app.agentes import claude, extractor, rubrica
from app.agentes.extractor import ConocimientoExtraido, DatoExtraido, EscenarioExtraido, Extraccion
from app.main import app
from app.perfil import store
from app.perfil.modelos import CALCULADOS, Flag, Fuente, Parche, Perfil, Turno

C = "carmen-68"
ENTREVISTA = json.loads((Path(__file__).parents[1] / "fixtures" / "entrevistas" / "carmen-68.json").read_text("utf-8"))
TURNOS = [Turno(**t) for t in ENTREVISTA["turns"]]


def dato(campo, valor, turn_id, cita, certeza="explicita", periodo=None):
    return DatoExtraido(campo=campo, valor=valor, periodo=periodo, certeza=certeza, turn_id=turn_id, cita=cita)


RESPUESTA_CARMEN = Extraccion(
    datos=[
        dato("disclosures.ai_notice_ack", "true", "t-002", "Sí, de acuerdo"),
        dato("objectives.o1.goal", "complementar la pensión", "t-004", "para complementar la pensión"),
        dato("objectives.o1.horizon_years", "10", "t-006", "Para los próximos diez años, más o menos.", "aproximada"),
        dato("financial.net_monthly_income_eur", "1450", "t-008", "Cobro unos mil cuatrocientos cincuenta de pensión", "aproximada"),
        dato("financial.fixed_monthly_costs_eur", "900", "t-008", "Entre luz, comunidad y la compra, unos novecientos", "aproximada"),
        dato("financial.liquid_savings_eur", "80000", "t-010", "Tengo ochenta mil en depósitos."),
        dato("financial.debts_eur", "0", "t-010", "No debo nada"),
        dato("risk_tolerance.past_behaviour", "vendería todo ante una caída del 20 %", "t-014", "lo saco todo"),
        dato("sustainability.preference", "none", "t-016", "Eso me da igual"),
    ],
    conocimientos=[
        ConocimientoExtraido(familia="equity_funds", nivel_declarado="high", resultado_comprobacion="incorrecta",
                             turn_id="t-012", cita="Eso no puede pasar, el fondo es del banco."),
    ],
    escenario=EscenarioExtraido(reaccion="vender_todo", certeza="explicita", puntuacion_declarada=None,
                                turn_id="t-014", cita="Si baja un veinte por ciento, lo saco todo."),
)


def vacio(cid="nuevo-1") -> Perfil:
    return Perfil(client_id=cid)


def por_ruta(parches: list[Parche]) -> dict[str, Parche]:
    return {p.path: p for p in parches}


# ---------- citas y conversión ----------

@pytest.mark.parametrize("cita,texto,ok", [
    ("Eso no puede pasar", "Eso no puede pasar, el fondo es del banco.", True),
    ("eso NO puede pasar el fondo", "Eso no puede pasar, el fondo es del banco.", True),  # mayúsculas y comas
    ("«lo saco todo»", "Si baja un veinte por ciento, lo saco todo.", True),
    ("lo vendo todo", "Si baja un veinte por ciento, lo saco todo.", False),  # parecido no es literal
    ("", "cualquier cosa", False),
])
def test_cita_debe_ser_literal(cita, texto, ok):
    assert extractor.cita_valida(cita, texto) is ok


def test_convertir_a_los_tipos_del_catalogo():
    from app.agentes.normalizacion import convertir

    assert convertir("financial.liquid_savings_eur", "80000").valor == 80000.0
    assert convertir("disclosures.ai_notice_ack", "true").valor is True
    assert convertir("disclosures.ai_notice_ack", "No").valor is False
    assert convertir("sustainability.min_sfdr_article", "8").valor == 8
    with pytest.raises(ValueError):
        convertir("disclosures.ai_notice_ack", "quizá")
    with pytest.raises(ValueError):
        convertir("financial.debts_eur", "mucho")


def test_el_modelo_no_puede_ni_pedir_datos_calculados():
    assert not CALCULADOS & set(extractor.CAMPOS_DATO)
    esquema = json.dumps(Extraccion.model_json_schema())
    assert all(c not in esquema for c in CALCULADOS)


# ---------- parte determinista sobre la entrevista de Carmen ----------

def test_carmen_da_los_datos_clave_con_evidencia_y_rubrica():
    parches = por_ruta(extractor.a_parches(RESPUESTA_CARMEN, TURNOS, vacio(), "s-1"))

    rv = parches["knowledge.equity_funds"]
    assert (rv.value, rv.declared, rv.source) == ("none", "high", Fuente.demonstrated)
    assert rv.confidence == 0.85 and rv.confidence_basis == "rubric:knowledge.equity_funds:v2"
    assert rv.evidence[0].quote == "Eso no puede pasar, el fondo es del banco."
    assert rv.evidence[0].turn_id == "t-012" and rv.evidence[0].t == (57.0, 61.0)

    esc = parches["risk_tolerance.scenario_score"]
    assert (esc.value, esc.source, esc.confidence) == (1, Fuente.demonstrated, 0.85)

    assert parches["financial.net_monthly_income_eur"].value == 1450.0
    assert parches["financial.net_monthly_income_eur"].confidence == rubrica.CONFIANZA_CERTEZA["aproximada"]
    assert parches["financial.debts_eur"].value == 0.0
    assert parches["disclosures.ai_notice_ack"].value is True
    assert parches["risk_tolerance.past_behaviour"].source == Fuente.demonstrated

    # Todos pasan las reglas del store tal cual (tipos, autoría, evidencia).
    for p in parches.values():
        store.comprobar_parche(p, "agent:extractor")


def test_cita_inventada_o_de_turno_del_asistente_se_descarta():
    respuesta = Extraccion(
        datos=[
            dato("financial.debts_eur", "0", "t-010", "no tengo ninguna deuda"),          # no está en el turno
            dato("objectives.o1.goal", "pensión", "t-003", "¿Para qué le gustaría invertir"),  # turno del asistente
            dato("financial.liquid_savings_eur", "80000", "t-999", "ochenta mil"),       # turno inexistente
        ],
        conocimientos=[], escenario=None,
    )
    assert extractor.a_parches(respuesta, TURNOS, vacio(), "s-1") == []


def test_dato_inferido_lleva_low_confidence():
    respuesta = Extraccion(
        datos=[dato("objectives.o1.liquidity_need", "low", "t-004", "complementar la pensión", "inferida")],
        conocimientos=[ConocimientoExtraido(familia="etfs", nivel_declarado="medium", resultado_comprobacion=None,
                                            turn_id="t-004", cita="complementar la pensión")],
        escenario=None,
    )
    parches = por_ruta(extractor.a_parches(respuesta, TURNOS, vacio(), "s-1"))
    assert Flag.low_confidence in parches["objectives.o1.liquidity_need"].flags
    # Conocimiento solo declarado: fuente declared y por debajo del umbral (hay que comprobarlo).
    etf = parches["knowledge.etfs"]
    assert etf.source == Fuente.declared and Flag.low_confidence in etf.flags


def test_no_pisa_al_asesor_ni_lo_demostrado_ni_repite():
    from app.perfil.modelos import ahora
    from app.perfil.store import _fact  # helper interno, solo para montar el perfil del test

    perfil = vacio("x")
    for p in extractor.a_parches(RESPUESTA_CARMEN, TURNOS, vacio(), "s-1"):
        perfil.mifid[p.path] = _fact(store.comprobar_parche(p, "agent:extractor"), "agent:extractor", ahora())
    perfil.mifid["financial.liquid_savings_eur"] = perfil.mifid["financial.liquid_savings_eur"].model_copy(
        update={"source": Fuente.advisor, "value": 75000.0})

    otra = Extraccion(
        datos=[dato("financial.liquid_savings_eur", "80000", "t-010", "Tengo ochenta mil")],  # asesor: no se pisa
        conocimientos=[ConocimientoExtraido(familia="equity_funds", nivel_declarado="high", resultado_comprobacion=None,
                                            turn_id="t-012", cita="Eso no puede pasar")],  # demostrado: no se pisa
        escenario=None,
    )
    assert extractor.a_parches(otra, TURNOS, perfil, "s-1") == []
    # Repetir exactamente lo mismo no genera parches (ni versiones vacías).
    sin_asesor = RESPUESTA_CARMEN.model_copy(update={"datos": [d for d in RESPUESTA_CARMEN.datos
                                                                if d.campo != "financial.liquid_savings_eur"]})
    assert extractor.a_parches(sin_asesor, TURNOS, perfil, "s-1") == []


# ---------- extraer(): sin clave y con Claude simulado ----------

def test_sin_clave_devuelve_lista_vacia(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert asyncio.run(extractor.extraer(TURNOS, vacio(), "s-1")) == []


def simular_claude(monkeypatch, respuesta: Extraccion, llamadas: list | None = None):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")

    async def falso(**kw):
        if llamadas is not None:
            llamadas.append(kw)
        return respuesta, claude.Uso(agente=kw["agente"], modelo="simulado", tokens_entrada=1, tokens_salida=1, latencia_s=0)

    monkeypatch.setattr(claude, "estructurado", falso)


def test_mensaje_al_modelo_lleva_catalogo_perfil_y_turnos(monkeypatch):
    llamadas: list = []
    simular_claude(monkeypatch, RESPUESTA_CARMEN, llamadas)
    asyncio.run(extractor.extraer(TURNOS, vacio(), "s-1"))
    kw = llamadas[0]
    assert kw["agente"] == "extractor" and kw["esquema"] is Extraccion
    # Lo estable (instrucciones y catálogo) va en el sistema, que se cachea; lo variable, en el mensaje.
    assert "Eres el extractor" in kw["sistema"] and "financial.liquid_savings_eur" in kw["sistema"]
    assert "financial.emergency_fund_months" not in kw["sistema"]
    assert '"turn_id": "t-012"' in kw["mensaje"] and '"turn_id": "t-002"' not in kw["mensaje"]  # ventana de 8


def test_entrevista_de_carmen_por_la_api_da_el_perfil_y_la_alerta_clave(monkeypatch):
    """Criterio de «terminado» de B1: la entrevista de Carmen da su perfil con la alerta clave."""
    simular_claude(monkeypatch, RESPUESTA_CARMEN)
    store.reiniciar()
    api = cliente_autorizado("carmen-nueva")
    sid = api.post("/api/sessions", json={"client_id": "carmen-nueva"}).json()["session_id"]
    for t in TURNOS:  # como en producción: se procesa cada turno al llegar (ventana de 6 turnos)
        store.anadir_turno(sid, t)
        asyncio.run(main._procesar_turno(sid))

    p = store.perfil("carmen-nueva")
    assert p.mifid["knowledge.equity_funds"].value == "none"
    assert Flag.declared_vs_demonstrated in p.mifid["knowledge.equity_funds"].flags
    assert p.mifid["financial.emergency_fund_months"].source == Fuente.calculated  # lo calcula el sistema
    assert any(a.flag == Flag.declared_vs_demonstrated and a.path == "knowledge.equity_funds" for a in p.alerts)
    assert api.get(f"/api/sessions/{sid}").json()["rejections"] == []


# ---------- rúbrica y configuración ----------

def test_rubrica_de_conocimiento():
    r = "knowledge.equity_funds"
    assert rubrica.conocimiento(r, "high", "incorrecta")[:3] == ("none", "demonstrated", 0.85)
    assert rubrica.conocimiento(r, None, "parcial")[:3] == ("basic", "demonstrated", 0.7)
    assert rubrica.conocimiento(r, "basic", "correcta")[:3] == ("basic", "demonstrated", 0.8)
    assert rubrica.conocimiento(r, "none", "correcta")[:3] == ("basic", "demonstrated", 0.8)
    assert rubrica.conocimiento(r, None, "correcta")[:3] == ("medium", "demonstrated", 0.85)
    assert rubrica.conocimiento(r, "medium", "correcta")[:3] == ("medium", "demonstrated", 0.85)
    assert rubrica.conocimiento(r, "high", "correcta")[:3] == ("high", "demonstrated", 0.75)
    valor, fuente, conf, _ = rubrica.conocimiento(r, "medium", None)
    assert (valor, fuente) == ("medium", "declared") and rubrica.baja(conf)


def test_modelo_y_esfuerzo_por_variable(monkeypatch):
    monkeypatch.delenv("MODEL_EXTRACTOR", raising=False)
    assert claude.modelo("extractor") == claude.MODELO_POR_DEFECTO
    monkeypatch.setenv("MODEL_EXTRACTOR", "claude-opus-5-5")
    assert claude.modelo("extractor") == "claude-opus-5-5"
    monkeypatch.setenv("EFFORT_EXTRACTOR", "nada")
    assert claude.esfuerzo("extractor", "low") == "low"
    monkeypatch.setenv("EFFORT_EXTRACTOR", "HIGH")
    assert claude.esfuerzo("extractor", "low") == "high"


def test_sin_clave_el_cliente_avisa(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(claude.ClaudeNoDisponible):
        asyncio.run(claude.estructurado(agente="x", sistema="s", mensaje="m", esquema=Extraccion))


def test_el_perfil_actual_marca_la_confianza_baja():
    from app.agentes import extractor as ex
    from app.perfil.modelos import Fact, Flag, Fuente, Perfil

    perfil = Perfil(client_id="x", mifid={
        "financial.debts_eur": Fact(value=0, source=Fuente.declared, confidence=0.55, flags=[Flag.low_confidence],
                                    updated_by="agent:extractor"),
        "financial.liquid_savings_eur": Fact(value=80000, source=Fuente.declared, confidence=0.9, updated_by="agent:extractor"),
    })
    estado = ex._estado(perfil)
    assert "- financial.debts_eur = 0 (declared, confianza baja)" in estado
    assert "- financial.liquid_savings_eur = 80000 (declared)" in estado


def test_un_fallo_en_la_comprobacion_no_se_borra_tras_la_explicacion():
    from app.agentes import extractor as ex
    from app.perfil.modelos import Evidencia, Fact, Fuente, Parche

    ev = lambda sid, tid: [Evidencia(session_id=sid, turn_id=tid, t=[0, 1], quote="x")]  # noqa: E731
    fallo = Fact(value="none", source=Fuente.demonstrated, confidence=0.85, evidence=ev("s-1", "t-022"),
                 updated_by="agent:extractor")
    tras_explicar = Parche(path="knowledge.equity_funds", value="basic", source=Fuente.demonstrated, confidence=0.7,
                           confidence_basis="b", evidence=ev("s-1", "t-024"), updated_by="agent:extractor")
    assert ex._protegido(fallo, tras_explicar)
    otra_entrevista = tras_explicar.model_copy(update={"evidence": ev("s-2", "t-010")})
    assert not ex._protegido(fallo, otra_entrevista)
