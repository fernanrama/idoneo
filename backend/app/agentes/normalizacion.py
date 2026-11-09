"""Normalización determinista de lo que devuelve el modelo (B1).

- Números como los dice un cliente español: «1.450», «1.450,50», «80 mil», «1,5 millones», «unos 900 €».
- Rangos («entre 800 y 1.000», «800-1000»): punto medio, marcado como aproximado.
- Importes anuales de campos mensuales: se dividen entre 12 aquí, no en el modelo (el modelo no calcula).
- Citas: comparación literal tolerante a mayúsculas, tildes, puntuación y espacios (transcripción de voz).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..perfil.validacion import TIPOS

# Campos mensuales que el cliente a veces da en cifra anual («gano 30.000 al año»).
MENSUALES = {"financial.net_monthly_income_eur", "financial.fixed_monthly_costs_eur"}
LIMITE_CITA = 400    # una cita es un fragmento, no un turno entero copiado
LIMITE_TEXTO = 200   # textos breves del perfil (objetivo, profesión, comportamiento pasado)

_MULTIPLICADORES = {"mil": 1_000, "k": 1_000, "millon": 1_000_000, "millones": 1_000_000, "m": 1_000_000}
_NUMERO = re.compile(r"^[+-]?\d[\d.,]*$")
_RANGO = re.compile(r"^(?:entre\s+)?(.+?)\s*(?:-|–|—|\by\b|\ba\b)\s*(.+)$")
_BOOL = {"true": True, "false": False, "si": True, "sí": True, "no": False}


@dataclass(frozen=True)
class Valor:
    valor: object
    aproximado: bool = False  # rango, conversión anual→mensual…: rebaja la certeza a «aproximada»


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _cifra(texto: str) -> float:
    """«1.450» → 1450; «1.450,5» → 1450.5; «0,5» → 0.5; «1,000» → 1000; «2.5» → 2.5."""
    t = texto.strip().replace(" ", "")
    if not _NUMERO.match(t):
        raise ValueError(f"{texto!r} no es un número")
    if "." in t and "," in t:  # formato español: punto de miles y coma decimal
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", t) else t.replace(",", ".")
    elif "." in t and re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    return float(t)


def numero(texto: str) -> Valor:
    """Número de un cliente hispanohablante, con unidades, multiplicadores y rangos."""
    t = sin_tildes(texto).casefold().strip()
    t = re.sub(r"(€|eur(os)?|%|por ?ciento|aprox\.?|unos|unas|alrededor de|mas o menos|~)", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    rango = _RANGO.match(t)
    if rango and not _NUMERO.match(t.replace(" ", "")):
        a, b = numero(rango.group(1)).valor, numero(rango.group(2)).valor
        return Valor(round((float(a) + float(b)) / 2, 2), aproximado=True)
    partes = t.split(" ")
    if len(partes) == 2 and partes[1] in _MULTIPLICADORES:
        return Valor(_cifra(partes[0]) * _MULTIPLICADORES[partes[1]])
    m = re.fullmatch(r"([\d.,]+)(k|m)", t)
    if m:
        return Valor(_cifra(m.group(1)) * _MULTIPLICADORES[m.group(2)])
    return Valor(_cifra(t))


def convertir(campo: str, texto: str, periodo: str | None = None) -> Valor:
    """Texto del modelo → valor con el tipo del catálogo. ValueError si no encaja (el dato se descarta)."""
    tipo = TIPOS[campo][0]
    t = texto.strip()
    if tipo == "bool":
        clave = t.casefold()
        if clave not in _BOOL:
            raise ValueError(f"{campo}: {texto!r} no es true/false")
        return Valor(_BOOL[clave])
    if tipo in ("eur", "anios", "pct"):
        v = numero(t)
        if campo in MENSUALES and periodo == "anual":
            return Valor(round(float(v.valor) / 12, 2), aproximado=True)  # SUPUESTO: 12 pagas
        return v
    if tipo in ("entero", "sfdr", "puntuacion"):
        v = numero(t)
        if float(v.valor) != int(float(v.valor)):
            raise ValueError(f"{campo}: {texto!r} no es un entero")
        return Valor(int(float(v.valor)), v.aproximado)
    if tipo == "texto":
        limpio = limpiar(t)
        if not limpio:
            raise ValueError(f"{campo}: texto vacío")
        return Valor(limpio[:LIMITE_TEXTO])
    return Valor(t)  # opciones: las valida store


def limpiar(texto: str) -> str:
    """Quita caracteres de control y espacios de más (texto que entra en el prompt o en el perfil)."""
    sin_control = "".join(c for c in texto if unicodedata.category(c)[0] != "C" or c in "\n\t")
    return re.sub(r"\s+", " ", sin_control).strip()


def _para_comparar(texto: str) -> str:
    t = sin_tildes(unicodedata.normalize("NFKC", texto)).casefold()
    t = re.sub(r"[^\w\s%€]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def cita_valida(cita: str, texto: str) -> bool:
    """La cita es un fragmento real del turno (ignorando mayúsculas, tildes, puntuación y espacios)."""
    c = _para_comparar(cita)
    return 2 <= len(c) <= LIMITE_CITA and c in _para_comparar(texto)
