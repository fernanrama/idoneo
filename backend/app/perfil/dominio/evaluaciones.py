"""Resultados de los dos tests MiFID, calculados de forma determinista a partir del perfil.

- Idoneidad (asesoramiento y gestión de carteras): perfil de riesgo = el tope más restrictivo
  entre tolerancia por escenarios, caída aceptada, plazo y capacidad de pérdida.
- Conveniencia (compra sin asesoramiento): por familia de producto, según el conocimiento
  demostrado y la experiencia.

El verificador no calcula estos resultados: solo marca alertas. Tablas en supuestos.py.
"""

from __future__ import annotations

from . import supuestos as S
from .esquema import FAMILIAS, id_objetivo
from .modelos import (
    ORDEN_NIVEL,
    ORDEN_PERFIL,
    Conveniencia,
    Evaluaciones,
    Flag,
    Idoneidad,
    Perfil,
    PerfilRiesgo,
)


def _eur(cantidad: float) -> str:
    """74600 -> '74.600' (separador de miles español)."""
    return f"{cantidad:,.0f}".replace(",", ".")


def _por_tramos(valor: float, tramos: tuple[tuple[float, PerfilRiesgo], ...]) -> PerfilRiesgo:
    for limite, perfil in tramos:
        if valor < limite:
            return perfil
    return PerfilRiesgo.MUY_AGRESIVO


def tope_por_caida_aceptada(pct: float) -> PerfilRiesgo:
    return _por_tramos(pct, S.TRAMOS_CAIDA_ACEPTADA_PCT)


def tope_por_plazo(anios: float) -> PerfilRiesgo:
    return _por_tramos(anios, S.TRAMOS_PLAZO_ANIOS)


def tope_por_capacidad(capacidad: float, importe: float) -> PerfilRiesgo | None:
    if importe <= 0:
        return None
    return _por_tramos(capacidad / importe, S.TRAMOS_CAPACIDAD_RATIO)


def objetivo_principal(perfil: Perfil) -> str | None:
    """Id del objetivo con prioridad más alta (número más bajo); a igualdad, el de id menor."""
    ids = sorted({o for r in perfil.mifid if (o := id_objetivo(r))})
    if not ids:
        return None
    def orden(o: str) -> tuple[float, str]:
        prioridad = perfil.valor(f"objectives.{o}.priority")
        return (float("inf") if prioridad is None else prioridad, o)

    return min(ids, key=orden)


def _sin_confianza(perfil: Perfil, ruta: str) -> bool:
    dato = perfil.mifid.get(ruta)
    return dato is not None and Flag.low_confidence in dato.flags


def idoneidad(perfil: Perfil) -> Idoneidad:
    v = perfil.valor
    faltan = [r for r in S.CAMPOS_OBLIGATORIOS if v(r) is None or _sin_confianza(perfil, r)]

    topes: list[tuple[PerfilRiesgo, str, str]] = []  # (perfil, ruta que lo justifica, explicación)
    if (e := v("risk_tolerance.scenario_score")) is not None:
        topes.append((S.TOPE_POR_ESCENARIO[e], "risk_tolerance.scenario_score", f"reacción en escenarios {e}/5"))
    if (c := v("risk_tolerance.max_drawdown_accepted_pct")) is not None:
        topes.append((tope_por_caida_aceptada(c), "risk_tolerance.max_drawdown_accepted_pct",
                      f"acepta caídas de hasta un {c:g} %"))
    obj = objetivo_principal(perfil)
    if obj and (h := v(f"objectives.{obj}.horizon_years")) is not None:
        topes.append((tope_por_plazo(h), f"objectives.{obj}.horizon_years", f"plazo de {h:g} años"))
    capacidad = v("financial.loss_capacity_eur")
    importe = v(f"objectives.{obj}.amount_eur") if obj else None
    if capacidad is not None and importe:
        t = tope_por_capacidad(capacidad, importe)
        if t is not None:
            topes.append((t, "financial.loss_capacity_eur",
                          f"puede perder {_eur(capacidad)} € frente a {_eur(importe)} € a invertir"))

    motivos = [f"{expl} → como máximo {p.value}" for p, _, expl in topes]
    if not topes:
        return Idoneidad(complete=False, missing=faltan, rationale=["Sin datos para el perfil de riesgo"])

    perfil_riesgo = min((p for p, _, _ in topes), key=ORDEN_PERFIL.index)
    decisivos = [ruta for p, ruta, _ in topes if p == perfil_riesgo]
    marcados = [r for r, d in perfil.mifid.items() if d.flags]
    motivos.append(f"Manda el más restrictivo: {perfil_riesgo.value}")
    return Idoneidad(
        complete=not faltan,
        missing=faltan,
        risk_profile=perfil_riesgo,
        max_sri=S.SRI_MAX_POR_PERFIL[perfil_riesgo],
        portfolio_risk_max=S.RISK_MAX_CARTERAS_POR_PERFIL[perfil_riesgo],
        rationale=motivos,
        rationale_ids=list(dict.fromkeys(decisivos + marcados)),
    )


def conveniencia_familia(perfil: Perfil, familia: str) -> Conveniencia:
    ruta = f"knowledge.{familia}"
    nivel = perfil.valor(ruta)
    if nivel is None or _sin_confianza(perfil, ruta):
        return Conveniencia.unknown
    minimo = ORDEN_NIVEL[S.NIVEL_MINIMO_POR_FAMILIA[familia]]
    if ORDEN_NIVEL[nivel] >= minimo:
        return Conveniencia.appropriate
    operaciones = perfil.valor(f"experience.by_family.{familia}.operations_last_3y") or 0
    if ORDEN_NIVEL[nivel] == minimo - 1 and operaciones >= S.OPERACIONES_COMPENSAN_UN_NIVEL:
        return Conveniencia.appropriate
    return Conveniencia.not_appropriate


def evaluar(perfil: Perfil) -> Evaluaciones:
    return Evaluaciones(
        suitability=idoneidad(perfil),
        appropriateness={f: conveniencia_familia(perfil, f) for f in FAMILIAS},
    )
