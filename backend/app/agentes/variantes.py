"""Generador de clientes simulados para el laboratorio (B1/B2).

Crea personas variadas a partir de una semilla: edad, ingresos estables o variables, gastos, ahorro,
deudas, objetivo y plazo, lo que sabe de verdad de renta variable y renta fija (o lo que cree saber),
reacción ante una caída, sostenibilidad, forma de hablar y, a veces, un cliente que no acepta la
grabación. De cada una salen la ficha que interpreta el cliente simulado y lo que el perfil debe (y no
debe) tener al final. Misma semilla, mismas personas: los resultados se pueden repetir y comparar.

Todo es inventado (DATOS SIMULADOS). Las cifras son redondas a propósito: se comprueba que el sistema
las recoge, no que adivine.
"""

from __future__ import annotations

import random

from . import evaluacion
from .laboratorio import Persona

NOMBRES = ["Ana", "Luis", "Marta", "Pedro", "Rosa", "Jorge", "Elena", "Antonio", "Pilar", "Sergio",
           "Nuria", "Manuel", "Inés", "Raúl", "Teresa", "Diego", "Lola", "Andrés", "Sara", "Íñigo"]
# En forma neutra («trabaja en…»): el nombre no dice nada del género de la persona simulada.
PROFESIONES = ["trabaja en un colegio", "trabaja en hostelería", "trabaja en un hospital", "trabaja en una oficina",
               "trabaja en la construcción", "trabaja en un despacho de abogados", "trabaja en una tienda",
               "trabaja en una empresa de software", "trabaja en una farmacia", "trabaja en el transporte",
               "trabaja en el campo", "trabaja en un estudio de arquitectura"]
RASGOS = [
    "Habla poco: contesta con frases muy cortas.",
    "Es muy hablador: se va por las ramas y cuenta anécdotas antes de contestar.",
    "Está nervioso con el tema del dinero y pide que le repitan las cosas.",
    "Desconfía: pregunta para qué quieren saber cada cosa antes de contestar.",
    "Es bromista y contesta con humor, pero acaba dando los datos.",
    "Va con prisa y pide ir al grano.",
]
REACCIONES = {
    1: "lo vendería todo para no perder más",
    2: "vendería una parte, por si acaso",
    3: "no haría nada y esperaría a que se recupere",
    4: "aprovecharía para invertir un poco más",
}
SOSTENIBILIDAD = {
    "none": "La sostenibilidad no le importa.",
    "some": "La sostenibilidad le importa algo, pero no es lo principal.",
    "strong": "La sostenibilidad le importa mucho: no quiere invertir en empresas contaminantes.",
}


def _redondo(x: float, paso: int) -> int:
    return int(round(x / paso) * paso)


def _euros(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def generar(n: int, semilla: int = 1) -> list[Persona]:
    azar = random.Random(semilla)
    return [_persona(azar, i + 1) for i in range(n)]


def _persona(azar: random.Random, numero: int) -> Persona:
    nombre = azar.choice(NOMBRES)
    edad = azar.randint(24, 76)
    jubilado = edad >= 66
    ocupacion = "cobra una pensión de jubilación" if jubilado else azar.choice(PROFESIONES)
    rasgo = azar.choice(RASGOS)
    lineas = [f"{nombre}, {edad} años, {ocupacion}."]
    esperado: dict[str, object] = {"disclosures.ai_notice_ack": True}
    prohibido: list[str] = []
    prohibido_valores: dict[str, list] = {}
    alertas: list[str] = []

    if azar.random() < 0.1:
        lineas.append("- NO acepta que se grabe la conversación ni quiere seguir: lo dice educadamente al principio y se despide.")
        caso = evaluacion.Caso(
            nombre=f"v{numero:03d}-{nombre.lower()}-no-acepta", que_prueba="No acepta la grabación: no debe seguir ni apuntar nada.",
            turnos=[], esperado={},
            prohibido=["financial.net_monthly_income_eur", "financial.liquid_savings_eur", "objectives.o1.goal",
                       "risk_tolerance.scenario_score"],
        )
        return Persona(caso=caso, ficha="\n".join(lineas))

    lineas[0] += f" {rasgo}"
    lineas.append("- Acepta que se grabe la conversación.")

    # Objetivo, plazo y liquidez.
    if jubilado:
        objetivo, plazo, liquidez = "complementar la pensión", azar.choice([5, 10]), "low"
    else:
        objetivo, plazo, liquidez = azar.choice([
            ("ahorrar para la jubilación", max(5, 67 - edad), "low"),
            ("la entrada de un piso", azar.choice([2, 3]), "high"),
            ("los estudios de sus hijos", azar.choice([8, 12]), "medium"),
            ("hacer crecer sus ahorros", azar.choice([5, 7]), "medium"),
        ])
    frase_liquidez = {"low": "No necesitará ese dinero antes.",
                      "medium": "Quizá necesite una parte antes, no lo sabe.",
                      "high": "Puede que lo necesite antes de tiempo."}[liquidez]
    lineas.append(f"- Quiere invertir para {objetivo}, durante unos {plazo} años. {frase_liquidez}")
    esperado.update({"objectives.o1.goal": {"presente": True}, "objectives.o1.horizon_years": plazo})

    # Situación financiera.
    ingresos = _redondo(azar.uniform(900, 5000), 50)
    if not jubilado and azar.random() < 0.3:
        bajo, alto = _redondo(ingresos * 0.5, 100), _redondo(ingresos * 1.3, 100)
        lineas.append(f"- Sus ingresos varían: hay meses de {_euros(bajo)} euros y meses de {_euros(alto)}.")
        esperado["financial.income_stability"] = "variable"
        ingresos = (bajo + alto) // 2
    else:
        fuente = "de pensión" if jubilado else "netos"
        lineas.append(f"- Cobra {_euros(ingresos)} euros {fuente} al mes, estables.")
        esperado["financial.net_monthly_income_eur"] = ingresos
        esperado["financial.income_stability"] = "stable"
    gastos = _redondo(ingresos * azar.uniform(0.4, 0.75), 50)
    ahorro = _redondo(azar.uniform(3000, 150000), 1000)
    lineas.append(f"- Gastos fijos: unos {_euros(gastos)} euros al mes.")
    lineas.append(f"- Ahorro disponible: {_euros(ahorro)} euros.")
    esperado.update({"financial.fixed_monthly_costs_eur": gastos, "financial.liquid_savings_eur": ahorro})
    if azar.random() < 0.4:
        deuda = _redondo(azar.uniform(3000, 180000), 1000)
        lineas.append(f"- Debe {_euros(deuda)} euros ({'de hipoteca' if deuda > 50000 else 'de un préstamo'}).")
        esperado["financial.debts_eur"] = deuda
    else:
        lineas.append("- No tiene deudas.")
        esperado["financial.debts_eur"] = 0

    # Conocimientos: lo que sabe de verdad, no lo que dice.
    rv = azar.choice(["sabe", "se_equivoca", "no_sabe"])
    if rv == "sabe":
        lineas.append("- Entiende bien los fondos de renta variable: sabe que pueden bajar mucho aunque los venda un banco. "
                      "Ha invertido en ellos en los últimos tres años.")
        esperado["knowledge.equity_funds"] = {"uno_de": ["medium", "high"], "fuente": "demonstrated"}
    elif rv == "se_equivoca":
        lineas.append("- Dice que conoce bien los fondos de renta variable, pero cree que si se mantienen el tiempo suficiente "
                      "no se puede perder dinero, o que un fondo de su banco no puede bajar. Defiende esa idea.")
        esperado["knowledge.equity_funds"] = {"valor": "none", "fuente": "demonstrated"}
        alertas.append("knowledge.equity_funds")
    else:
        lineas.append("- No sabe qué es un fondo de renta variable y lo reconoce.")
        prohibido_valores["knowledge.equity_funds"] = ["medium", "high"]
    if azar.random() < 0.5:
        lineas.append("- Sabe que si suben los tipos de interés, los fondos de renta fija bajan de precio.")
        esperado["knowledge.fixed_income_funds"] = {"uno_de": ["basic", "medium", "high"]}
    else:
        lineas.append("- No sabe cómo funcionan los fondos de renta fija.")
        prohibido_valores["knowledge.fixed_income_funds"] = ["medium", "high"]
    lineas.append("- Nunca ha usado productos complejos (derivados, estructurados) ni sabe qué son.")
    prohibido_valores["knowledge.complex_products"] = ["medium", "high"]

    # Riesgo y sostenibilidad.
    puntuacion = azar.choice(list(REACCIONES))
    caida = azar.choice([15, 20, 25])
    lineas.append(f"- Si sus inversiones bajaran un {caida} % en unos meses, {REACCIONES[puntuacion]}.")
    esperado["risk_tolerance.scenario_score"] = puntuacion
    sost = azar.choice(list(SOSTENIBILIDAD))
    lineas.append(f"- {SOSTENIBILIDAD[sost]}")
    esperado["sustainability.preference"] = sost

    if azar.random() < 0.3:
        lineas.append("- Si sale el tema, menciona lo que gana su pareja, pero sus finanzas son separadas.")

    caso = evaluacion.Caso(
        nombre=f"v{numero:03d}-{nombre.lower()}-{edad}", que_prueba=f"Variante generada ({rv.replace('_', ' ')} de renta variable).",
        turnos=[], esperado=esperado, prohibido=prohibido, prohibido_valores=prohibido_valores,
    )
    return Persona(caso=caso, ficha="\n".join(lineas), alertas=alertas)
