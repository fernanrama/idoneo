"""Capa personal (onboarding ampliado), separada de la capa MiFID.

Base legal distinta: la capa MiFID es obligación legal (RGPD 6.1.c); la personal necesita
consentimiento propio. Se guarda aparte para poder borrarla (derecho de supresión) sin tocar el
registro MiFID. Hacia fuera se sigue viendo en `Perfil.personal`, con la forma del contrato 04:
`{"consent": {"given": true, "at": "..."}, "exclusions": [...], ...}`.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .modelos import ahora

BLOQUES = frozenset({
    "life_stage", "retirement", "held_elsewhere", "tax",
    "exclusions", "communication", "concerns",
})
MAX_BYTES = 4096
MAX_ELEMENTOS = 20
MAX_TEXTO = 300


class PreferenciasComunicacion(BaseModel):
    """Preferencias cerradas que sí pueden proyectarse al agente de conversación."""

    treatment: Literal["usted", "tu"] | None = None
    detail: Literal["low", "normal", "high"] | None = None
    pace: Literal["slow", "normal", "fast"] | None = None
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    channel: Literal["web", "app", "phone", "whatsapp", "email"] | None = None
    format: Literal["voice", "audio", "text", "mixed"] | None = None


def _lista_textos(valor: Any, campo: str) -> list[str]:
    if not isinstance(valor, list) or len(valor) > MAX_ELEMENTOS:
        raise ValueError(f"{campo} debe ser una lista de hasta {MAX_ELEMENTOS} textos")
    salida = []
    for elemento in valor:
        if not isinstance(elemento, str) or not elemento.strip() or len(elemento.strip()) > MAX_TEXTO:
            raise ValueError(f"cada elemento de {campo} debe tener entre 1 y {MAX_TEXTO} caracteres")
        salida.append(elemento.strip())
    return salida


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
        data = dict(data)
        desconocidos = set(data) - BLOQUES
        if desconocidos:
            raise ValueError(f"Bloques personales no previstos: {sorted(desconocidos)}")
        if "communication" in data:
            data["communication"] = PreferenciasComunicacion.model_validate(data["communication"]).model_dump(
                exclude_none=True
            )
        for campo in ("exclusions", "concerns"):
            if campo in data:
                data[campo] = _lista_textos(data[campo], campo)
        try:
            serializado = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as e:
            raise ValueError("la capa personal debe contener datos JSON") from e
        if len(serializado.encode("utf-8")) > MAX_BYTES:
            raise ValueError(f"la capa personal supera {MAX_BYTES} bytes")
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
