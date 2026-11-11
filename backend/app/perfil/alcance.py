"""Alcance de una revisión del perfil: qué preguntar en una microentrevista y por qué. Sin modelo.

Diseño: docs/diseno/06-actualizacion-continua.md (§3 y §4.2–4.4). Este módulo SOLO LEE el perfil:
no escribe versiones, no cambia estados y no toca las fórmulas de calculos.py, que reutiliza para
saber si un cambio mueve los resultados. Todavía no lo llama ninguna ruta ni ningún agente.

    vencimientos(perfil, hoy)      → peticiones por calendario: next_review, bloques caducados, plazo agotado
    planificar(perfil, peticiones) → Alcance: preguntas ordenadas, aplazadas y si hay que ampliar
    es_material(anterior, nueva)   → qué resultados o restricciones cambian entre dos versiones
    plazo_restante(fact, hoy)      → años que quedan de un plazo declarado

Todas las tablas son SUPUESTOS v1 del equipo, pendientes de revisión financiera y normativa.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from . import calculos
from .calculos import ORDEN_PERFILES, desconocimiento_declarado, valor
from .modelos import CALCULADOS, CAMPOS, FAMILIAS, EstadoAlerta, EstadoPerfil, Fact, Flag, Perfil
from .validacion import DatoInvalido

# ---------- supuestos v1 ----------

MAX_PREGUNTAS = 6          # [SUPUESTO] una microentrevista de 2–4 minutos
BLOQUES_AMPLIAR = 3        # [SUPUESTO] cambios en 3 bloques o más → reevaluación completa
SALTO_PERFIL_AMPLIAR = 2   # [SUPUESTO] el perfil de riesgo se mueve 2 niveles o más → material grave
VARIACION_CAPACIDAD = 0.20  # [SUPUESTO] variación relativa de la capacidad de pérdida que es material
DIAS_POR_ANIO = 365.25

# [SUPUESTO] Días tras los que un dato de cada bloque se da por caducado si no se ha vuelto a escribir.
CADUCIDAD_DIAS: dict[str, int] = {
    "financial": 365,
    "objectives": 365,
    "risk_tolerance": 730,
    "knowledge": 730,
    "experience": 730,
    "sustainability": 730,
}

ORDEN_GUION = {ruta: i for i, ruta in enumerate(CAMPOS)}  # el orden de CAMPOS es el del guion


# ---------- catálogo cerrado de motivos ----------

class Motivo(str, Enum):
    # calendario (los genera vencimientos)
    next_review_due = "next_review_due"
    stale_block = "stale_block"
    horizon_elapsed = "horizon_elapsed"
    # eventos vitales que cuenta el cliente
    retirement = "retirement"
    job_loss = "job_loss"
    windfall = "windfall"
    planned_expense = "planned_expense"
    income_change = "income_change"
    goal_change = "goal_change"
    new_debt = "new_debt"
    dependants = "dependants"
    # alertas de otros agentes
    knowledge_not_assessed = "knowledge_not_assessed"
    liquidity_change = "liquidity_change"
    amount_exceeds_objective = "amount_exceeds_objective"
    behaviour_vs_tolerance = "behaviour_vs_tolerance"
    new_product_family = "new_product_family"
    stale_profile = "stale_profile"
    # asesor o cliente
    advisor_request = "advisor_request"
    full_reassessment_requested = "full_reassessment_requested"
    # sesión de revisión: el dato ya cambió (está respondido); solo se confirman sus dependencias
    value_changed = "value_changed"


class TipoPregunta(str, Enum):
    confirmar = "confirmar"      # «¿Sigue siendo…?»: se lee el valor vigente
    repreguntar = "repreguntar"  # el dato cambió, falta o es dudoso
    comprobar = "comprobar"      # conocimiento: escenario de comprobación, no autoevaluación


_F, _O, _R = "financial.", "objectives.o1.", "risk_tolerance."
_REVISION_ANUAL = [f"{_F}net_monthly_income_eur", f"{_F}fixed_monthly_costs_eur", f"{_F}liquid_savings_eur",
                   f"{_F}debts_eur", f"{_O}horizon_years", f"{_O}liquidity_need"]

# Motivos con rutas fijas: (lo que hay que repreguntar, lo que basta con confirmar).
SEMILLAS: dict[Motivo, tuple[list[str], list[str]]] = {
    Motivo.stale_profile: ([], _REVISION_ANUAL),
    Motivo.horizon_elapsed: ([f"{_O}horizon_years"], []),
    Motivo.retirement: ([f"{_F}net_monthly_income_eur", f"{_F}income_stability"],
                        [f"{_O}goal", f"{_O}horizon_years"]),
    Motivo.job_loss: ([f"{_F}net_monthly_income_eur", f"{_F}income_stability", f"{_O}liquidity_need"],
                      [f"{_F}liquid_savings_eur"]),
    Motivo.windfall: ([f"{_F}liquid_savings_eur", f"{_F}other_assets_eur"], [f"{_O}goal", f"{_O}amount_eur"]),
    Motivo.planned_expense: ([f"{_O}liquidity_need"], [f"{_F}liquid_savings_eur"]),
    # Subida o bajada de sueldo: cambia lo que entra y quizá lo que gasta o ahorra.
    Motivo.income_change: ([f"{_F}net_monthly_income_eur", f"{_F}income_stability"],
                           [f"{_F}fixed_monthly_costs_eur"]),
    # Ha cambiado de idea: para qué, cuánto y durante cuánto tiempo.
    Motivo.goal_change: ([f"{_O}goal", f"{_O}amount_eur", f"{_O}horizon_years"], []),
    # Hipoteca o préstamo: la hipoteca de la vivienda va aparte y no resta capacidad, pero su cuota es gasto fijo.
    Motivo.new_debt: ([f"{_F}debts_eur", f"{_F}mortgage_eur", f"{_F}fixed_monthly_costs_eur"], []),
    Motivo.dependants: ([f"{_F}fixed_monthly_costs_eur"], [f"{_O}goal"]),
    Motivo.liquidity_change: ([f"{_O}liquidity_need"], [f"{_F}liquid_savings_eur"]),
    Motivo.amount_exceeds_objective: ([f"{_O}amount_eur"], [f"{_F}liquid_savings_eur"]),
    Motivo.behaviour_vs_tolerance: ([f"{_R}scenario_score", f"{_R}max_drawdown_accepted_pct",
                                     f"{_R}past_behaviour"], []),
    Motivo.full_reassessment_requested: ([], []),
}

# Motivos cuyas rutas las indica quien pide: prefijos admitidos y si se repreguntan o se confirman.
_CONOCIMIENTO = ("knowledge.", "experience.")
_TODO = tuple(sorted({r.split(".")[0] + "." for r in CAMPOS} - {"disclosures."}))
VARIABLES: dict[Motivo, tuple[tuple[str, ...], TipoPregunta]] = {
    Motivo.stale_block: (_TODO, TipoPregunta.confirmar),
    Motivo.knowledge_not_assessed: (_CONOCIMIENTO, TipoPregunta.repreguntar),
    Motivo.new_product_family: (_CONOCIMIENTO, TipoPregunta.repreguntar),
    Motivo.advisor_request: (_TODO, TipoPregunta.repreguntar),
    Motivo.value_changed: (_TODO, TipoPregunta.confirmar),  # ver planificar: no se pregunta la ruta
    Motivo.next_review_due: (_TODO, TipoPregunta.confirmar),  # vencimientos: solo lo no confirmado desde el vencimiento
}


def _dependencias() -> dict[str, list[str]]:
    """Si cambia la clave, hay que confirmar también los valores. Sale de calculos.py y de las reglas
    deterministas del verificador (agentes/verificador.reglas); unos tests lo vigilan. No añade fórmulas.

    Un solo nivel: las dependencias de una confirmación no se añaden (si no cambia, no arrastra nada).
    """
    d: dict[str, list[str]] = {
        # colchón y capacidad de pérdida → perfil por capacidad → SRI máximo
        f"{_F}liquid_savings_eur": [f"{_F}fixed_monthly_costs_eur", f"{_F}debts_eur"],
        f"{_F}fixed_monthly_costs_eur": [f"{_F}liquid_savings_eur", f"{_F}debts_eur",
                                          f"{_F}net_monthly_income_eur"],
        # ingresos: NO entran en ningún cálculo de riesgo; solo en la regla del verificador «gastos fijos
        # iguales o mayores que los ingresos» (alerta needs_advisor, que impide validar sin revisión)
        f"{_F}net_monthly_income_eur": [f"{_F}fixed_monthly_costs_eur"],
        f"{_F}debts_eur": [f"{_F}liquid_savings_eur", f"{_F}fixed_monthly_costs_eur"],
        # tolerancia por escenarios → perfil por tolerancia
        f"{_R}scenario_score": [f"{_R}max_drawdown_accepted_pct"],
        f"{_R}max_drawdown_accepted_pct": [f"{_R}scenario_score"],
        # plazo → perfil por plazo y renta fija a corto; liquidez → plazo de reembolso
        f"{_O}horizon_years": [f"{_O}liquidity_need"],
        f"{_O}liquidity_need": [f"{_O}horizon_years"],
        # importe → filtro de inversión mínima y, si supera la capacidad de pérdida, perfil CONSERVADOR
        f"{_O}amount_eur": [f"{_F}liquid_savings_eur", f"{_F}fixed_monthly_costs_eur", f"{_F}debts_eur"],
        # preferencias de sostenibilidad → esg_only y artículo SFDR
        "sustainability.preference": ["sustainability.min_sfdr_article"],
        "sustainability.min_sfdr_article": ["sustainability.preference"],
    }
    for fam in FAMILIAS:  # conveniencia: conocimiento o experiencia que lo compense
        conoce, opera = f"knowledge.{fam}", f"experience.{fam}.operations_last_3y"
        d[conoce], d[opera] = [opera], [conoce]
    return d


DEPENDENCIAS = _dependencias()


# ---------- tipos ----------

class Peticion(BaseModel):
    """Por qué hay que revisar. `rutas` solo para los motivos de VARIABLES."""

    motivo: Motivo
    rutas: list[str] = Field(default_factory=list)


class Pregunta(BaseModel):
    path: str
    tipo: TipoPregunta
    motivos: list[Motivo]
    valor_vigente: Any = None  # para confirmar: «¿Sigues teniendo unos 900 € de gastos fijos?»


class Alcance(BaseModel):
    preguntas: list[Pregunta]          # como mucho MAX_PREGUNTAS, primero lo que cambia
    aplazadas: list[str]               # quedan para otra microentrevista
    reevaluacion_completa: bool        # el llamante abre una entrevista completa; las preguntas, por dónde empezar
    razones: list[str]                 # por qué se amplía (vacío si no)
    # Sesión de revisión: tras las preguntas (o si no hay ninguna) se pregunta si ha cambiado algo más.
    # Así una revisión no termina nada más empezar por tener la lista vacía. False en la entrevista inicial.
    apertura: bool = False
    # Preguntas del alcance que el inversor ya contestó (dio o confirmó el dato) en esta revisión, con su tipo,
    # para mostrar el progreso. Orden del guion. No se vuelven a hacer.
    respondidas: list[Pregunta] = Field(default_factory=list)


# ---------- planificación ----------

def _comprobar_ruta(ruta: str) -> None:
    if ruta not in CAMPOS:
        raise DatoInvalido(f"Ruta desconocida: {ruta!r}")
    if ruta in CALCULADOS:
        raise DatoInvalido(f"{ruta} es un dato calculado: se revisan sus entradas, no el resultado")
    if ruta.startswith("disclosures."):
        raise DatoInvalido(f"{ruta} se recoge en cada sesión, no se revisa")


def _semillas(p: Peticion) -> tuple[list[str], list[str]]:
    if p.motivo in VARIABLES:
        prefijos, tipo = VARIABLES[p.motivo]
        if not p.rutas:
            raise DatoInvalido(f"El motivo {p.motivo.value} necesita rutas")
        for r in p.rutas:
            _comprobar_ruta(r)
            if not r.startswith(prefijos):
                raise DatoInvalido(f"El motivo {p.motivo.value} no admite la ruta {r}")
        return (list(p.rutas), []) if tipo == TipoPregunta.repreguntar else ([], list(p.rutas))
    if p.rutas:
        raise DatoInvalido(f"El motivo {p.motivo.value} tiene rutas fijas; no admite otras")
    return SEMILLAS[p.motivo]


def _tipo(perfil: Perfil, ruta: str, base: TipoPregunta) -> TipoPregunta:
    f = perfil.mifid.get(ruta)
    tipo = base
    if tipo == TipoPregunta.confirmar:
        if f is None or f.value is None or _dudoso(perfil, ruta):
            tipo = TipoPregunta.repreguntar  # no se confirma lo que falta o no es fiable
    if (tipo == TipoPregunta.repreguntar and ruta.startswith("knowledge.")
            and not desconocimiento_declarado(ruta, f)):
        tipo = TipoPregunta.comprobar  # «no lo conozco» no se comprueba
    return tipo


def _dado(perfil: Perfil, ruta: str) -> bool:
    """Tiene valor y no ha quedado dudoso: se puede dar por respondido."""
    f = perfil.mifid.get(ruta)
    return f is not None and f.value is not None and not _dudoso(perfil, ruta)


def _dudoso(perfil: Perfil, ruta: str) -> bool:
    f = perfil.mifid.get(ruta)
    return f is not None and (Flag.low_confidence in f.flags or Flag.inconsistent in f.flags)


def planificar(perfil: Perfil, peticiones: list[Peticion], vigentes: frozenset[str] = frozenset()) -> Alcance:
    """Une las peticiones, añade dependencias de lo que cambia, ordena y recorta. Determinista.

    `value_changed`: la ruta ya está respondida (cambió en esta revisión), así que no se pregunta otra vez
    salvo que haya quedado dudosa; sí se confirman sus dependencias de `calculos.py`. Cuenta como cambio
    para decidir si hay que ampliar a una reevaluación completa.

    `vigentes`: rutas que el inversor ya dio o confirmó en esta revisión. No se vuelven a preguntar, sea
    cual sea el tipo de pregunta (sí si faltan o han quedado dudosas), y salen en `Alcance.respondidas`.
    Las reglas para ampliar a una reevaluación completa se evalúan antes de quitarlas, así que contestar
    no cambia esa decisión.
    """
    tipos: dict[str, TipoPregunta] = {}
    motivos: dict[str, list[Motivo]] = {}
    respondidas: set[str] = set()

    def anotar(ruta: str, tipo: TipoPregunta, motivo: Motivo) -> None:
        if tipos.get(ruta) != TipoPregunta.repreguntar:  # repreguntar gana a confirmar
            tipos[ruta] = tipo
        if motivo not in motivos.setdefault(ruta, []):
            motivos[ruta].append(motivo)

    for p in peticiones:
        repreguntar, confirmar = _semillas(p)
        if p.motivo == Motivo.value_changed:
            respondidas.update(confirmar)
            for r in confirmar:
                for dep in DEPENDENCIAS.get(r, []):
                    anotar(dep, TipoPregunta.confirmar, p.motivo)
            continue
        for r in repreguntar:
            anotar(r, TipoPregunta.repreguntar, p.motivo)
        for r in confirmar:
            anotar(r, TipoPregunta.confirmar, p.motivo)
        for r in repreguntar:
            for dep in DEPENDENCIAS.get(r, []):
                anotar(dep, TipoPregunta.confirmar, p.motivo)

    for r in respondidas:
        if _dudoso(perfil, r):
            anotar(r, TipoPregunta.repreguntar, Motivo.value_changed)
    preguntas = [Pregunta(path=r, tipo=_tipo(perfil, r, t), motivos=motivos[r], valor_vigente=valor(perfil, r))
                 for r, t in tipos.items()]
    preguntas.sort(key=lambda q: (q.tipo == TipoPregunta.confirmar, ORDEN_GUION[q.path]))
    bloques = {q.path.split(".")[0] for q in preguntas if q.tipo != TipoPregunta.confirmar}  # antes de quitar
    # Ya contestadas en esta revisión: cambiadas (value_changed, salvo dudosas) o dadas o confirmadas (vigentes).
    hechas = {q.path for q in preguntas
              if (q.path in respondidas or q.path in vigentes) and _dado(perfil, q.path)}
    ya = [q for q in preguntas if q.path in hechas]
    preguntas = [q for q in preguntas if q.path not in hechas]

    razones = []
    if any(p.motivo == Motivo.full_reassessment_requested for p in peticiones):
        razones.append("lo pide el cliente o la entidad")
    bloques |= {r.split(".")[0] for r in respondidas}
    if len(bloques) >= BLOQUES_AMPLIAR:
        razones.append(f"cambios en {len(bloques)} bloques: {', '.join(sorted(bloques))}")
    if any(a.status == EstadoAlerta.open and a.flag == Flag.needs_advisor for a in perfil.alerts):
        razones.append("hay una alerta abierta que necesita al asesor")

    return Alcance(preguntas=preguntas[:MAX_PREGUNTAS], aplazadas=[q.path for q in preguntas[MAX_PREGUNTAS:]],
                   reevaluacion_completa=bool(razones), razones=razones,
                   respondidas=sorted(ya, key=lambda q: ORDEN_GUION[q.path]))


# ---------- cambios entre versiones ----------

def _contenido(f: Fact | None) -> tuple[Any, Any, tuple[str, ...]] | None:
    """Lo que cuenta como cambio de un dato: valor, declarado y flags (no evidencia, confianza ni fechas)."""
    return None if f is None else (f.value, f.declared, tuple(sorted(x.value for x in f.flags)))


def orden_guion(rutas) -> list[str]:
    return sorted(set(rutas), key=lambda r: (ORDEN_GUION.get(r, len(ORDEN_GUION)), r))


def cambiados(anterior: Perfil, nueva: Perfil) -> list[str]:
    """Rutas MiFID no calculadas cuyo valor, declarado o flags difieren entre dos versiones (orden del guion).

    Única definición de «dato cambiado»: la usan `store.revision_pendiente` (lo que se avisa a los
    consumidores) y `alcance_revision` (lo que se pregunta al inversor). Una confirmación no cuenta.
    """
    return orden_guion(r for r in set(anterior.mifid) | set(nueva.mifid)
                       if r not in CALCULADOS and _contenido(anterior.mifid.get(r)) != _contenido(nueva.mifid.get(r)))


# ---------- calendario ----------

def ultimo_momento(f: Fact) -> datetime:
    """Última vez que el cliente dio este dato: al escribirlo o al confirmarlo (§4.3 del diseño)."""
    return max(f.updated_at, f.confirmed_at or f.updated_at)


def ultima_vez(f: Fact) -> date:
    return ultimo_momento(f).date()


def plazo_restante(f: Fact, hoy: date) -> float:
    """Años que quedan de un plazo declarado, contados desde la última vez que el cliente lo dijo.

    Un plazo confirmado («siguen siendo diez años») cuenta desde la confirmación. Límite: si el dato se
    reescribe por otro motivo (p. ej. al recargar un fixture) también se renueva. La solución definitiva es
    guardar una fecha objetivo (§4.3 del diseño), que es un cambio de contrato.
    """
    transcurridos = (hoy - ultima_vez(f)).days / DIAS_POR_ANIO
    return round(float(f.value) - transcurridos, 1)


def _recalculado(perfil: Perfil) -> Perfil:
    copia = perfil.model_copy(deep=True)
    calculos.recalcular(copia)
    return copia


def vencimientos(perfil: Perfil, hoy: date) -> list[Peticion]:
    """Peticiones por calendario. Se evalúa al leer: no hace falta un proceso periódico.

    Es pura y vale para cualquier estado; tiene sentido sobre el perfil `active`.
    """
    out: list[Peticion] = []
    nr = perfil.review.next_review
    if nr and date.fromisoformat(nr) <= hoy:
        vence = date.fromisoformat(nr)
        # Revisión anual: lo que el inversor ya dio o confirmó después del vencimiento sigue vigente.
        rutas = [r for r in _REVISION_ANUAL
                 if (f := perfil.mifid.get(r)) is None or f.value is None or ultima_vez(f) < vence]
        if rutas:
            out.append(Peticion(motivo=Motivo.next_review_due, rutas=rutas))

    caducados: dict[str, list[str]] = {}
    for ruta, f in perfil.mifid.items():
        bloque = ruta.split(".")[0]
        if ruta in CALCULADOS or bloque not in CADUCIDAD_DIAS or f.value is None or ruta not in CAMPOS:
            continue
        if (hoy - ultima_vez(f)).days > CADUCIDAD_DIAS[bloque]:
            caducados.setdefault(bloque, []).append(ruta)
    for bloque in sorted(caducados, key=lambda b: min(ORDEN_GUION[r] for r in caducados[b])):
        out.append(Peticion(motivo=Motivo.stale_block, rutas=sorted(caducados[bloque], key=ORDEN_GUION.get)))

    plazo = perfil.mifid.get(f"{_O}horizon_years")
    if plazo is not None and plazo.value is not None:
        restante = plazo_restante(plazo, hoy)
        if restante <= 0:
            out.append(Peticion(motivo=Motivo.horizon_elapsed))
        else:
            base = _recalculado(perfil)
            simulado = base.model_copy(deep=True)
            simulado.mifid[f"{_O}horizon_years"] = plazo.model_copy(update={"value": restante})
            calculos.recalcular(simulado)
            if es_material(base, simulado):
                out.append(Peticion(motivo=Motivo.horizon_elapsed))
    return out


# ---------- materialidad ----------

def _filtros(perfil: Perfil) -> tuple[dict[str, tuple[str, Any]], bool]:
    r = calculos.restricciones(perfil)
    return {f.field: (f.op, f.value) for f in r.post_filters}, bool(r.funds_query.get("esg_only"))


def es_material(anterior: Perfil, nueva: Perfil) -> list[str]:
    """Qué cambia en resultados y restricciones. Vacío = solo confirmaciones o cambios sin efecto.

    Compara lo ya calculado en cada versión (store siempre recalcula antes de guardar).
    """
    out: list[str] = []
    sa, sn = anterior.assessments.suitability, nueva.assessments.suitability
    if sa.complete != sn.complete:
        out.append("suitability_complete")
    if sa.risk_profile != sn.risk_profile:
        out.append("risk_profile")
        if sa.risk_profile and sn.risk_profile and abs(
                ORDEN_PERFILES.index(sa.risk_profile) - ORDEN_PERFILES.index(sn.risk_profile)) >= SALTO_PERFIL_AMPLIAR:
            out.append("risk_profile_jump")
    for fam in FAMILIAS:
        if anterior.assessments.appropriateness.get(fam) != nueva.assessments.appropriateness.get(fam):
            out.append(f"appropriateness:{fam}")
    (fa, esg_a), (fn, esg_n) = _filtros(anterior), _filtros(nueva)
    out += [f"filter:{campo}" for campo in sorted(set(fa) | set(fn)) if fa.get(campo) != fn.get(campo)]
    if esg_a != esg_n:
        out.append("esg_only")
    ca, cn = valor(anterior, f"{_F}loss_capacity_eur"), valor(nueva, f"{_F}loss_capacity_eur")
    if (ca is None) != (cn is None) or (
            ca is not None and cn is not None and abs(cn - ca) > VARIACION_CAPACIDAD * abs(ca)):
        out.append("loss_capacity")
    return out


# ---------- sesión de revisión ----------

def alcance_revision(servido: Perfil, ultima: Perfil, hoy: date, motivos: Iterable[Motivo] = (),
                     desde: datetime | None = None) -> Alcance:
    """Único planificador de una microentrevista sobre un perfil ya validado. Determinista, sin modelo.

    - `servido`: el último perfil `active` (lo validado y sus evidencias; `store.perfil_para_consumidor`).
    - `ultima`: la última versión (`store.perfil`), con lo que ya haya cambiado o confirmado en la revisión.
    - `motivos`: lo que el inversor dice que ha cambiado (catálogo cerrado de motivos de rutas fijas,
      p. ej. `planned_expense`). Opcional.
    - `desde`: cuándo empezó la revisión (p. ej. al pedirla el cliente). Lo dado o confirmado después cuenta
      como respondido. Por defecto, la creación de `servido`.

    Combina: los motivos del inversor, los vencimientos de `ultima`, los datos ya cambiados desde `servido`
    (`value_changed`: no se repiten; se confirman sus dependencias de calculos.py y del verificador) y lo
    respondido en la revisión (sale de las preguntas y aparece en `respondidas`). Los resultados (perfil de
    riesgo, restricciones) los recalcula después `calculos.recalcular` en cada escritura: aquí no se calcula
    nada nuevo. `apertura` siempre es True: la revisión no termina por tener la lista vacía.
    """
    if servido.status != EstadoPerfil.active:
        raise DatoInvalido("Sin un perfil validado no hay revisión: es una entrevista inicial")
    if ultima.client_id != servido.client_id or ultima.version < servido.version:
        raise DatoInvalido("La última versión no corresponde al perfil servido")
    peticiones = [Peticion(motivo=Motivo(m)) for m in dict.fromkeys(motivos)]  # sin repetir, en su orden
    peticiones += vencimientos(ultima, hoy)
    cambios = [r for r in cambiados(servido, ultima) if r in CAMPOS and not r.startswith("disclosures.")]
    if cambios:
        peticiones.append(Peticion(motivo=Motivo.value_changed, rutas=cambios))
    desde = desde or servido.created_at
    # Respondido = el inversor lo dijo (con su cita) desde que empezó la revisión; una corrección del asesor
    # sin cita no cuenta como respuesta suya.
    vigentes = frozenset(r for r, f in ultima.mifid.items()
                         if r not in CALCULADOS and f.value is not None and f.evidence
                         and ultimo_momento(f) >= desde)
    return planificar(ultima, peticiones, vigentes).model_copy(update={"apertura": True})
