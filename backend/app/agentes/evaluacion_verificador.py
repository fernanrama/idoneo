"""Evaluación del verificador (B2) con tramos de entrevista de casos difíciles.

Cada caso (`fixtures/verificacion/casos.json`) trae el perfil que ya tenía el cliente, los turnos
recientes y las alertas que deben salir (`esperadas`: un flag y las rutas que se aceptan; `null` es
una alerta sin dato concreto). Con `ninguna_mas`, cualquier otra alerta cuenta como falsa alarma.

Métricas (las mismas para el pitch y para afinar el prompt):
- detección = alertas esperadas que salen / alertas esperadas;
- falsas alarmas = alertas que salen en un caso con `ninguna_mas` sin estar esperadas.

Este módulo solo carga y puntúa; ejecutar el verificador con Claude es cosa de
`scripts/evaluar_verificador.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..perfil.modelos import Alerta, Evidencia, Fact, Flag, Fuente, Perfil, Turno

FICHERO = Path(__file__).resolve().parents[2] / "fixtures" / "verificacion" / "casos.json"
SESION = "eval-verificador"


@dataclass
class Esperada:
    flag: Flag
    rutas: list[str | None]


@dataclass
class Caso:
    nombre: str
    que_prueba: str
    perfil: Perfil
    turnos: list[Turno]
    esperadas: list[Esperada]
    ninguna_mas: bool


@dataclass
class Resultado:
    caso: str
    detectadas: list[Esperada] = field(default_factory=list)
    perdidas: list[Esperada] = field(default_factory=list)
    falsas: list[Alerta] = field(default_factory=list)
    obtenidas: list[Alerta] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.perdidas and not self.falsas


def _perfil(nombre: str, datos: dict[str, dict], turnos: list[Turno]) -> Perfil:
    tiempos = {t.turn_id: (t.t_start, t.t_end) for t in turnos}
    mifid = {
        ruta: Fact(value=d["valor"], source=Fuente(d.get("fuente", "declared")), confidence=0.9,
                   evidence=[Evidencia(session_id=SESION, turn_id=d["turn_id"], t=tiempos.get(d["turn_id"], (0, 0)),
                                       quote=d["cita"])],
                   updated_by="fixture")
        for ruta, d in datos.items()
    }
    return Perfil(client_id=f"eval-{nombre}", mifid=mifid, reason="DATOS SIMULADOS")


def casos(fichero: Path = FICHERO) -> list[Caso]:
    d = json.loads(fichero.read_text("utf-8"))
    salida = []
    for c in d["casos"]:
        turnos = [Turno(**t) for t in c["turns"]]
        salida.append(Caso(
            nombre=c["nombre"], que_prueba=c.get("que_prueba", ""), perfil=_perfil(c["nombre"], c["perfil"], turnos),
            turnos=turnos, esperadas=[Esperada(Flag(e["flag"]), e["rutas"]) for e in c["esperadas"]],
            ninguna_mas=bool(c.get("ninguna_mas")),
        ))
    return salida


def puntuar(caso: Caso, alertas: list[Alerta]) -> Resultado:
    r = Resultado(caso=caso.nombre, obtenidas=list(alertas))
    usadas: set[int] = set()
    for e in caso.esperadas:
        i = next((i for i, a in enumerate(alertas) if i not in usadas and a.flag == e.flag and a.path in e.rutas), None)
        if i is None:
            r.perdidas.append(e)
        else:
            usadas.add(i)
            r.detectadas.append(e)
    if caso.ninguna_mas:
        r.falsas = [a for i, a in enumerate(alertas) if i not in usadas]
    return r


def resumen(resultados: list[Resultado]) -> dict[str, float]:
    esperadas = sum(len(r.detectadas) + len(r.perdidas) for r in resultados)
    detectadas = sum(len(r.detectadas) for r in resultados)
    return {
        "casos": len(resultados),
        "casos_ok": sum(1 for r in resultados if r.ok),
        "esperadas": esperadas,
        "detectadas": detectadas,
        "deteccion": detectadas / esperadas if esperadas else 1.0,
        "falsas_alarmas": sum(len(r.falsas) for r in resultados),
    }
