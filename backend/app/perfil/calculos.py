"""Cálculos deterministas del perfil (contrato v1). El modelo nunca pone estos números.

Todas las tablas son SUPUESTOS v1 del equipo, no fórmulas regulatorias. Revisarlas antes del pitch
y decirlo así ante el jurado. Las decisiones abiertas del contrato están marcadas con [ABIERTO].
"""

from __future__ import annotations

from .modelos import (
    CALCULADOS,
    FAMILIAS,
    NIVELES,
    OBLIGATORIOS,
    Conveniencia,
    EstadoPerfil,
    Fact,
    FiltroPosterior,
    Flag,
    Fuente,
    Idoneidad,
    Perfil,
    PerfilRiesgo,
    Restricciones,
    Resultados,
)

MESES_COLCHON_OBJETIVO = 6
ORDEN_PERFILES = list(PerfilRiesgo)  # de más a menos conservador

# [ABIERTO] Perfil de riesgo → SRI máximo de fondos (SRRI 1–7 en search_funds.max_risk).
MAX_SRI = {
    PerfilRiesgo.CONSERVADOR: 3,
    PerfilRiesgo.MODERADO: 4,
    PerfilRiesgo.DINAMICO: 5,
    PerfilRiesgo.AGRESIVO: 6,
    PerfilRiesgo.MUY_AGRESIVO: 7,
}
# [ABIERTO] Perfil → risk_max de carteras (escala propia 0–5). Verificar con list_facets en MyInvestor.
RISK_MAX_CARTERAS = {
    PerfilRiesgo.CONSERVADOR: 1,
    PerfilRiesgo.MODERADO: 2,
    PerfilRiesgo.DINAMICO: 3,
    PerfilRiesgo.AGRESIVO: 4,
    PerfilRiesgo.MUY_AGRESIVO: 5,
}
# Familia de producto → asset_type de search_funds (solo fondos).
ASSET_TYPE = {
    "deposits_money_market": "Monetario",
    "fixed_income_funds": "Renta Fija",
    "mixed_funds": "Mixto",
    "equity_funds": "Renta Variable",
}
# [ABIERTO] Operaciones en 3 años que compensan un conocimiento bajo, para la conveniencia.
OPERACIONES_EXPERIENCIA = 5
# [ABIERTO] SRI mínimo del perfil para buscar acciones sueltas: una acción suele estar en SRI 6–7.
SRI_MIN_ACCIONES = 6
# Plazo de reembolso máximo según la necesidad de liquidez.
REEMBOLSO_MAX_DIAS = {"high": 3, "medium": 7}


# ---------- utilidades ----------

def valor(perfil: Perfil, ruta: str):
    f = perfil.mifid.get(ruta)
    return None if f is None else f.value


def _indice(p: PerfilRiesgo) -> int:
    return ORDEN_PERFILES.index(p)


# ---------- campos calculados ----------

def meses_colchon(ahorro_liquido: float, gastos_fijos: float) -> float:
    """Meses de gastos fijos que cubre el ahorro líquido."""
    return round(ahorro_liquido / gastos_fijos, 1) if gastos_fijos > 0 else 0.0


def capacidad_perdida(ahorro_liquido: float, gastos_fijos: float, deudas: float) -> float:
    """Lo que podría perder sin tocar un colchón de 6 meses de gastos ni dejar deudas sin cubrir.

    `deudas` no incluye la hipoteca de la vivienda (`financial.mortgage_eur`): es deuda a largo plazo
    respaldada por la casa y su cuota ya va en los gastos fijos. Restar su capital del ahorro dejaba a
    cualquiera con hipoteca en CONSERVADOR aunque le sobrara colchón. SUPUESTO v1."""
    return round(max(0.0, ahorro_liquido - MESES_COLCHON_OBJETIVO * gastos_fijos - deudas), 2)


def recalcular(perfil: Perfil) -> None:
    """Rellena campos calculados y resultados. Se llama tras cada escritura."""
    # Los derivados heredados no justifican la versión actual: reconstruirlos
    # solo si siguen presentes todas sus entradas, antes de evaluar idoneidad.
    for ruta in CALCULADOS:
        perfil.mifid.pop(ruta, None)
    ahorro = valor(perfil, "financial.liquid_savings_eur")
    gastos = valor(perfil, "financial.fixed_monthly_costs_eur")
    deudas = valor(perfil, "financial.debts_eur")
    if ahorro is not None and gastos is not None:
        perfil.mifid["financial.emergency_fund_months"] = Fact(
            value=meses_colchon(float(ahorro), float(gastos)), source=Fuente.calculated,
            updated_by="fn:meses_colchon",
            inputs=["financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur"],
        )
        if deudas is not None:
            perfil.mifid["financial.loss_capacity_eur"] = Fact(
                value=capacidad_perdida(float(ahorro), float(gastos), float(deudas)),
                source=Fuente.calculated, updated_by="fn:capacidad_perdida",
                inputs=["financial.liquid_savings_eur", "financial.fixed_monthly_costs_eur", "financial.debts_eur"],
            )
    perfil.assessments = Resultados(suitability=idoneidad(perfil), appropriateness=conveniencia(perfil))
    perfil.review.open_flags = sum(1 for a in perfil.alerts if a.status == "open")


# ---------- idoneidad ----------

def _por_tolerancia(score: int) -> PerfilRiesgo:
    # Rúbrica de escenarios 1–5 → perfil
    return ORDEN_PERFILES[max(1, min(5, int(score))) - 1]


def _por_plazo(anios: float) -> PerfilRiesgo:
    if anios < 2:
        return PerfilRiesgo.CONSERVADOR
    if anios < 5:
        return PerfilRiesgo.MODERADO
    if anios < 8:
        return PerfilRiesgo.DINAMICO
    if anios < 12:
        return PerfilRiesgo.AGRESIVO
    return PerfilRiesgo.MUY_AGRESIVO


def _por_capacidad(capacidad: float, ahorro: float) -> PerfilRiesgo:
    # Fracción del ahorro que podría perder sin comprometer el colchón
    if ahorro <= 0 or capacidad <= 0:
        return PerfilRiesgo.CONSERVADOR
    r = capacidad / ahorro
    if r < 0.25:
        return PerfilRiesgo.MODERADO
    if r < 0.5:
        return PerfilRiesgo.DINAMICO
    if r < 0.75:
        return PerfilRiesgo.AGRESIVO
    return PerfilRiesgo.MUY_AGRESIVO


def desconocimiento_declarado(ruta: str, f: Fact | None) -> bool:
    """«No lo conozco»: conocimiento declarado `none`. Es un dato cerrado: no hay nada que comprobar.

    Regla común del perfil (`faltan`) y del entrevistador (`agentes.chat`), para que no diverjan. Cubre
    también perfiles antiguos donde la rúbrica v2 lo dejó con low_confidence."""
    return (f is not None and ruta.startswith("knowledge.")
            and f.source == Fuente.declared and f.value == "none")


def faltan(perfil: Perfil) -> list[str]:
    out = []
    for ruta in OBLIGATORIOS:
        f = perfil.mifid.get(ruta)
        dudoso = f is not None and Flag.low_confidence in f.flags and not desconocimiento_declarado(ruta, f)
        if f is None or f.value is None or dudoso:
            out.append(ruta)
    return out


def idoneidad(perfil: Perfil) -> Idoneidad:
    """Manda el más restrictivo de tolerancia, capacidad de pérdida y plazo."""
    candidatos: list[tuple[PerfilRiesgo, str, str]] = []
    score = valor(perfil, "risk_tolerance.scenario_score")
    if score is not None:
        p = _por_tolerancia(score)
        candidatos.append((p, "risk_tolerance.scenario_score", f"Tolerancia por escenarios ({score}/5) → {p.value}"))
    cap, ahorro = valor(perfil, "financial.loss_capacity_eur"), valor(perfil, "financial.liquid_savings_eur")
    if cap is not None and ahorro is not None:
        p = _por_capacidad(float(cap), float(ahorro))
        candidatos.append((p, "financial.loss_capacity_eur", f"Capacidad de pérdida {cap:,.0f} € de {ahorro:,.0f} € → {p.value}"))
    importe = valor(perfil, "objectives.o1.amount_eur")
    if cap is not None and importe is not None and float(importe) > float(cap):
        # Invertiría parte del colchón de 6 meses o del dinero de sus deudas: SUPUESTO v1, prudente.
        candidatos.append((PerfilRiesgo.CONSERVADOR, "objectives.o1.amount_eur",
                           f"Quiere invertir {float(importe):,.0f} €, más de lo que puede perder sin tocar su colchón "
                           f"({float(cap):,.0f} €) → {PerfilRiesgo.CONSERVADOR.value}"))
    plazo = valor(perfil, "objectives.o1.horizon_years")
    if plazo is not None:
        p = _por_plazo(float(plazo))
        candidatos.append((p, "objectives.o1.horizon_years", f"Plazo de {plazo} años → {p.value}"))

    pendientes = faltan(perfil)
    if not candidatos:
        return Idoneidad(complete=False, missing=pendientes)
    perfil_final = min(candidatos, key=lambda c: _indice(c[0]))[0]
    decisivos = [c[1] for c in candidatos if c[0] == perfil_final]
    return Idoneidad(
        complete=not pendientes,
        missing=pendientes,
        risk_profile=perfil_final,
        max_sri=MAX_SRI[perfil_final],
        rationale_ids=decisivos,
        rationale=[c[2] for c in candidatos] + [f"Manda el más restrictivo: {perfil_final.value} → SRI máximo {MAX_SRI[perfil_final]}"],
    )


# ---------- conveniencia ----------

def _fiable(f: Fact | None) -> bool:
    """Dato sin dudas abiertas: lo corrigió la entidad, o no tiene confianza baja ni incoherencias."""
    if f is None or f.value is None:
        return False
    return f.source == Fuente.advisor or not ({Flag.low_confidence, Flag.inconsistent} & set(f.flags))


def conveniencia(perfil: Perfil) -> dict[str, Conveniencia]:
    """Por familia: conocimiento comprobado suficiente, o experiencia que compense uno no comprobado.

    - Lo que el cliente dice saber no basta: el nivel cuenta si lo demostró en una pregunta de
      comprobación o lo fijó la entidad, y sin dudas abiertas.
    - La experiencia (OPERACIONES_EXPERIENCIA en 3 años, dato fiable) compensa un conocimiento que dice
      tener y no se ha comprobado, o uno parcial; nunca una comprobación fallada (`none` demostrado) ni
      un «no lo conozco».
    - Depósitos y monetarios: basta con que diga conocerlos (no complejos, riesgo mínimo), sin incoherencias.
    """
    out: dict[str, Conveniencia] = {}
    for fam in FAMILIAS:
        f = perfil.mifid.get(f"knowledge.{fam}")
        if f is None or f.value is None:
            out[fam] = Conveniencia.not_assessed
            continue
        minimo = "high" if fam == "complex_products" else "medium"
        comprobado = f.source in (Fuente.demonstrated, Fuente.advisor) and _fiable(f)
        suficiente = comprobado and NIVELES.index(f.value) >= NIVELES.index(minimo)
        if fam == "deposits_money_market":
            suficiente = f.value != "none" and (f.source == Fuente.advisor or Flag.inconsistent not in f.flags)
        f_ops = perfil.mifid.get(f"experience.{fam}.operations_last_3y")
        ops = int(f_ops.value) if _fiable(f_ops) else 0
        # `none` cubre tanto «no lo conozco» como una comprobación fallada: ahí la experiencia no compensa.
        compensa = (ops >= OPERACIONES_EXPERIENCIA and f.value != "none"
                    and (f.source == Fuente.advisor or Flag.inconsistent not in f.flags))
        out[fam] = Conveniencia.appropriate if (suficiente or compensa) else Conveniencia.not_appropriate
    return out


# ---------- restricciones para consumidores ----------

def restricciones(perfil: Perfil) -> Restricciones:
    s, conv = perfil.assessments.suitability, perfil.assessments.appropriateness
    motivos = list(s.rationale)
    usable = perfil.status == EstadoPerfil.active
    if not usable:
        motivos.append(f"Perfil en estado '{perfil.status.value}': no usable hasta que lo active la entidad")

    funds: dict = {"currency": "EUR"}  # supuesto: cliente minorista en euros
    portfolios: dict = {}
    if s.risk_profile:
        funds["max_risk"] = s.max_sri
        portfolios = {"profile": s.risk_profile.value, "risk_max": RISK_MAX_CARTERAS[s.risk_profile]}
    # Lista explícita siempre: [] significa «ningún tipo», nunca «cualquiera».
    funds["asset_type"] = [ASSET_TYPE[f] for f in ASSET_TYPE if conv.get(f) == Conveniencia.appropriate]

    bloqueadas: list[str] = []
    if not s.risk_profile:
        bloqueadas += ["funds", "portfolios", "etfs", "stocks"]
        motivos.append("Sin perfil de riesgo calculado: no se busca ningún producto")
    else:
        if not funds["asset_type"]:
            bloqueadas.append("funds")
            motivos.append("Ninguna familia de fondos es conveniente: no se buscan fondos")
        if conv.get("etfs") != Conveniencia.appropriate:
            bloqueadas.append("etfs")
            motivos.append("ETF no convenientes o sin evaluar: no se buscan ETF")
        else:
            motivos.append("ETF convenientes, pero el catálogo no da su SRRI: comprobar el riesgo en cada ficha "
                           f"(máximo {s.max_sri})")
        if conv.get("stocks") != Conveniencia.appropriate:
            bloqueadas.append("stocks")
            motivos.append("Acciones no convenientes o sin evaluar: no se buscan acciones")
        elif s.max_sri < SRI_MIN_ACCIONES:
            bloqueadas.append("stocks")
            motivos.append(f"Perfil {s.risk_profile.value} (SRI máximo {s.max_sri}): una acción suelta suele "
                           f"tener SRI {SRI_MIN_ACCIONES}–7, no se buscan acciones")

    pref = valor(perfil, "sustainability.preference")
    art = valor(perfil, "sustainability.min_sfdr_article")
    if pref in ("some", "strong") or (art is not None and int(art) >= 8):
        funds["esg_only"] = True

    post: list[FiltroPosterior] = []
    liquidez = valor(perfil, "objectives.o1.liquidity_need")
    if liquidez in REEMBOLSO_MAX_DIAS:
        post.append(FiltroPosterior(field="redemption_lag_days", op="<=", value=REEMBOLSO_MAX_DIAS[liquidez], why="liquidity_need"))
    plazo = valor(perfil, "objectives.o1.horizon_years")
    if plazo is not None and float(plazo) < 3:
        post.append(FiltroPosterior(field="fixed_income_term", op="in", value=["Corto plazo"], why="horizon_years"))
    if art is not None and int(art) == 9:
        post.append(FiltroPosterior(field="sustainability_article", op=">=", value=9, why="sustainability"))
    excl = perfil.personal.get("exclusions") or []
    if excl:
        post.append(FiltroPosterior(field="top_sectors", op="not_contains", value=excl, why="exclusions"))
    importe = valor(perfil, "objectives.o1.amount_eur")
    if importe is not None:
        post.append(FiltroPosterior(field="min_initial", op="<=", value=importe, why="objectives.o1.amount_eur"))

    no_conv = [f for f, v in conv.items() if v == Conveniencia.not_appropriate]
    refs = list(dict.fromkeys(s.rationale_ids + [f"knowledge.{f}" for f in no_conv]))
    return Restricciones(
        client_id=perfil.client_id, profile_version=perfil.version, status=perfil.status, usable=usable,
        funds_query=funds, portfolios_query=portfolios, post_filters=post,
        appropriateness={f: v for f, v in conv.items() if v != Conveniencia.not_assessed},
        blocked_searches=bloqueadas,
        evidence_refs=refs, rationale=motivos,
    )


def es_calculado(ruta: str) -> bool:
    return ruta in CALCULADOS
