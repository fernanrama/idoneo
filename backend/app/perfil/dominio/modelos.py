"""Modelo del perfil según el contrato 04 (docs/proyecto/04_CONTRATO_PERFIL.md). BORRADOR.

Decisión de diseño: internamente cada dato MiFID se guarda con su **ruta plana**
("knowledge.equity_funds", "objectives.o1.horizon_years"). `Perfil.exportar()` produce el JSON
anidado del contrato. Así los agentes escriben por ruta y la forma de salida puede cambiar
sin tocarles.

Este módulo convive con el v0 (`app/perfil/modelos.py`), que sigue usando la API actual
hasta que se coordine el cambio con front y agentes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def ahora() -> datetime:
    return datetime.now(timezone.utc)


# ---------- enumeraciones ----------

class Fuente(str, Enum):
    declared = "declared"          # lo dijo el cliente
    demonstrated = "demonstrated"  # lo demostró al responder una pregunta de comprobación
    calculated = "calculated"      # sale de una función determinista, nunca del modelo
    advisor = "advisor"            # lo corrigió una persona de la entidad


class EstadoPerfil(str, Enum):
    draft = "draft"                            # entrevista en curso o incompleta
    pending_validation = "pending_validation"  # completo, falta la revisión humana
    active = "active"                          # validado: único estado "apto para recomendar"
    review_due = "review_due"                  # hay que actualizar algo


class Nivel(str, Enum):
    none = "none"
    basic = "basic"
    medium = "medium"
    high = "high"


ORDEN_NIVEL: dict[str, int] = {"none": 0, "basic": 1, "medium": 2, "high": 3}


class Flag(str, Enum):
    declared_vs_demonstrated = "declared_vs_demonstrated"  # lo declarado no coincide con lo demostrado
    inconsistent = "inconsistent"                          # choca con otro dato
    low_confidence = "low_confidence"                      # hay que repreguntar
    needs_advisor = "needs_advisor"                        # el verificador pide revisión humana


class PerfilRiesgo(str, Enum):
    """Mismos valores que `search_portfolios.profile` del MCP de MyInvestor (docs/proyecto/05)."""

    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    DINAMICO = "DINAMICO"
    AGRESIVO = "AGRESIVO"
    MUY_AGRESIVO = "MUY_AGRESIVO"


ORDEN_PERFIL: list[PerfilRiesgo] = list(PerfilRiesgo)  # de menos a más riesgo


class Conveniencia(str, Enum):
    appropriate = "appropriate"
    not_appropriate = "not_appropriate"
    unknown = "unknown"  # falta el dato o la confianza es baja


class EstadoAlerta(str, Enum):
    open = "open"
    resolved = "resolved"


# ---------- autores (formato del contrato: agent:<x>, fn:<x>, advisor:<id>) ----------

AUTOR_EXTRACTOR = "agent:extractor"
AUTOR_VERIFICADOR = "agent:verifier"
AUTOR_FIXTURE = "fixture"
AUTOR_SISTEMA = "system"


def autor_funcion(nombre: str) -> str:
    return f"fn:{nombre}"


def autor_asesor(asesor_id: str) -> str:
    return f"advisor:{asesor_id}"


def es_asesor(autor: str) -> bool:
    return autor.startswith("advisor:")


def es_agente(autor: str) -> bool:
    return autor.startswith("agent:")


# ---------- piezas del perfil ----------

class Evidencia(BaseModel):
    session_id: str
    turn_id: str | None = None
    t: tuple[float, float] | None = Field(
        default=None, description="Segundos [inicio, fin] en la grabación; None en modo texto"
    )
    quote: str = Field(min_length=1, description="Cita literal de la transcripción")
    audio_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _acepta_formato_v0(cls, datos: Any) -> Any:
        """Acepta también `t_start`/`t_end` (contrato v0) para no romper a los agentes."""
        if isinstance(datos, dict) and "t" not in datos and "t_start" in datos:
            datos = dict(datos)
            inicio = datos.pop("t_start")
            fin = datos.pop("t_end", inicio)
            datos["t"] = (inicio, fin)
        return datos

    @field_validator("t")
    @classmethod
    def _tiempos_validos(cls, t: tuple[float, float] | None) -> tuple[float, float] | None:
        if t is not None and not (0 <= t[0] <= t[1]):
            raise ValueError("t debe cumplir 0 <= inicio <= fin")
        return t


class Fact(BaseModel):
    """Un dato del perfil con su procedencia. Es lo que diferencia el perfil de un formulario."""

    value: Any = None
    declared: Any = None  # lo que dijo el cliente, solo si difiere de value
    source: Fuente
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_basis: str | None = None  # p. ej. "rubric:knowledge.equity_funds:v1"
    evidence: list[Evidencia] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)  # solo para source=calculated
    flags: list[Flag] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=ahora)
    updated_by: str


class Alerta(BaseModel):
    id: str
    type: str  # valores conocidos: los de Flag
    field: str | None = None
    message: str
    evidence: list[Evidencia] = Field(default_factory=list)
    status: EstadoAlerta = EstadoAlerta.open
    created_at: datetime = Field(default_factory=ahora)
    created_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class Revision(BaseModel):
    validated_by: str | None = None
    validated_at: datetime | None = None
    next_review: str | None = None  # fecha ISO
    open_flags: int = 0


class Idoneidad(BaseModel):
    complete: bool = False
    missing: list[str] = Field(default_factory=list)
    risk_profile: PerfilRiesgo | None = None
    max_sri: int | None = Field(default=None, ge=1, le=7)
    portfolio_risk_max: int | None = Field(default=None, ge=0, le=5)
    rationale: list[str] = Field(default_factory=list)
    rationale_ids: list[str] = Field(default_factory=list)


class Evaluaciones(BaseModel):
    suitability: Idoneidad = Field(default_factory=Idoneidad)
    appropriateness: dict[str, Conveniencia] = Field(default_factory=dict)


class Perfil(BaseModel):
    client_id: str = Field(min_length=1, max_length=64)
    version: int = Field(default=1, ge=1)
    status: EstadoPerfil = EstadoPerfil.draft
    created_at: datetime = Field(default_factory=ahora)
    reason: str = "creación"
    author: str = AUTOR_SISTEMA
    mifid: dict[str, Fact] = Field(default_factory=dict)  # ruta plana -> dato
    assessments: Evaluaciones = Field(default_factory=Evaluaciones)  # siempre calculado
    alerts: list[Alerta] = Field(default_factory=list)
    review: Revision = Field(default_factory=Revision)

    def valor(self, ruta: str) -> Any:
        dato = self.mifid.get(ruta)
        return None if dato is None else dato.value

    def alertas_abiertas(self) -> list[Alerta]:
        return [a for a in self.alerts if a.status == EstadoAlerta.open]

    def exportar(self, personal: CapaPersonal | None = None) -> dict:
        """JSON con la forma del contrato 04 (capa MiFID anidada y, si hay consentimiento, la personal)."""
        datos = self.model_dump(mode="json", exclude={"mifid"})
        datos["mifid"] = anidar({r: d.model_dump(mode="json") for r, d in self.mifid.items()})
        if personal is not None and personal.consent_given:
            datos["personal"] = personal.exportar()
        return datos


def anidar(planos: dict[str, Any]) -> dict:
    """{"a.b": x} -> {"a": {"b": x}}; los objetivos pasan a lista [{"id": "o1", ...}]."""
    raiz: dict = {}
    for ruta in sorted(planos):
        nodo = raiz
        *padres, hoja = ruta.split(".")
        for p in padres:
            nodo = nodo.setdefault(p, {})
        nodo[hoja] = planos[ruta]
    if isinstance(raiz.get("objectives"), dict):
        raiz["objectives"] = [{"id": oid, **campos} for oid, campos in sorted(raiz["objectives"].items())]
    return raiz


class ActualizacionCampo(BaseModel):
    """Lo que escriben el extractor, el verificador o el asesor. Se direcciona por ruta."""

    field: str
    value: Any
    source: Fuente
    declared: Any = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_basis: str | None = None
    evidence: list[Evidencia] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)


class Turno(BaseModel):
    turn_id: str | None = None  # si el front lo manda, reenviar el mismo turno no lo duplica
    speaker: Literal["agent", "client"]
    text: str = Field(min_length=1)
    t_start: float | None = Field(default=None, ge=0)
    t_end: float | None = Field(default=None, ge=0)


# ---------- capa personal (separada, con consentimiento propio) ----------

BLOQUES_PERSONALES = frozenset({
    "life_stage", "income", "retirement", "held_elsewhere", "tax",
    "past_behaviour", "exclusions", "communication", "concerns",
})


class CapaPersonal(BaseModel):
    """Onboarding ampliado. Se guarda aparte de la capa MiFID para poder borrarla (RGPD)."""

    client_id: str
    version: int = Field(default=1, ge=1)
    consent_given: bool
    consent_at: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    author: str = AUTOR_SISTEMA
    created_at: datetime = Field(default_factory=ahora)

    @field_validator("data")
    @classmethod
    def _solo_bloques_conocidos(cls, data: dict[str, Any]) -> dict[str, Any]:
        desconocidos = set(data) - BLOQUES_PERSONALES
        if desconocidos:
            raise ValueError(f"Bloques personales no previstos: {sorted(desconocidos)}")
        exclusiones = data.get("exclusions")
        if exclusiones is not None and not (
            isinstance(exclusiones, list) and all(isinstance(x, str) for x in exclusiones)
        ):
            raise ValueError("exclusions debe ser una lista de textos")
        return data

    @model_validator(mode="after")
    def _sin_consentimiento_sin_datos(self) -> CapaPersonal:
        if not self.consent_given and self.data:
            raise ValueError("Sin consentimiento no se guardan datos personales")
        return self

    def exportar(self) -> dict:
        return {
            "consent": {"given": self.consent_given,
                        "at": self.consent_at.isoformat() if self.consent_at else None},
            **self.data,
        }


# ---------- restricciones para consumidores (get_investment_constraints) ----------

class FiltroPosterior(BaseModel):
    field: str  # campo de la ficha de MyInvestor
    op: Literal["<=", ">=", "==", "in", "not_contains"]
    value: Any
    why: str    # ruta del perfil que lo justifica


class ConsultaFondos(BaseModel):
    """Parámetros que se pasan tal cual a `search_funds` de MyInvestor."""

    max_risk: int | None = Field(default=None, ge=1, le=7)
    esg_only: bool = False
    currency: str | None = None
    asset_type: list[str] = Field(default_factory=list)


class ConsultaCarteras(BaseModel):
    """Parámetros que se pasan tal cual a `search_portfolios` de MyInvestor."""

    risk_max: int | None = Field(default=None, ge=0, le=5)
    profile: PerfilRiesgo | None = None


class Restricciones(BaseModel):
    client_id: str
    profile_version: int
    status: EstadoPerfil
    usable: bool  # solo True con perfil activo y completo
    missing: list[str] = Field(default_factory=list)
    max_sri: int | None = None
    risk_profile: PerfilRiesgo | None = None
    funds_query: ConsultaFondos = Field(default_factory=ConsultaFondos)
    portfolios_query: ConsultaCarteras = Field(default_factory=ConsultaCarteras)
    post_filters: list[FiltroPosterior] = Field(default_factory=list)
    appropriateness: dict[str, Conveniencia] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)

    # Alias de solo lectura con los nombres del contrato v0 (los usa agentes/contexto.py).
    @property
    def eligible(self) -> bool:
        return self.usable

    @property
    def max_risk_indicator(self) -> int | None:
        return self.max_sri
