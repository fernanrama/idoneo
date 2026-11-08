"""SUPUESTOS DEL EQUIPO (borrador). No son fórmulas regulatorias.

Todo número o tabla que decide algo sobre el cliente está aquí, en un solo sitio, para revisarlo
con Alejandro (contrato 04, "decisiones abiertas") y con Rodrigo (revisión financiera y normativa)
antes del pitch. Cambiar un valor aquí no obliga a tocar el resto del código; los tests que
dependen de un valor concreto lo importan desde este módulo.
"""

from __future__ import annotations

from .modelos import PerfilRiesgo as P

# --- Campos obligatorios para que `suitability.complete` sea True (decisión abierta del contrato 04) ---
CAMPOS_OBLIGATORIOS: tuple[str, ...] = (
    "disclosures.ai_notice_ack",
    "disclosures.purpose_ack",
    "knowledge.equity_funds",
    "knowledge.fixed_income_funds",
    "financial.net_monthly_income_eur",
    "financial.fixed_monthly_costs_eur",
    "financial.liquid_savings_eur",
    "financial.debts_eur",
    "objectives.o1.goal",
    "objectives.o1.horizon_years",
    "risk_tolerance.scenario_score",
    "sustainability.preference",
)

# --- Rúbrica de confianza ---
# confianza = respuestas de comprobación coherentes con el nivel asignado / preguntas hechas.
# Por debajo del umbral el dato se marca low_confidence y no cuenta como completo.
UMBRAL_CONFIANZA = 0.6

# --- Colchón de emergencia (meses de gastos fijos) según estabilidad de ingresos ---
MESES_COLCHON = {"stable": 6, "variable": 9}
MESES_COLCHON_DEFECTO = 6

# --- Perfil de riesgo: manda el tope más restrictivo de los disponibles ---
# Escenario: 1 = vende todo ante una caída pequeña ... 5 = compraría más.
TOPE_POR_ESCENARIO = {1: P.CONSERVADOR, 2: P.MODERADO, 3: P.DINAMICO, 4: P.AGRESIVO, 5: P.MUY_AGRESIVO}

# (límite superior exclusivo, perfil). El último tramo aplica a todo lo demás.
TRAMOS_CAIDA_ACEPTADA_PCT = ((5, P.CONSERVADOR), (10, P.MODERADO), (20, P.DINAMICO), (30, P.AGRESIVO))
TRAMOS_PLAZO_ANIOS = ((2, P.CONSERVADOR), (4, P.MODERADO), (7, P.DINAMICO), (10, P.AGRESIVO))
# Capacidad de pérdida / importe a invertir en el objetivo principal.
TRAMOS_CAPACIDAD_RATIO = ((0.05, P.CONSERVADOR), (0.15, P.MODERADO), (0.30, P.DINAMICO), (0.50, P.AGRESIVO))

# --- Equivalencias con MyInvestor (pendiente: leer valores reales con list_facets) ---
SRI_MAX_POR_PERFIL = {P.CONSERVADOR: 3, P.MODERADO: 4, P.DINAMICO: 5, P.AGRESIVO: 6, P.MUY_AGRESIVO: 7}
RISK_MAX_CARTERAS_POR_PERFIL = {P.CONSERVADOR: 1, P.MODERADO: 2, P.DINAMICO: 3, P.AGRESIVO: 4, P.MUY_AGRESIVO: 5}

# --- Conveniencia: nivel de conocimiento mínimo por familia de producto ---
NIVEL_MINIMO_POR_FAMILIA = {
    "deposits_money_market": "basic",
    "fixed_income_funds": "basic",
    "mixed_funds": "medium",
    "equity_funds": "medium",
    "etfs": "medium",
    "stocks": "medium",
    "complex_products": "high",
}
# Con un nivel por debajo del mínimo, basta esta experiencia (operaciones en 3 años) para ser conveniente.
OPERACIONES_COMPENSAN_UN_NIVEL = 5

# --- Liquidez y plazo como filtros posteriores sobre la ficha del fondo ---
DIAS_REEMBOLSO_MAX = {"high": 3, "medium": 7}  # "low" no filtra
# Necesidad de liquidez deducida del plazo si el cliente no la dijo: (plazo exclusivo, necesidad).
TRAMOS_LIQUIDEZ_POR_PLAZO = ((2, "high"), (5, "medium"))
# Valores de `fixed_income_term` en la ficha. "Corto plazo" está verificado (docs/proyecto/05);
# "Medio plazo" NO está verificado.
PLAZOS_RENTA_FIJA_POR_HORIZONTE = ((2, ["Corto plazo"]), (5, ["Corto plazo", "Medio plazo"]))

DIVISA_POR_DEFECTO = "EUR"  # cliente residente en España sin preferencia de divisa
DIAS_HASTA_REVISION = 365   # próxima revisión periódica tras validar
