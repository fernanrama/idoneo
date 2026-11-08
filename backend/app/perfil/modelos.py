"""Modelo de datos del perfil de Idóneo (contrato v0).

Es la fuente única de verdad del contrato descrito en docs/CONTRATOS.md.
Cualquier cambio aquí se coordina con el resto del equipo antes de fusionar.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Fuente(str, Enum):
    declared = "declared"          # lo dijo el cliente
    demonstrated = "demonstrated"  # lo demostró al responder una pregunta de comprobación
    calculated = "calculated"      # sale de una función determinista (nunca del modelo)
    advisor = "advisor"            # lo corrigió una persona de la entidad


class Autor(str, Enum):
    extractor = "extractor"
    verificador = "verificador"
    calculo = "calculo"
    asesor = "asesor"
    fixture = "fixture"


class EstadoPerfil(str, Enum):
    draft = "draft"                    # borrador: lo están rellenando los agentes
    validated = "validated"            # revisado por el asesor
    active = "active"                  # único estado "apto para recomendar"
    review_pending = "review_pending"  # hay que reevaluar


class Nivel(str, Enum):
    none = "none"
    basic = "basic"
    medium = "medium"
    high = "high"


class Evidencia(BaseModel):
    session_id: str
    t_start: float = Field(description="Segundos desde el inicio de la sesión")
    t_end: float
    quote: str = Field(description="Cita literal de la transcripción")


class Campo(BaseModel):
    value: Any = None
    source: Fuente
    declared: Any = None  # lo que el cliente dijo, si difiere de value
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: list[Evidencia] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)  # solo para source=calculated
    flags: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=ahora)
    updated_by: Autor


class EstadoAlerta(str, Enum):
    open = "open"
    resolved = "resolved"


class Alerta(BaseModel):
    id: str
    type: str  # p. ej. "declared_vs_demonstrated", "incoherencia", "falta_dato"
    field: str | None = None
    message: str
    evidence: list[Evidencia] = Field(default_factory=list)
    status: EstadoAlerta = EstadoAlerta.open
    created_at: datetime = Field(default_factory=ahora)


class Revision(BaseModel):
    validated_by: str | None = None
    validated_at: datetime | None = None
    next_review: str | None = None  # fecha ISO


class Perfil(BaseModel):
    client_id: str
    version: int = 1
    status: EstadoPerfil = EstadoPerfil.draft
    created_at: datetime = Field(default_factory=ahora)
    reason: str = "creación"  # motivo de esta versión
    mifid: dict[str, Campo] = Field(default_factory=dict)
    personal: dict[str, Any] = Field(default_factory=dict)  # fuera del MVP
    alerts: list[Alerta] = Field(default_factory=list)
    review: Revision = Field(default_factory=Revision)


class ActualizacionCampo(BaseModel):
    """Lo que devuelve el extractor (o el asesor) para escribir en el perfil."""

    field: str
    value: Any
    source: Fuente
    declared: Any = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: list[Evidencia] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


class Turno(BaseModel):
    speaker: str = Field(pattern="^(agent|client)$")
    text: str
    t_start: float
    t_end: float


class Restricciones(BaseModel):
    """Salida de get_investment_constraints: filtros que cualquier recomendación debe cumplir."""

    client_id: str
    profile_version: int
    eligible: bool  # apto para recomendar: perfil activo y sin campos obligatorios pendientes
    missing_fields: list[str]
    max_risk_indicator: int | None = Field(default=None, ge=1, le=7)  # SRI del KID (PRIIPs)
    horizon_years: float | None = None
    loss_capacity_eur: float | None = None  # pérdida máxima asumible, no importe a invertir
    liquidity_need: str | None = None  # "high" | "medium" | "low"
    esg_required: bool = False
    exclusions: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)  # por qué sale cada límite


# Campos de la capa MiFID del MVP. Ver docs/CONTRATOS.md para tipos y significado.
CAMPOS_MIFID: dict[str, str] = {
    "consent.recording": "bool",
    "consent.ai_notice": "bool",
    "knowledge.investment_funds": "Nivel",
    "knowledge.equity_risk": "Nivel",
    "experience.past_investments": "str",
    "financial.monthly_income_eur": "float",
    "financial.monthly_fixed_costs_eur": "float",
    "financial.liquid_savings_eur": "float",
    "financial.debts_eur": "float",
    "financial.emergency_fund_eur": "float (calculado)",
    "financial.loss_capacity_eur": "float (calculado)",
    "objective.goal": "str",
    "objective.amount_eur": "float",
    "objective.horizon_years": "float",
    "risk.reaction_to_drop": "str",
    "risk.tolerance": "low|medium|high",
    "sustainability.preference": "none|some|strong",
    "sustainability.explained": "bool",
    "exclusions.sectors": "list[str]",
}

# Sin estos campos el perfil no puede ser "apto para recomendar".
CAMPOS_OBLIGATORIOS: list[str] = [
    "consent.recording",
    "consent.ai_notice",
    "knowledge.investment_funds",
    "knowledge.equity_risk",
    "financial.monthly_income_eur",
    "financial.monthly_fixed_costs_eur",
    "financial.liquid_savings_eur",
    "financial.debts_eur",
    "objective.goal",
    "objective.horizon_years",
    "risk.tolerance",
    "sustainability.preference",
]
