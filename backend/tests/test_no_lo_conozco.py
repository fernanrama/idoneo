"""Defecto «No lo conozco» (diagnóstico, 10/11/2026). Sin Claude: la salida del modelo se simula.

Un cliente que dice con sinceridad que no conoce una familia obligatoria («No lo conozco») queda con
`knowledge.<familia> = none`, fuente `declared` y confianza 0,5 (rubrica.CONFIANZA_SOLO_DECLARADO), es decir,
con `low_confidence`. Hay dos criterios de «completo» que no coinciden:

- El entrevistador (`chat._pendientes_por_tipo`) excluye a propósito ese caso: «No sé qué es un ETF» no se
  comprueba. Da el dato por cerrado y no vuelve a preguntar.
- El perfil (`calculos.faltan`) cuenta todo obligatorio con `low_confidence` como no rellenado. Así
  `suitability.complete` nunca llega a true, el perfil se queda en `draft` y validar responde 409.

Las pruebas marcadas `xfail(strict=True)` describen el comportamiento esperado y hoy fallan: reproducen el
defecto. Cuando se corrija, pytest avisará (XPASS estricto) para quitar la marca. Las demás fijan lo que
la corrección no debe romper: no inventar conocimiento y seguir marcando el producto como no conveniente.
"""
from __future__ import annotations

import pytest

from app.agentes import chat, extractor, rubrica
from app.agentes.extractor import ConocimientoExtraido, Extraccion
from app.perfil import calculos, store
from app.perfil.modelos import Conveniencia, EstadoPerfil, Flag, Fuente, Turno

CID = "cliente-no-lo-conozco"
FAMILIA = "fixed_income_funds"
RUTA = f"knowledge.{FAMILIA}"

TURNOS = [
    Turno(turn_id="t-101", speaker="agent", t_start=0.0, t_end=4.0,
          text="¿Cómo de bien diría que conoce los fondos de renta fija: nada, algo o bien?"),
    Turno(turn_id="t-102", speaker="client", t_start=4.0, t_end=7.0,
          text="No lo conozco, nunca he oído hablar de eso."),
]
# Lo que devolvería el modelo según prompts/extractor.md: «nunca ha oído hablar» → none, sin comprobación.
RESPUESTA = Extraccion(datos=[], conocimientos=[
    ConocimientoExtraido(familia=FAMILIA, nivel_declarado="none", resultado_comprobacion=None,
                         turn_id="t-102", cita="No lo conozco, nunca he oído hablar de eso."),
], escenario=None)


def _perfil_con_no_lo_conozco():
    """Perfil completo de Carmen (fixture simulado) salvo la renta fija, que llega por el extractor."""
    _, parches, _ = store._leer_fixture("carmen-68")
    store.crear_nuevo(CID)
    store.aplicar(CID, [p for p in parches if p.path != RUTA], "datos simulados de prueba", store.AUTOR_FIXTURE)
    nuevos = extractor.a_parches(RESPUESTA, TURNOS, store.perfil(CID), "s-prueba")
    return nuevos, store.aplicar(CID, nuevos, "respuesta «No lo conozco»", "agent:extractor")


def test_reproduce_el_dato_queda_declarado_none_con_confianza_baja():
    nuevos, p = _perfil_con_no_lo_conozco()
    (parche,) = [x for x in nuevos if x.path == RUTA]
    assert (parche.value, parche.source, parche.confidence) == ("none", Fuente.declared, rubrica.CONFIANZA_SOLO_DECLARADO)
    assert Flag.low_confidence in p.mifid[RUTA].flags
    assert parche.evidence[0].quote == "No lo conozco, nunca he oído hablar de eso."


def test_reproduce_criterios_de_completo_contradictorios():
    _, p = _perfil_con_no_lo_conozco()
    # El entrevistador lo da por cerrado: no lo pedirá otra vez…
    assert RUTA not in chat.pendientes(p)
    # …pero el perfil lo sigue contando como faltante.
    assert RUTA in calculos.faltan(p)
    assert p.assessments.suitability.complete is False
    assert p.status == EstadoPerfil.draft


def test_invariante_no_se_inventa_conocimiento_y_sigue_no_conveniente():
    _, p = _perfil_con_no_lo_conozco()
    assert p.mifid[RUTA].value == "none"
    assert p.assessments.appropriateness[FAMILIA] == Conveniencia.not_appropriate
    assert calculos.restricciones(p).appropriateness[FAMILIA] == Conveniencia.not_appropriate


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="Defecto «No lo conozco»: el desconocimiento declarado no completa el perfil")
def test_esperado_el_desconocimiento_declarado_completa_el_perfil():
    _, p = _perfil_con_no_lo_conozco()
    assert RUTA not in calculos.faltan(p)
    assert p.assessments.suitability.complete is True
    assert p.status == EstadoPerfil.pending_validation


@pytest.mark.xfail(strict=True, raises=store.Conflicto,
                   reason="Defecto «No lo conozco»: validar responde 409 (faltan datos obligatorios)")
def test_esperado_el_asesor_puede_validar_y_sigue_no_conveniente():
    _, p = _perfil_con_no_lo_conozco()
    activo = store.validar(CID, "asesor-prueba")
    assert activo.status == EstadoPerfil.active
    assert activo.assessments.appropriateness[FAMILIA] == Conveniencia.not_appropriate
