"""Máquina de estados del perfil (contrato 04).

draft ──completo y sin bloqueos──▶ pending_validation ──asesor valida──▶ active
  ▲                                     │                                  │
  └──────── falta algo / repreguntar ───┘                                  │
  ▲                                                                        ▼
  └────────────── empieza una entrevista corta ◀──────────────────── review_due
                                                  (cambio no hecho por el asesor,
                                                   evento vital o revisión periódica)
"""

from __future__ import annotations

from .errores import TransicionNoPermitida
from .modelos import EstadoPerfil as E
from .modelos import Flag, Perfil

TRANSICIONES: dict[E, frozenset[E]] = {
    E.draft: frozenset({E.pending_validation}),
    E.pending_validation: frozenset({E.active, E.draft}),
    E.active: frozenset({E.review_due}),
    E.review_due: frozenset({E.draft}),
}


def comprobar(de: E, a: E) -> None:
    if de != a and a not in TRANSICIONES[de]:
        raise TransicionNoPermitida(f"No se puede pasar de '{de.value}' a '{a.value}'")


def tiene_bloqueos(perfil: Perfil) -> bool:
    """Una alerta abierta de revisión humana impide pasar a validación."""
    return any(a.type == Flag.needs_advisor.value for a in perfil.alertas_abiertas())


def tras_cambio(perfil: Perfil, por_asesor: bool) -> E:
    """Estado tras escribir datos o alertas. `perfil` ya tiene sus evaluaciones recalculadas."""
    actual = perfil.status
    if actual == E.active:
        return E.active if por_asesor else E.review_due
    if actual == E.review_due:
        return E.review_due
    listo = perfil.assessments.suitability.complete and not tiene_bloqueos(perfil)
    return E.pending_validation if listo else E.draft
