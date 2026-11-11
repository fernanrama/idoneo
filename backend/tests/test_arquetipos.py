"""Perfiles de clientes tipo, calculados a mano (bloque A, punto 5). DATOS SIMULADOS.

Cada caso lleva la cuenta en el comentario. Reglas v1 (calculos.py):
- capacidad = max(0, ahorro − 6 × gastos − deudas sin hipoteca); ratio = capacidad / ahorro:
  ≤0 CONSERVADOR, <0,25 MODERADO, <0,5 DINAMICO, <0,75 AGRESIVO, resto MUY_AGRESIVO.
- plazo: <2 CONSERVADOR, <5 MODERADO, <8 DINAMICO, <12 AGRESIVO, resto MUY_AGRESIVO.
- tolerancia 1–5 → CONSERVADOR … MUY_AGRESIVO.
- importe > capacidad → CONSERVADOR. Manda el más restrictivo. SRI máximo: 3, 4, 5, 6, 7.
"""

import pytest

from app.perfil import calculos
from app.perfil.modelos import Fact, Fuente, Perfil, PerfilRiesgo

C, M, D, A, MA = (PerfilRiesgo.CONSERVADOR, PerfilRiesgo.MODERADO, PerfilRiesgo.DINAMICO,
                  PerfilRiesgo.AGRESIVO, PerfilRiesgo.MUY_AGRESIVO)

# nombre, ahorro, gastos/mes, deudas, hipoteca, importe, plazo, tolerancia, capacidad esperada, perfil
CASOS = [
    # 8.000 − 5.400 = 2.600 (0,33 → D); plazo 30 → MA; tolerancia 4 → A. Manda D.
    ("joven-poco-ahorro", 8000, 900, 0, 0, 2000, 30, 4, 2600, D),
    # Igual, pero quiere invertir los 8.000: 8.000 > 2.600 → C.
    ("joven-lo-invierte-todo", 8000, 900, 0, 0, 8000, 30, 4, 2600, C),
    # 40.000 − 9.000 = 31.000 (0,78 → MA); la hipoteca de 120.000 no resta. Plazo 25, tolerancia 5.
    ("hipoteca-javier", 40000, 1500, 0, 120000, 20000, 25, 5, 31000, MA),
    # 95.000 − 8.400 = 86.600 (0,91 → MA); plazo 3 → M; tolerancia 2 → M. Manda M.
    ("jubilada-plazo-corto", 95000, 1400, 0, 0, 20000, 3, 2, 86600, M),
    # 12.000 − 12.000 = 0 → C. Su colchón es justo el ahorro.
    ("autonomo-colchon-justo", 12000, 2000, 0, 0, 5000, 10, 4, 0, C),
    # 30.000 − 6.000 − 12.000 (coche) = 12.000 (0,4 → D); plazo 10 → A; tolerancia 5. Manda D.
    ("prestamo-coche", 30000, 1000, 12000, 0, 10000, 10, 5, 12000, D),
    # 50.000 − 6.000 = 44.000 (0,88 → MA); plazo 1 → C. Manda C.
    ("entrada-piso-en-un-anio", 50000, 1000, 0, 0, 40000, 1, 3, 44000, C),
    # 500.000 − 18.000 = 482.000 (0,96 → MA); plazo 15 → MA; tolerancia 1 → C. Manda C.
    ("rico-que-vende-en-caidas", 500000, 3000, 0, 0, 100000, 15, 1, 482000, C),
    # 40.000 − 30.000 = 10.000 (0,25 justo → D); plazo 8 justo → A; tolerancia 4 → A. Manda D.
    ("fronteras-exactas", 40000, 5000, 0, 0, 5000, 8, 4, 10000, D),
    # 10.000 − 3.000 − 20.000 < 0 → 0 → C.
    ("deudas-mayores-que-ahorro", 10000, 500, 20000, 0, 1000, 20, 5, 0, C),
    # 60.000 − 12.000 = 48.000 (0,8 → MA); plazo 6 → D; tolerancia 3 → D. Manda D.
    ("familia-a-medio-plazo", 60000, 2000, 0, 150000, 30000, 6, 3, 48000, D),
]


def _perfil(ahorro, gastos, deudas, hipoteca, importe, plazo, tolerancia) -> Perfil:
    datos = {"financial.liquid_savings_eur": ahorro, "financial.fixed_monthly_costs_eur": gastos,
             "financial.debts_eur": deudas, "objectives.o1.amount_eur": importe,
             "objectives.o1.horizon_years": plazo, "risk_tolerance.scenario_score": tolerancia}
    if hipoteca:
        datos["financial.mortgage_eur"] = hipoteca
    p = Perfil(client_id="arquetipo")
    for ruta, v in datos.items():
        p.mifid[ruta] = Fact(value=v, source=Fuente.declared, updated_by="fixture")
    calculos.recalcular(p)
    return p


@pytest.mark.parametrize("nombre,ahorro,gastos,deudas,hipoteca,importe,plazo,tolerancia,capacidad,esperado",
                         CASOS, ids=[c[0] for c in CASOS])
def test_arquetipo(nombre, ahorro, gastos, deudas, hipoteca, importe, plazo, tolerancia, capacidad, esperado):
    p = _perfil(ahorro, gastos, deudas, hipoteca, importe, plazo, tolerancia)
    assert calculos.valor(p, "financial.loss_capacity_eur") == capacidad
    s = p.assessments.suitability
    assert s.risk_profile == esperado
    assert s.max_sri == {C: 3, M: 4, D: 5, A: 6, MA: 7}[esperado]
    assert calculos.restricciones(p).funds_query["max_risk"] == s.max_sri
