"""Traduce el perfil a las reglas que cualquier recomendación debe cumplir (get_investment_constraints).

Las devuelve en el idioma del consumidor: parámetros para el MCP de MyInvestor y filtros
posteriores sobre la ficha. Nosotros no filtramos nada; lo hace el agente de la entidad.
"""

from __future__ import annotations

from . import supuestos as S
from .esquema import ASSET_TYPE_POR_FAMILIA
from .evaluaciones import objetivo_principal
from .modelos import (
    CapaPersonal,
    ConsultaCarteras,
    ConsultaFondos,
    Conveniencia,
    EstadoPerfil,
    FiltroPosterior,
    Perfil,
    Restricciones,
)


def _por_tramos(valor: float, tramos):
    for limite, resultado in tramos:
        if valor < limite:
            return resultado
    return None


def calcular(perfil: Perfil, personal: CapaPersonal | None = None) -> Restricciones:
    ido = perfil.assessments.suitability
    conv = perfil.assessments.appropriateness
    v = perfil.valor
    motivos = list(ido.rationale)
    filtros: list[FiltroPosterior] = []

    obj = objetivo_principal(perfil)
    plazo = v(f"objectives.{obj}.horizon_years") if obj else None
    importe = v(f"objectives.{obj}.amount_eur") if obj else None

    liquidez = v(f"objectives.{obj}.liquidity_need") if obj else None
    origen_liquidez = f"objectives.{obj}.liquidity_need"
    if liquidez is None and plazo is not None:
        liquidez = _por_tramos(plazo, S.TRAMOS_LIQUIDEZ_POR_PLAZO)
        origen_liquidez = f"objectives.{obj}.horizon_years"
    if liquidez in S.DIAS_REEMBOLSO_MAX:
        filtros.append(FiltroPosterior(field="redemption_lag_days", op="<=",
                                       value=S.DIAS_REEMBOLSO_MAX[liquidez], why=origen_liquidez))

    if plazo is not None and (plazos_rf := _por_tramos(plazo, S.PLAZOS_RENTA_FIJA_POR_HORIZONTE)):
        filtros.append(FiltroPosterior(field="fixed_income_term", op="in", value=plazos_rf,
                                       why=f"objectives.{obj}.horizon_years"))

    articulo = v("sustainability.min_sfdr_article")
    if articulo in (8, 9):
        filtros.append(FiltroPosterior(field="sustainability_article", op=">=", value=articulo,
                                       why="sustainability.min_sfdr_article"))

    if personal is not None and personal.consent_given and (excl := personal.data.get("exclusions")):
        filtros.append(FiltroPosterior(field="top_sectors", op="not_contains", value=list(excl),
                                       why="personal.exclusions"))

    if importe:
        filtros.append(FiltroPosterior(field="min_initial", op="<=", value=importe,
                                       why=f"objectives.{obj}.amount_eur"))

    tipos = [t for f, t in ASSET_TYPE_POR_FAMILIA.items() if conv.get(f) == Conveniencia.appropriate]
    no_convenientes = sorted(f for f, c in conv.items() if c == Conveniencia.not_appropriate)
    if no_convenientes:
        motivos.append(f"No conveniente sin asesoramiento: {', '.join(no_convenientes)}")

    activo = perfil.status == EstadoPerfil.active
    if not activo:
        motivos.append(f"Perfil en estado '{perfil.status.value}': no usable hasta que lo valide la entidad")
    if ido.missing:
        motivos.append(f"Faltan datos obligatorios: {', '.join(ido.missing)}")

    return Restricciones(
        client_id=perfil.client_id,
        profile_version=perfil.version,
        status=perfil.status,
        usable=activo and ido.complete,
        missing=ido.missing,
        max_sri=ido.max_sri,
        risk_profile=ido.risk_profile,
        funds_query=ConsultaFondos(
            max_risk=ido.max_sri,
            esg_only=v("sustainability.preference") in ("some", "strong"),
            currency=S.DIVISA_POR_DEFECTO,
            asset_type=tipos,
        ),
        portfolios_query=ConsultaCarteras(risk_max=ido.portfolio_risk_max, profile=ido.risk_profile),
        post_filters=filtros,
        appropriateness=conv,
        evidence_refs=ido.rationale_ids,
        rationale=motivos,
    )
