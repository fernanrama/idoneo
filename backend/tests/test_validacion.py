"""Validación estricta de entrada (app/perfil/validacion.py). Sin almacén."""

from __future__ import annotations

import pytest

from app.perfil import validacion as V
from app.perfil.modelos import CALCULADOS, CAMPOS, Alerta, Evidencia, Flag, Fuente, Parche

EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="lo que dijo")]


def test_los_tipos_cubren_exactamente_el_esquema_de_la_pr7():
    assert set(V.TIPOS) == set(CAMPOS)
    assert {r for r, (t, _) in V.TIPOS.items() if t == "calculado"} == CALCULADOS


@pytest.mark.parametrize("ruta,entrada,esperado", [
    ("financial.debts_eur", "1500", 1500.0),
    ("financial.debts_eur", 99.999, 100.0),
    ("risk_tolerance.scenario_score", 3.0, 3),
    ("knowledge.etfs", "basic", "basic"),
    ("experience.profession", "  enfermera ", "enfermera"),
    ("sustainability.min_sfdr_article", 9, 9),
    ("disclosures.ai_notice_ack", None, None),
])
def test_valores_validos(ruta, entrada, esperado):
    assert V.normalizar(ruta, entrada) == esperado


@pytest.mark.parametrize("ruta,entrada", [
    ("financial.debts_eur", -1), ("financial.debts_eur", True), ("financial.debts_eur", "muchísimo"),
    ("risk_tolerance.scenario_score", 6), ("risk_tolerance.scenario_score", 2.5),
    ("knowledge.etfs", "experto"), ("disclosures.ai_notice_ack", "sí"),
    ("sustainability.min_sfdr_article", 7), ("objectives.o1.horizon_years", 150),
    ("experience.profession", "   "), ("experience.profession", "x" * 1001),
    ("salud.diagnostico", "x"), ("objectives.o2.goal", "x"),
])
def test_valores_y_rutas_invalidos(ruta, entrada):
    with pytest.raises(V.DatoInvalido):
        V.normalizar(ruta, entrada)


def test_nadie_escribe_calculados():
    for p in (Parche(path="financial.loss_capacity_eur", value=1, source="advisor"),
              Parche(path="financial.debts_eur", value=1, source="calculated", evidence=EV)):
        with pytest.raises(V.EscrituraCalculada):
            V.comprobar_parche(p, "advisor:a")


def test_autoria():
    with pytest.raises(V.DatoInvalido):  # un agente no se hace pasar por la entidad
        V.comprobar_parche(Parche(path="financial.debts_eur", value=1, source="advisor", evidence=EV), "agent:extractor")
    with pytest.raises(V.DatoInvalido):  # dato de la conversación sin evidencia
        V.comprobar_parche(Parche(path="financial.debts_eur", value=1, source="declared"), "agent:extractor")
    p = V.comprobar_parche(Parche(path="financial.debts_eur", value=1, source="declared"), "advisor:asesor-07")
    assert p.source == Fuente.advisor  # la entidad no necesita cita, pero queda como corrección
    for autor in ("", "extractor", "advisor:", "agent:Extractor!", "root"):
        with pytest.raises(V.DatoInvalido):
            V.comprobar_autor(autor)


def test_marcas_automaticas():
    p = V.comprobar_parche(Parche(path="knowledge.etfs", value="none", declared="high", source="demonstrated",
                                  evidence=EV), "agent:extractor")
    assert p.flags == [Flag.declared_vs_demonstrated]
    p = V.comprobar_parche(Parche(path="knowledge.etfs", value="basic", declared="basic", source="demonstrated",
                                  evidence=EV, flags=[Flag.declared_vs_demonstrated]), "agent:extractor")
    assert p.declared is None and p.flags == []  # igual a lo demostrado: ni se guarda ni se marca
    p = V.comprobar_parche(Parche(path="knowledge.etfs", value="basic", source="declared", evidence=EV,
                                  flags=[Flag.low_confidence]), "agent:extractor")
    assert p.flags == [Flag.low_confidence]  # la confianza baja la marca el extractor (contrato PR #7)


@pytest.mark.parametrize("cid", ["carmen-68", "cliente-1a2b3c", "a"])
def test_client_id_valido(cid):
    assert V.comprobar_client_id(cid) == cid


@pytest.mark.parametrize("cid", ["", "../x", "Carmen", "a b", "x" * 65, "a/b", "-a"])
def test_client_id_invalido(cid):
    with pytest.raises(V.DatoInvalido):
        V.comprobar_client_id(cid)


def test_alertas():
    V.comprobar_alerta(Alerta(id="a", path="knowledge.etfs", flag=Flag.inconsistent, message="m"))
    V.comprobar_alerta(Alerta(id="a", path=None, flag=Flag.needs_advisor, message="m"))
    with pytest.raises(V.DatoInvalido):
        V.comprobar_alerta(Alerta(id="a", path="no.existe", flag=Flag.inconsistent, message="m"))
    with pytest.raises(V.DatoInvalido):
        V.comprobar_alerta(Alerta(id="a", path=None, flag=Flag.inconsistent, message="  "))
