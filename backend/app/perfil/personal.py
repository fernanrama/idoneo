"""Capa personal (onboarding ampliado), separada de la capa MiFID.

Base legal distinta: la capa MiFID es obligación legal (RGPD 6.1.c); la personal necesita
consentimiento propio. Se guarda aparte para poder borrarla (derecho de supresión) sin tocar el
registro MiFID. Hacia fuera se sigue viendo en `Perfil.personal`, con la forma del contrato 04:
`{"consent": {"given": true, "at": "..."}, "exclusions": [...], ...}`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .modelos import ahora

BLOQUES = frozenset({
    "life_stage", "retirement", "held_elsewhere", "tax",
    "exclusions", "communication", "concerns",
})


class CapaPersonal(BaseModel):
    client_id: str
    version: int = Field(default=1, ge=1)
    consent_given: bool
    consent_at: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    author: str = "system"
    created_at: datetime = Field(default_factory=ahora)

    @field_validator("data")
    @classmethod
    def _solo_bloques_previstos(cls, data: dict[str, Any]) -> dict[str, Any]:
        desconocidos = set(data) - BLOQUES
        if desconocidos:
            raise ValueError(f"Bloques personales no previstos: {sorted(desconocidos)}")
        excl = data.get("exclusions")
        if excl is not None and not (isinstance(excl, list) and all(isinstance(x, str) for x in excl)):
            raise ValueError("exclusions debe ser una lista de textos")
        return data

    @model_validator(mode="after")
    def _sin_consentimiento_no_hay_datos(self) -> CapaPersonal:
        if not self.consent_given and self.data:
            raise ValueError("Sin consentimiento no se guardan datos personales")
        return self

    def exportar(self) -> dict[str, Any]:
        """Forma del contrato 04. Sin consentimiento no se expone nada."""
        if not self.consent_given:
            return {}
        return {"consent": {"given": True, "at": self.consent_at.isoformat() if self.consent_at else None},
                **self.data}


def separar(personal: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """`{"consent": {"given": ...}, ...datos}` → (consentimiento, datos)."""
    personal = dict(personal or {})
    consent = personal.pop("consent", None) or {}
    return bool(consent.get("given")), personal
