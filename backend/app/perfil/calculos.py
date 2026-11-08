"""Cálculos deterministas del perfil. El modelo nunca pone estos números.

SUPUESTOS v0 (del equipo, no son fórmulas regulatorias; revisar con tutoría antes del pitch):
- Colchón de emergencia = 6 meses de gastos fijos.
- Capacidad de soportar pérdidas = ahorro líquido - colchón - deudas, nunca negativa.
- Riesgo máximo (SRI 1-7 del KID) = el mínimo de tres topes: tolerancia, plazo y conocimientos.
"""

from __future__ import annotations

from .modelos import CAMPOS_OBLIGATORIOS, EstadoPerfil, Perfil, Restricciones

MESES_COLCHON = 6

TOPE_POR_TOLERANCIA = {"low": 3, "medium": 5, "high": 7}
TOPE_POR_CONOCIMIENTO = {"none": 2, "basic": 3, "medium": 5, "high": 7}


def colchon_emergencia(gastos_fijos_mensuales: float) -> float:
    return round(MESES_COLCHON * gastos_fijos_mensuales, 2)


def capacidad_perdida(ahorro_liquido: float, colchon: float, deudas: float) -> float:
    return round(max(0.0, ahorro_liquido - colchon - deudas), 2)


def tope_por_plazo(horizonte_anios: float) -> int:
    if horizonte_anios < 2:
        return 2
    if horizonte_anios < 5:
        return 4
    if horizonte_anios < 8:
        return 6
    return 7


def _valor(perfil: Perfil, campo: str):
    c = perfil.mifid.get(campo)
    return None if c is None else c.value


def campos_pendientes(perfil: Perfil) -> list[str]:
    return [c for c in CAMPOS_OBLIGATORIOS if _valor(perfil, c) is None]


def restricciones(perfil: Perfil) -> Restricciones:
    faltan = campos_pendientes(perfil)
    motivos: list[str] = []
    topes: list[int] = []

    tolerancia = _valor(perfil, "risk.tolerance")
    if tolerancia in TOPE_POR_TOLERANCIA:
        topes.append(TOPE_POR_TOLERANCIA[tolerancia])
        motivos.append(f"Tolerancia '{tolerancia}' → riesgo máximo {TOPE_POR_TOLERANCIA[tolerancia]}")

    horizonte = _valor(perfil, "objective.horizon_years")
    if horizonte is not None:
        t = tope_por_plazo(float(horizonte))
        topes.append(t)
        motivos.append(f"Plazo de {horizonte} años → riesgo máximo {t}")

    # Se usa el conocimiento más bajo; si hay contradicción, manda el demostrado (value).
    niveles = [_valor(perfil, c) for c in ("knowledge.investment_funds", "knowledge.equity_risk")]
    niveles = [n for n in niveles if n in TOPE_POR_CONOCIMIENTO]
    if niveles:
        t = min(TOPE_POR_CONOCIMIENTO[n] for n in niveles)
        topes.append(t)
        motivos.append(f"Conocimientos demostrados ({', '.join(niveles)}) → riesgo máximo {t}")

    capacidad = _valor(perfil, "financial.loss_capacity_eur")
    if capacidad is not None:
        motivos.append(f"Capacidad de soportar pérdidas: {capacidad} € (cálculo determinista)")

    if horizonte is None:
        liquidez = None
    else:
        liquidez = "high" if horizonte < 2 else "medium" if horizonte < 5 else "low"

    esg = _valor(perfil, "sustainability.preference") in ("some", "strong")
    exclusiones = _valor(perfil, "exclusions.sectors") or []

    activo = perfil.status == EstadoPerfil.active
    if not activo:
        motivos.append(f"Perfil en estado '{perfil.status.value}': no apto hasta que lo active un asesor")

    return Restricciones(
        client_id=perfil.client_id,
        profile_version=perfil.version,
        eligible=activo and not faltan,
        missing_fields=faltan,
        max_risk_indicator=min(topes) if topes else None,
        horizon_years=horizonte,
        loss_capacity_eur=capacidad,
        liquidity_need=liquidez,
        esg_required=esg,
        exclusions=list(exclusiones),
        rationale=motivos,
    )
