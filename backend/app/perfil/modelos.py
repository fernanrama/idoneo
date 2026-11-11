"""Modelo de datos del perfil (contrato v1).

Especificación: docs/diseno/03-contrato-perfil.md (Alex). Este módulo la implementa;
las desviaciones están listadas en docs/contratos.md. Cambios aquí = PR avisada al equipo.

Decisión de implementación: la capa `mifid` es un mapa plano de rutas con punto
("knowledge.equity_funds", "objectives.o1.horizon_years") a `Fact`. Equivale al JSON anidado
de la especificación y simplifica los parches (`profile.patch` ya usa `path`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def ahora() -> datetime:
    return datetime.now(timezone.utc)


# ---------- dato ----------

class Fuente(str, Enum):
    declared = "declared"          # lo dijo el cliente
    demonstrated = "demonstrated"  # lo demostró en una pregunta de comprobación
    calculated = "calculated"      # función determinista, nunca el modelo
    advisor = "advisor"            # lo corrigió alguien de la entidad


class Flag(str, Enum):
    declared_vs_demonstrated = "declared_vs_demonstrated"
    inconsistent = "inconsistent"
    low_confidence = "low_confidence"
    needs_advisor = "needs_advisor"


class Evidencia(BaseModel):
    session_id: str
    turn_id: str | None = None
    t: tuple[float, float] = Field(description="Segundos [inicio, fin] en la grabación de la sesión")
    quote: str = Field(description="Cita literal")
    audio_url: str | None = None  # clip, cuando exista


class Fact(BaseModel):
    value: Any = None
    declared: Any = None  # solo si difiere de value
    source: Fuente
    confidence: float | None = Field(default=None, ge=0, le=1)  # de una rúbrica fija, nunca del modelo
    confidence_basis: str | None = None  # p. ej. "rubric:knowledge.equity_funds:v1"
    evidence: list[Evidencia] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)  # rutas de las que sale un valor calculado
    flags: list[Flag] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=ahora)
    updated_by: str  # "agent:extractor", "agent:verifier", "fn:<nombre>", "advisor:<id>", "fixture"
    # Última vez que se confirmó el MISMO dato con una cita nueva (no cambia value ni updated_at; la
    # evidencia se acumula). Diseño 06, §4.3. None si nunca se ha confirmado.
    confirmed_at: datetime | None = None
    confirmed_by: str | None = None


# ---------- perfil ----------

class EstadoPerfil(str, Enum):
    draft = "draft"                            # entrevista en curso o incompleta
    pending_validation = "pending_validation"  # completo; falta la revisión humana
    active = "active"                          # validado: único estado usable para recomendar
    review_due = "review_due"                  # hay que actualizar algo


class EstadoAlerta(str, Enum):
    open = "open"
    resolved = "resolved"


class Alerta(BaseModel):
    """Texto legible de un flag, para el front (evento flag.raised) y el asesor."""

    id: str
    path: str | None = None
    flag: Flag
    message: str
    evidence: list[Evidencia] = Field(default_factory=list)
    status: EstadoAlerta = EstadoAlerta.open
    created_at: datetime = Field(default_factory=ahora)
    # Trazabilidad (añadido en la integración de persistencia; opcional, no rompe al front).
    created_by: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None


class PerfilRiesgo(str, Enum):  # mismos valores que `profile` en search_portfolios de MyInvestor
    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    DINAMICO = "DINAMICO"
    AGRESIVO = "AGRESIVO"
    MUY_AGRESIVO = "MUY_AGRESIVO"


class Conveniencia(str, Enum):
    appropriate = "appropriate"
    not_appropriate = "not_appropriate"
    not_assessed = "not_assessed"


class Idoneidad(BaseModel):
    complete: bool = False
    missing: list[str] = Field(default_factory=list)
    risk_profile: PerfilRiesgo | None = None
    max_sri: int | None = Field(default=None, ge=1, le=7)
    rationale_ids: list[str] = Field(default_factory=list)  # rutas que han determinado el resultado
    rationale: list[str] = Field(default_factory=list)      # explicación legible (añadido v1)


class Resultados(BaseModel):
    suitability: Idoneidad = Field(default_factory=Idoneidad)
    appropriateness: dict[str, Conveniencia] = Field(default_factory=dict)


class Revision(BaseModel):
    validated_by: str | None = None
    validated_at: datetime | None = None
    next_review: str | None = None  # fecha ISO
    open_flags: int = 0


class Perfil(BaseModel):
    client_id: str
    version: int = 1
    status: EstadoPerfil = EstadoPerfil.draft
    created_at: datetime = Field(default_factory=ahora)
    reason: str = "created"
    author: str = "system"
    mifid: dict[str, Fact] = Field(default_factory=dict)
    assessments: Resultados = Field(default_factory=Resultados)  # siempre calculado, nunca escrito a mano
    personal: dict[str, Any] = Field(default_factory=dict)       # capa opcional, base legal distinta
    alerts: list[Alerta] = Field(default_factory=list)
    review: Revision = Field(default_factory=Revision)


# ---------- escritura y sesión ----------

class Parche(BaseModel):
    """Lo que escriben el extractor, el verificador o el asesor (`changes[]`)."""

    path: str
    value: Any
    source: Fuente
    declared: Any = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_basis: str | None = None
    evidence: list[Evidencia] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)


class Turno(BaseModel):
    turn_id: str | None = None  # si no viene, lo asigna el backend
    speaker: str = Field(pattern="^(agent|client)$")
    text: str
    # Tiempos medidos en el navegador (aproximados). El webhook de fin de llamada los sustituirá.
    t_start: float
    t_end: float


# ---------- restricciones para consumidores ----------

class FiltroPosterior(BaseModel):
    field: str
    op: str  # "<=", ">=", "in", "not_contains"
    value: Any
    why: str


class RevisionPendiente(BaseModel):
    """Datos del perfil servido que han cambiado en una versión posterior aún sin validar.

    Decisión §4.6 de docs/diseno/06-actualizacion-continua.md (opción B): se sigue sirviendo el último
    `active`, pero el consumidor sabe qué está en revisión y no debe apoyarse en esas rutas para recomendar.
    """

    since_version: int            # primera versión posterior a la servida
    latest_version: int
    latest_status: EstadoPerfil
    paths: list[str]              # rutas MiFID cuyo valor cambió o con alertas nuevas abiertas
    opened_at: datetime           # cuándo se creó `since_version`
    # Qué resultados mueve el cambio pendiente (`alcance.es_material`: perfil de riesgo, conveniencia, filtros…).
    # Vacío: el dato cambió pero no altera las restricciones (p. ej. los ingresos). Añadido el 11/11 (R6).
    material: list[str] = Field(default_factory=list)


class Restricciones(BaseModel):
    client_id: str
    profile_version: int
    status: EstadoPerfil
    usable: bool  # solo con perfil active
    pending_review: RevisionPendiente | None = None  # §4.6: qué está en revisión; null si nada
    funds_query: dict[str, Any] = Field(default_factory=dict)       # parámetros de search_funds
    portfolios_query: dict[str, Any] = Field(default_factory=dict)  # parámetros de search_portfolios
    post_filters: list[FiltroPosterior] = Field(default_factory=list)
    appropriateness: dict[str, Conveniencia] = Field(default_factory=dict)
    # Búsquedas que no se hacen para este cliente: "funds", "portfolios", "etfs", "stocks".
    blocked_searches: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


# ---------- catálogo de campos del MVP ----------

FAMILIAS = [
    "deposits_money_market",
    "fixed_income_funds",
    "mixed_funds",
    "equity_funds",
    "etfs",
    "stocks",
    "complex_products",
]

NIVELES = ["none", "basic", "medium", "high"]

CAMPOS: dict[str, str] = {
    "disclosures.ai_notice_ack": "bool",
    "disclosures.purpose_ack": "bool",
    **{f"knowledge.{f}": "none|basic|medium|high" for f in FAMILIAS},
    **{f"experience.{f}.operations_last_3y": "int" for f in FAMILIAS},
    "experience.education": "str",
    "experience.profession": "str",
    "financial.net_monthly_income_eur": "float",
    "financial.income_stability": "stable|variable",
    "financial.fixed_monthly_costs_eur": "float",
    "financial.liquid_savings_eur": "float",
    "financial.other_assets_eur": "float",
    "financial.debts_eur": "float (deudas sin contar la hipoteca de la vivienda)",
    "financial.mortgage_eur": "float (hipoteca pendiente de la vivienda)",
    "financial.emergency_fund_months": "float (calculado)",
    "financial.loss_capacity_eur": "float (calculado)",
    "objectives.o1.goal": "str",
    "objectives.o1.amount_eur": "float",
    "objectives.o1.horizon_years": "float",
    "objectives.o1.liquidity_need": "high|medium|low",
    "risk_tolerance.scenario_score": "int 1-5 (rúbrica de escenarios)",
    "risk_tolerance.max_drawdown_accepted_pct": "float",
    "risk_tolerance.past_behaviour": "str",
    "sustainability.preference": "none|some|strong",
    "sustainability.min_sfdr_article": "6|8|9",
    "sustainability.explained": "bool",
}

CALCULADOS = {"financial.emergency_fund_months", "financial.loss_capacity_eur"}

# PROPUESTA (decisión abierta en el contrato): sin estos campos, suitability.complete = false.
OBLIGATORIOS: list[str] = [
    "disclosures.ai_notice_ack",
    "disclosures.purpose_ack",
    "knowledge.fixed_income_funds",
    "knowledge.equity_funds",
    "financial.net_monthly_income_eur",
    "financial.fixed_monthly_costs_eur",
    "financial.liquid_savings_eur",
    "financial.debts_eur",
    "objectives.o1.goal",
    "objectives.o1.horizon_years",
    "risk_tolerance.scenario_score",
    "sustainability.preference",
]
