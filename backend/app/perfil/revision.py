"""Microentrevista de revisión: el cliente cuenta qué ha cambiado y se le pregunta solo lo necesario.

Diseño: docs/diseno/06-actualizacion-continua.md (§3.2, §3.3 y §4.2). Sin tabla nueva ni migración:
- Abrir una revisión escribe una versión con motivo `review_requested:<motivos>` (historial inmutable).
- La revisión en curso se reconstruye leyendo el historial hacia atrás hasta la última validación.
- Qué preguntar lo decide `alcance.planificar` (determinista). Una pregunta está respondida cuando su dato
  se ha vuelto a escribir después de abrir la revisión (cambio o confirmación con cita nueva).
- `cambios` compara el último perfil validado con el último guardado, para la vista de la entidad.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from . import alcance, store
from .alcance import Motivo, Peticion, TipoPregunta
from .modelos import CALCULADOS, EstadoPerfil, Perfil

PREFIJO = "review_requested:"

# Lo que el cliente puede elegir en «Ha cambiado algo», en el orden en que se muestra. DATOS DEL PRODUCTO.
MOTIVOS_CLIENTE: dict[Motivo, dict[str, str]] = {
    Motivo.income_change: {"titulo": "Me han subido o bajado el sueldo",
                           "detalle": "Cambia lo que entra cada mes", "icono": "sueldo"},
    Motivo.planned_expense: {"titulo": "Tengo un gasto importante a la vista",
                             "detalle": "Una reforma, un coche, unos estudios, un imprevisto", "icono": "gasto"},
    Motivo.windfall: {"titulo": "He recibido un dinero extra",
                      "detalle": "Una herencia, un premio, una venta", "icono": "extra"},
    Motivo.goal_change: {"titulo": "He cambiado de idea sobre la inversión",
                         "detalle": "Para qué, cuánto o durante cuánto tiempo", "icono": "idea"},
    Motivo.new_debt: {"titulo": "Tengo una hipoteca o un préstamo nuevo",
                      "detalle": "O he terminado de pagar uno", "icono": "casa"},
    Motivo.job_loss: {"titulo": "Me he quedado sin trabajo",
                      "detalle": "O mis ingresos ya no son seguros", "icono": "trabajo"},
    Motivo.dependants: {"titulo": "Tengo personas nuevas a mi cargo",
                        "detalle": "Un hijo, un familiar", "icono": "familia"},
    Motivo.retirement: {"titulo": "Me jubilo o ya me he jubilado",
                        "detalle": "Cambian ingresos y planes", "icono": "jubilacion"},
}

# Qué significa para la entidad cada efecto de `alcance.es_material`.
EFECTOS = {
    "suitability_complete": "Cambia si el perfil está completo",
    "risk_profile": "Cambia el perfil de riesgo",
    "risk_profile_jump": "El perfil de riesgo salta dos niveles o más",
    "esg_only": "Cambia el criterio de sostenibilidad",
    "loss_capacity": "La capacidad de soportar pérdidas varía más de un 20 %",
}
_FILTROS = {
    "redemption_lag_days": "Cambia el plazo máximo de reembolso (liquidez)",
    "fixed_income_term": "Cambia el filtro de renta fija a corto plazo (plazo)",
    "min_initial": "Cambia la inversión mínima admitida (importe)",
    "sustainability_article": "Cambia el artículo SFDR exigido",
    "top_sectors": "Cambian los sectores excluidos",
}


class Pregunta(BaseModel):
    path: str
    tipo: TipoPregunta
    valor_vigente: Any = None
    respondida: bool = False


class RevisionEnCurso(BaseModel):
    motivos: list[Motivo]
    abierta_en: datetime
    desde_version: int
    preguntas: list[Pregunta]
    aplazadas: list[str]
    reevaluacion_completa: bool
    razones: list[str]

    @property
    def pendientes(self) -> list[Pregunta]:
        return [q for q in self.preguntas if not q.respondida]


class Cambio(BaseModel):
    path: str
    antes: Any = None
    ahora: Any = None
    fuente: str | None = None
    cita: str | None = None


class Comparacion(BaseModel):
    desde_version: int
    hasta_version: int
    cambios: list[Cambio]
    efectos: list[str]
    perfil_antes: str | None
    perfil_ahora: str | None
    sri_antes: int | None
    sri_ahora: int | None


def opciones() -> list[dict[str, str]]:
    return [{"code": m.value, **datos} for m, datos in MOTIVOS_CLIENTE.items()]


def _motivos(codigos: list[str]) -> list[Motivo]:
    validos = {m.value: m for m in MOTIVOS_CLIENTE}
    out: list[Motivo] = []
    for c in codigos:
        if c not in validos:
            raise store.DatoInvalido(f"Motivo de revisión no válido: {c!r}")
        if validos[c] not in out:
            out.append(validos[c])
    if not out:
        raise store.DatoInvalido("Elige al menos un motivo")
    return out


def previsualizar(client_id: str, codigos: list[str]) -> RevisionEnCurso:
    """Qué se preguntaría, sin escribir nada."""
    motivos = _motivos(codigos)
    p = store.perfil(client_id)
    return _construir(p, motivos, p.created_at, p.version + 1)


def abrir(client_id: str, codigos: list[str]) -> RevisionEnCurso:
    """Abre (o amplía) una revisión. Solo sobre un perfil ya completo: si no, se termina la entrevista."""
    motivos = _motivos(codigos)
    p = store.perfil(client_id)
    if not p.assessments.suitability.complete:
        raise store.Conflicto("Primero termina la entrevista: aún faltan datos de tu perfil")
    previos = en_curso(client_id)
    todos = list(dict.fromkeys((previos.motivos if previos else []) + motivos))
    store.pedir_revision(client_id, PREFIJO + ",".join(m.value for m in todos))
    actual = en_curso(client_id)
    assert actual is not None
    return actual


def _peticiones(reason: str) -> list[Motivo]:
    out = []
    for c in reason[len(PREFIJO):].split(","):
        try:
            out.append(Motivo(c))
        except ValueError:
            continue
    return out


def en_curso(client_id: str) -> RevisionEnCurso | None:
    """La revisión abierta desde la última validación (o None). Se reconstruye del historial."""
    historial = store.versiones(client_id)
    motivos: list[Motivo] = []
    abierta: dict | None = None
    for v in reversed(historial):
        if v["reason"] == "validated" or v["reason"].startswith("demo_reset"):
            break
        if v["reason"].startswith(PREFIJO):
            abierta = v  # la más antigua de esta revisión: desde ahí cuentan las respuestas
            motivos = list(dict.fromkeys(_peticiones(v["reason"]) + motivos))
    if abierta is None or not motivos:
        return None
    return _construir(store.perfil(client_id), motivos, abierta["created_at"], abierta["version"])


def _construir(p: Perfil, motivos: list[Motivo], abierta_en: datetime, desde: int) -> RevisionEnCurso:
    a = alcance.planificar(p, [Peticion(motivo=m) for m in motivos])
    preguntas = []
    for q in a.preguntas:
        f = p.mifid.get(q.path)
        hecha = f is not None and f.updated_at >= abierta_en and f.evidence != []
        preguntas.append(Pregunta(path=q.path, tipo=q.tipo, valor_vigente=q.valor_vigente, respondida=hecha))
    return RevisionEnCurso(motivos=motivos, abierta_en=abierta_en, desde_version=desde, preguntas=preguntas,
                           aplazadas=a.aplazadas, reevaluacion_completa=a.reevaluacion_completa, razones=a.razones)


def vista(r: RevisionEnCurso | None) -> dict[str, Any]:
    if r is None:
        return {"open": False}
    return {
        "open": True,
        "reasons": [{"code": m.value, **MOTIVOS_CLIENTE.get(m, {"titulo": m.value})} for m in r.motivos],
        "opened_at": r.abierta_en.isoformat(),
        "since_version": r.desde_version,
        "questions": [q.model_dump(mode="json") for q in r.preguntas],
        "remaining": len(r.pendientes),
        "deferred": r.aplazadas,
        "full_reassessment": r.reevaluacion_completa,
        "full_reassessment_reasons": r.razones,
    }


# ---------- antes y después, para la entidad ----------

def _ultima_validada(client_id: str) -> int | None:
    validadas = [v["version"] for v in store.versiones(client_id) if v["status"] == EstadoPerfil.active]
    return validadas[-1] if validadas else None


def comparar(client_id: str) -> Comparacion | None:
    """Último perfil validado frente al último guardado. None si no hay nada posterior que comparar."""
    desde = _ultima_validada(client_id)
    ultima = store.perfil(client_id)
    if desde is None or ultima.version <= desde:
        return None
    antes = store.perfil(client_id, desde)
    cambios = []
    for ruta in sorted(set(antes.mifid) | set(ultima.mifid), key=lambda r: alcance.ORDEN_GUION.get(r, 999)):
        if ruta in CALCULADOS:
            continue
        fa, fn = antes.mifid.get(ruta), ultima.mifid.get(ruta)
        va, vn = (fa.value if fa else None), (fn.value if fn else None)
        confirmado = fn is not None and fa is not None and va == vn and fn.updated_at > fa.updated_at
        if va == vn and not confirmado:
            continue
        cita = fn.evidence[0].quote if fn and fn.evidence else None
        cambios.append(Cambio(path=ruta, antes=va, ahora=vn, fuente=fn.source.value if fn else None, cita=cita))
    efectos = []
    for e in alcance.es_material(antes, ultima):
        if e.startswith("appropriateness:"):
            efectos.append(f"Cambia la conveniencia de {e.split(':', 1)[1]}")
        elif e.startswith("filter:"):
            efectos.append(_FILTROS.get(e.split(":", 1)[1], f"Cambia el filtro {e.split(':', 1)[1]}"))
        else:
            efectos.append(EFECTOS.get(e, e))
    if not cambios and not efectos:
        return None  # solo versiones de trámite (p. ej. la apertura de la revisión)
    sa, sn = antes.assessments.suitability, ultima.assessments.suitability
    return Comparacion(
        desde_version=desde, hasta_version=ultima.version, cambios=cambios, efectos=efectos,
        perfil_antes=sa.risk_profile.value if sa.risk_profile else None,
        perfil_ahora=sn.risk_profile.value if sn.risk_profile else None,
        sri_antes=sa.max_sri, sri_ahora=sn.max_sri)
