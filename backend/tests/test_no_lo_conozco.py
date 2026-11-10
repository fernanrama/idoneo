"""Defecto «No lo conozco» (11/11/2026). Sin Claude: la salida del modelo se simula.

Antes (rúbrica v2): un «No lo conozco» sincero sobre una familia obligatoria quedaba `none`, `declared`,
confianza 0,5 y `low_confidence`. El entrevistador (`chat._pendientes_por_tipo`) lo daba por cerrado, pero
`calculos.faltan` lo contaba como no rellenado: el perfil se quedaba en `draft` y validar respondía 409.

Ahora (rúbrica v3): el desconocimiento declarado de forma explícita es un dato suficiente (0,8) y la regla
`calculos.desconocimiento_declarado` es común al perfil y al entrevistador. Lo que NO cambia y se fija aquí:
no se inventa conocimiento (`none`), la familia sigue `not_appropriate` y los niveles declarados basic,
medium o high siguen necesitando comprobación.
"""
from __future__ import annotations

from app.agentes import chat, extractor, rubrica
from app.agentes.extractor import ConocimientoExtraido, Extraccion
from app.perfil import calculos, store
from app.perfil.modelos import Conveniencia, EstadoPerfil, Flag, Fuente, Parche, Turno

CID = "cliente-no-lo-conozco"
FAMILIA = "fixed_income_funds"
RUTA = f"knowledge.{FAMILIA}"

TURNOS = [
    Turno(turn_id="t-101", speaker="agent", t_start=0.0, t_end=4.0,
          text="¿Cómo de bien diría que conoce los fondos de renta fija: nada, algo o bien?"),
    Turno(turn_id="t-102", speaker="client", t_start=4.0, t_end=7.0,
          text="No lo conozco, nunca he oído hablar de eso."),
]


def _respuesta(nivel: str, cita: str = "No lo conozco, nunca he oído hablar de eso.") -> Extraccion:
    """Lo que devolvería el modelo según prompts/extractor.md: nivel declarado, sin comprobación."""
    return Extraccion(datos=[], conocimientos=[
        ConocimientoExtraido(familia=FAMILIA, nivel_declarado=nivel, resultado_comprobacion=None,
                             turn_id="t-102", cita=cita),
    ], escenario=None)


def _perfil_base():
    """Perfil completo de Carmen (fixture simulado) salvo la renta fija."""
    _, parches, _ = store._leer_fixture("carmen-68")
    store.crear_nuevo(CID)
    store.aplicar(CID, [p for p in parches if p.path != RUTA], "datos simulados de prueba", store.AUTOR_FIXTURE)


def _perfil_con(nivel: str):
    _perfil_base()
    nuevos = extractor.a_parches(_respuesta(nivel), TURNOS, store.perfil(CID), "s-prueba")
    return nuevos, store.aplicar(CID, nuevos, f"declara {nivel}", "agent:extractor")


def test_no_lo_conozco_queda_none_declarado_con_evidencia_y_confianza_suficiente():
    nuevos, p = _perfil_con("none")
    (parche,) = [x for x in nuevos if x.path == RUTA]
    assert (parche.value, parche.source) == ("none", Fuente.declared)
    assert parche.confidence == rubrica.CONFIANZA_DESCONOCIMIENTO_DECLARADO >= rubrica.UMBRAL
    assert parche.confidence_basis == f"rubric:{RUTA}:v3"
    assert Flag.low_confidence not in p.mifid[RUTA].flags
    assert parche.evidence[0].quote == "No lo conozco, nunca he oído hablar de eso."


def test_entrevistador_y_perfil_coinciden_el_perfil_se_completa():
    _, p = _perfil_con("none")
    assert RUTA not in chat.pendientes(p)
    assert RUTA not in calculos.faltan(p)
    assert p.assessments.suitability.complete is True
    assert p.status == EstadoPerfil.pending_validation


def test_el_asesor_puede_validar_y_sigue_no_conveniente():
    _perfil_con("none")
    activo = store.validar(CID, "asesor-prueba")
    assert activo.status == EstadoPerfil.active
    assert activo.mifid[RUTA].value == "none"
    assert activo.assessments.appropriateness[FAMILIA] == Conveniencia.not_appropriate
    assert calculos.restricciones(activo).appropriateness[FAMILIA] == Conveniencia.not_appropriate


def test_un_nivel_declarado_sin_comprobar_sigue_exigiendo_comprobacion():
    """«Lo conozco algo» no es «No lo conozco»: sin pregunta de comprobación no basta."""
    _, p = _perfil_con("basic")
    assert p.mifid[RUTA].confidence == rubrica.CONFIANZA_SOLO_DECLARADO
    assert Flag.low_confidence in p.mifid[RUTA].flags
    assert RUTA in calculos.faltan(p)
    assert RUTA in chat.pendientes(p)
    assert p.status == EstadoPerfil.draft


def test_perfil_antiguo_con_rubrica_v2_ya_no_se_queda_bloqueado():
    """Un dato guardado con la v2 (0,5 y low_confidence) también cuenta como cerrado."""
    _perfil_base()
    turno = TURNOS[1]
    antiguo = Parche(path=RUTA, value="none", source=Fuente.declared, confidence=0.5,
                     confidence_basis=f"rubric:{RUTA}:v2", flags=[Flag.low_confidence],
                     evidence=[{"session_id": "s-antigua", "turn_id": turno.turn_id, "quote": turno.text,
                                "t": [turno.t_start, turno.t_end]}])
    p = store.aplicar(CID, [antiguo], "dato de la rúbrica v2", "agent:extractor")
    assert Flag.low_confidence in p.mifid[RUTA].flags
    assert RUTA not in calculos.faltan(p)
    assert p.status == EstadoPerfil.pending_validation
    assert p.assessments.appropriateness[FAMILIA] == Conveniencia.not_appropriate
