"""Laboratorio de entrevistas: personas bien formadas y bucle de entrevista (sin llamar a Claude)."""

import asyncio

import pytest

from app.agentes import chat, cliente_simulado, evaluacion, laboratorio
from app.perfil import store

PERSONAS = laboratorio.personas()


def test_hay_personas():
    assert len(PERSONAS) >= 3


@pytest.mark.parametrize("persona", PERSONAS, ids=lambda p: p.caso.nombre)
def test_cada_persona_esta_bien_formada(persona):
    assert persona.ficha.strip()
    assert evaluacion.comprobar_caso(persona.caso, con_turnos=False) == []


def test_la_ficha_va_al_sistema_del_cliente_simulado_y_no_al_entrevistador():
    ficha = PERSONAS[0].ficha
    assert ficha.strip() in cliente_simulado.sistema(ficha)
    assert "ficha" not in chat._sistema().casefold()


async def _entrevista(monkeypatch, guion_asistente, max_turnos=10):
    store.reiniciar()
    respuestas = iter(guion_asistente)

    async def asistente(turnos, perfil):
        texto, fin = next(respuestas)
        return chat.Respuesta(texto=texto, terminada=fin)

    async def cliente(ficha, turnos):
        return "Pues unos mil cuatrocientos."

    procesados = []

    async def procesar(sid):
        procesados.append(sid)

    monkeypatch.setattr(chat, "responder", asistente)
    monkeypatch.setattr(cliente_simulado, "responder", cliente)
    informe = await laboratorio.entrevistar(
        PERSONAS[0],
        sesion_nueva=lambda: store.crear_sesion("laboratorio", "text")["session_id"],
        anadir_turno=store.anadir_turno, procesar_turno=procesar,
        perfil=lambda: store.perfil("laboratorio"), max_turnos=max_turnos,
    )
    return informe, procesados


def test_entrevista_hasta_el_cierre_y_mide_el_comportamiento(monkeypatch):
    informe, procesados = asyncio.run(_entrevista(monkeypatch, [
        ("Hola, soy una inteligencia artificial del banco. ¿Le parece bien que grabemos?", False),
        ("¿Cuánto cobra al mes? ¿Y cuánto gasta?", False),
        ("Con esos ahorros le recomiendo un fondo.", False),
        ("Gracias, una persona del banco revisará su perfil.", True),
    ]))
    assert informe.terminada and informe.aviso_ia_al_inicio
    assert informe.intervenciones == 4 and len(procesados) == 3
    assert informe.preguntas_dobles == 1
    assert informe.recomendaciones == 1
    assert [t.speaker for t in informe.turnos] == ["agent", "client"] * 3 + ["agent"]
    assert informe.alertas_esperadas == {"knowledge.equity_funds": False}
    assert "financial.net_monthly_income_eur" in informe.pendientes


def test_una_entrevista_que_no_cierra_se_corta(monkeypatch):
    informe, _ = asyncio.run(_entrevista(monkeypatch, [("¿Y qué más?", False)] * 5, max_turnos=3))
    assert not informe.terminada and not informe.aviso_ia_al_inicio
    assert informe.intervenciones == 3
