"""Rúbrica de confianza v1 (B1). Determinista: el modelo clasifica, este módulo puntúa.

Contrato 04: `confidence` sale de una rúbrica fija, nunca de la opinión del modelo, y `confidence_basis`
dice qué rúbrica la produjo. El modelo solo aporta categorías cerradas y comprobables con la cita:
- para un dato declarado, si el cliente lo dijo de forma explícita, aproximada o hay que inferirlo;
- para una pregunta de comprobación, si la respuesta fue correcta, parcial o incorrecta;
- para el escenario de caída, qué reacción eligió.
Con eso, aquí se fijan el valor demostrado, la confianza y el flag `low_confidence`.

SUPUESTOS v1 (revisables con tutoría; cambiar los números exige subir la versión):
- Una respuesta incorrecta a una comprobación es evidencia fuerte de falta de conocimiento (0,85).
- Una sola respuesta correcta demuestra al menos un nivel medio; si el cliente declaró nivel alto, se
  acepta alto con menos confianza (0,75), porque una pregunta no basta para probar un nivel alto.
- Un conocimiento solo declarado, sin comprobar, no llega al mínimo: hay que repreguntar.
"""

from __future__ import annotations

from typing import Literal

VERSION = "v1"
UMBRAL = 0.65  # por debajo, el dato lleva low_confidence y el entrevistador debe repreguntar

Certeza = Literal["explicita", "aproximada", "inferida"]
Resultado = Literal["correcta", "parcial", "incorrecta"]
Reaccion = Literal["vender_todo", "vender_parte", "mantener", "comprar_algo", "comprar_mucho"]
Nivel = Literal["none", "basic", "medium", "high"]

CONFIANZA_CERTEZA: dict[str, float] = {"explicita": 0.9, "aproximada": 0.75, "inferida": 0.55}
CONFIANZA_SOLO_DECLARADO = 0.5

# Escenario: «sus ahorros bajan un X % en unos meses, ¿qué haría?» → puntuación 1–5 del contrato.
PUNTUACION_REACCION: dict[str, int] = {
    "vender_todo": 1, "vender_parte": 2, "mantener": 3, "comprar_algo": 4, "comprar_mucho": 5,
}
CONFIANZA_ESCENARIO = {"explicita": 0.85, "aproximada": 0.7, "inferida": 0.55}


def base(ruta: str) -> str:
    return f"rubric:{ruta}:{VERSION}"


def baja(confianza: float | None) -> bool:
    return confianza is not None and confianza < UMBRAL


def dato_declarado(certeza: str) -> tuple[float, str]:
    """Confianza de un dato que el cliente cuenta de sí mismo (ingresos, plazo, objetivo…)."""
    return CONFIANZA_CERTEZA.get(certeza, CONFIANZA_CERTEZA["inferida"]), f"rubric:certeza.{certeza}:{VERSION}"


def conocimiento(ruta: str, declarado: str | None, resultado: str | None) -> tuple[str | None, str, float, str]:
    """Nivel de conocimiento de una familia. Devuelve (valor, fuente, confianza, base).

    Sin comprobación, el valor es el declarado y la fuente `declared`; con comprobación, `demonstrated`.
    """
    if resultado is None:
        return declarado, "declared", CONFIANZA_SOLO_DECLARADO, base(ruta)
    if resultado == "incorrecta":
        return "none", "demonstrated", 0.85, base(ruta)
    if resultado == "parcial":
        return "basic", "demonstrated", 0.7, base(ruta)
    # correcta
    if declarado == "high":
        return "high", "demonstrated", 0.75, base(ruta)
    return "medium", "demonstrated", 0.85, base(ruta)


def escenario(reaccion: str, certeza: str) -> tuple[int, float, str]:
    """Puntuación de tolerancia (1–5) a partir de la reacción elegida en el escenario de caída."""
    return (
        PUNTUACION_REACCION[reaccion],
        CONFIANZA_ESCENARIO.get(certeza, CONFIANZA_ESCENARIO["inferida"]),
        base("risk_tolerance.scenarios"),
    )

