"""Evaluación del extractor con entrevistas de casos difíciles (B1).

Cada caso (`fixtures/evaluacion/*.json`) es una entrevista simulada con lo que el perfil DEBE tener al
final (`esperado`) y lo que NO debe tener (`prohibido`, `prohibido_valores`): datos de terceros, evasivas,
lo que el cliente pide que se anote sin demostrarlo…

`esperado` admite, por ruta:
- un valor: tiene que coincidir (números con tolerancia de 1 céntimo, textos sin mayúsculas);
- `{"presente": true}`: basta con que exista (textos libres como el objetivo o la profesión);
- `{"valor": v}` o `{"uno_de": [v1, v2]}`, con `"fuente"` y `"flags"` opcionales que también se exigen.

Métricas (las mismas para el pitch y para afinar el prompt):
- cobertura = aciertos / esperados: cuánto de lo que dijo el cliente acaba en el perfil;
- precisión = aciertos / (aciertos + valores erróneos + prohibidos escritos): cuánto de lo escrito es fiable.
Un prohibido escrito es el fallo más grave: es un dato que el cliente no dio.

Este módulo solo puntúa; ejecutar las entrevistas con Claude es cosa de `scripts/evaluar_extractor.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..perfil.modelos import CALCULADOS, CAMPOS, Fact, Turno
from ..perfil.validacion import normalizar

CARPETA = Path(__file__).resolve().parents[2] / "fixtures" / "evaluacion"


@dataclass
class Caso:
    nombre: str
    que_prueba: str
    turnos: list[Turno]
    esperado: dict[str, object]
    prohibido: list[str] = field(default_factory=list)
    prohibido_valores: dict[str, list] = field(default_factory=dict)


@dataclass
class Linea:
    ruta: str
    estado: str  # ok | mal | falta | prohibido
    esperado: object
    obtenido: object
    detalle: str = ""


@dataclass
class Resultado:
    caso: str
    lineas: list[Linea]
    rechazos: list[str] = field(default_factory=list)

    def cuenta(self, estado: str) -> int:
        return sum(1 for li in self.lineas if li.estado == estado)

    @property
    def esperados(self) -> int:
        return sum(1 for li in self.lineas if li.estado != "prohibido")


def cargar(ruta: Path) -> Caso:
    d = json.loads(ruta.read_text("utf-8"))
    return Caso(
        nombre=d.get("nombre", ruta.stem), que_prueba=d.get("que_prueba", ""),
        turnos=[Turno(**t) for t in d["turns"]], esperado=d.get("esperado", {}),
        prohibido=d.get("prohibido", []), prohibido_valores=d.get("prohibido_valores", {}),
    )


def casos(carpeta: Path = CARPETA) -> list[Caso]:
    return [cargar(p) for p in sorted(carpeta.glob("*.json"))]


def comprobar_caso(caso: Caso, con_turnos: bool = True) -> list[str]:
    """Errores de forma del propio caso (rutas, valores, turnos); [] si está bien.

    `con_turnos=False` para las personas del laboratorio, que no traen conversación escrita."""
    errores = []
    ids = [t.turn_id for t in caso.turnos]
    if len(ids) != len(set(ids)):
        errores.append("turn_id repetidos")
    if con_turnos and not any(t.speaker == "client" for t in caso.turnos):
        errores.append("sin turnos del cliente")
    rutas = list(caso.esperado) + list(caso.prohibido) + list(caso.prohibido_valores)
    for ruta in rutas:
        if ruta not in CAMPOS:
            errores.append(f"ruta desconocida: {ruta}")
        elif ruta in CALCULADOS:
            errores.append(f"ruta calculada: {ruta}")
    for ruta in set(caso.esperado) & (set(caso.prohibido) | set(caso.prohibido_valores)):
        errores.append(f"{ruta} es esperado y prohibido a la vez")
    for ruta, regla in caso.esperado.items():
        if ruta not in CAMPOS or ruta in CALCULADOS:
            continue
        valores = _valores_aceptados(regla)
        for v in valores or []:
            try:
                normalizar(ruta, v)
            except ValueError as e:
                errores.append(f"{ruta}: valor esperado no válido ({e})")
    return errores


def _valores_aceptados(regla) -> list | None:
    """None = basta con que exista."""
    if isinstance(regla, dict):
        if regla.get("presente"):
            return None
        if "uno_de" in regla:
            return list(regla["uno_de"])
        return [regla.get("valor")]
    return [regla]


def _igual(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.01
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().casefold() == b.strip().casefold()
    return a == b


def puntuar(caso: Caso, mifid: dict[str, Fact]) -> Resultado:
    lineas: list[Linea] = []
    for ruta, regla in caso.esperado.items():
        f = mifid.get(ruta)
        if f is None:
            lineas.append(Linea(ruta, "falta", regla, None))
            continue
        aceptados = _valores_aceptados(regla)
        problemas = []
        if aceptados is not None and not any(_igual(f.value, v) for v in aceptados):
            problemas.append("valor")
        if isinstance(regla, dict):
            if regla.get("fuente") and f.source.value != regla["fuente"]:
                problemas.append(f"fuente {f.source.value}")
            faltan = set(regla.get("flags", [])) - {fl.value for fl in f.flags}
            if faltan:
                problemas.append(f"sin flags {sorted(faltan)}")
        lineas.append(Linea(ruta, "mal" if problemas else "ok", regla, f.value, ", ".join(problemas)))
    for ruta in caso.prohibido:
        f = mifid.get(ruta)
        if f is not None:
            lineas.append(Linea(ruta, "prohibido", None, f.value, "el cliente no lo dio"))
    for ruta, malos in caso.prohibido_valores.items():
        f = mifid.get(ruta)
        if f is not None and any(_igual(f.value, v) for v in malos):
            lineas.append(Linea(ruta, "prohibido", f"no {malos}", f.value, "valor no demostrado"))
    return Resultado(caso.nombre, lineas)


def resumen(resultados: list[Resultado]) -> dict[str, float]:
    ok = sum(r.cuenta("ok") for r in resultados)
    mal = sum(r.cuenta("mal") for r in resultados)
    prohibidos = sum(r.cuenta("prohibido") for r in resultados)
    esperados = sum(r.esperados for r in resultados)
    escritos = ok + mal + prohibidos
    return {
        "aciertos": ok, "esperados": esperados, "erroneos": mal, "prohibidos": prohibidos,
        "cobertura": ok / esperados if esperados else 1.0,
        "precision": ok / escritos if escritos else 1.0,
    }
