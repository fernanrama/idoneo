"""La hipoteca de la vivienda no cuenta como deuda para la capacidad de pérdida (bloque A, punto 1)."""

from app.perfil import calculos
from app.perfil.modelos import CAMPOS, OBLIGATORIOS, Fact, Fuente, Perfil, PerfilRiesgo
from app.perfil.validacion import TIPOS


def _perfil(datos: dict) -> Perfil:
    p = Perfil(client_id="test-hipoteca")
    for ruta, v in datos.items():
        p.mifid[ruta] = Fact(value=v, source=Fuente.declared, updated_by="fixture")
    calculos.recalcular(p)
    return p


def test_campo_hipoteca_en_catalogo_y_opcional():
    assert "financial.mortgage_eur" in CAMPOS and TIPOS["financial.mortgage_eur"][0] == "eur"
    assert "financial.mortgage_eur" not in OBLIGATORIOS


def test_hipoteca_no_resta_capacidad():
    # Javier: 40.000 € de ahorro, 1.500 € de gastos (cuota incluida), 120.000 € de hipoteca.
    p = _perfil({"financial.liquid_savings_eur": 40000, "financial.fixed_monthly_costs_eur": 1500,
                 "financial.debts_eur": 0, "financial.mortgage_eur": 120000})
    assert calculos.valor(p, "financial.loss_capacity_eur") == 31000
    assert "financial.mortgage_eur" not in p.mifid["financial.loss_capacity_eur"].inputs
    # 31.000 / 40.000 = 0,775 → MUY_AGRESIVO por capacidad (luego manda el más restrictivo).
    assert calculos._por_capacidad(31000, 40000) == PerfilRiesgo.MUY_AGRESIVO


def test_otras_deudas_si_restan():
    p = _perfil({"financial.liquid_savings_eur": 40000, "financial.fixed_monthly_costs_eur": 1500,
                 "financial.debts_eur": 15000})
    assert calculos.valor(p, "financial.loss_capacity_eur") == 16000
