"""Servicio de perfiles: la ÚNICA puerta de escritura del perfil.

Agentes, asesor, fixtures y webhooks escriben a través de aquí; la API, el MCP y el expediente
solo leen. Cada escritura:
  1. lee la versión vigente y hace una copia (nunca se modifica una versión guardada);
  2. aplica el cambio, validado contra el esquema y las reglas de autoría;
  3. recalcula datos calculados, evaluaciones y estado (funciones deterministas);
  4. inserta la versión nueva. Si otra escritura se adelantó, relee y reintenta (concurrencia optimista);
  5. publica los eventos para el panel en vivo.
"""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..dominio import calculos, esquema, estados, evaluaciones, restricciones
from ..dominio import supuestos as S
from ..dominio.errores import (
    CampoInvalido,
    ConflictoVersion,
    EscrituraNoPermitida,
    NoEncontrado,
    TransicionNoPermitida,
)
from ..dominio.modelos import (
    AUTOR_FIXTURE,
    AUTOR_SISTEMA,
    AUTOR_VERIFICADOR,
    ActualizacionCampo,
    Alerta,
    CapaPersonal,
    EstadoAlerta,
    EstadoPerfil,
    Fact,
    Flag,
    Fuente,
    Perfil,
    Restricciones,
    Revision,
    ahora,
    autor_asesor,
    es_agente,
    es_asesor,
)
from ..persistencia.repositorio import Repositorio
from .eventos import BusEventos, Evento

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "v1"
MAX_REINTENTOS = 5
_TIPOS_FLAG = {f.value for f in Flag}
_ORDEN_FLAG = list(Flag)


class _SinCambios(Exception):
    """La operación no cambia nada: no se crea versión."""


def _iguales(a: Fact, b: Fact) -> bool:
    excluir = {"updated_at", "updated_by"}
    return a.model_dump(exclude=excluir) == b.model_dump(exclude=excluir)


class ServicioPerfiles:
    def __init__(self, repo: Repositorio, bus: BusEventos | None = None, reloj: Callable = ahora):
        self.repo = repo
        self.bus = bus or BusEventos()
        self._reloj = reloj
        self._candados: dict[str, threading.RLock] = {}
        self._candado_global = threading.Lock()

    def _candado(self, client_id: str) -> threading.RLock:
        with self._candado_global:
            return self._candados.setdefault(client_id, threading.RLock())

    # ================= lectura =================

    def perfil(self, client_id: str, version: int | None = None) -> Perfil:
        p = self.repo.ultima_version(client_id) if version is None else self.repo.version(client_id, version)
        if p is None:
            raise NoEncontrado(f"{client_id}" + (f" v{version}" if version is not None else ""))
        return p

    def historial(self, client_id: str) -> list[dict[str, Any]]:
        h = self.repo.historial(client_id)
        if not h:
            raise NoEncontrado(client_id)
        return h

    def personal(self, client_id: str) -> CapaPersonal | None:
        self.perfil(client_id)
        return self.repo.ultima_personal(client_id)

    def restricciones(self, client_id: str) -> Restricciones:
        return restricciones.calcular(self.perfil(client_id), self.repo.ultima_personal(client_id))

    def exportar(self, client_id: str, version: int | None = None) -> dict:
        """Perfil con la forma del contrato 04. La capa personal es siempre la vigente."""
        return self.perfil(client_id, version).exportar(self.repo.ultima_personal(client_id))

    def evidencia(self, client_id: str, ruta: str) -> dict[str, Any]:
        esquema.espec(ruta)
        p = self.perfil(client_id)
        dato = p.mifid.get(ruta)
        if dato is None:
            raise NoEncontrado(f"{client_id}: sin datos en {ruta}")
        return {
            "client_id": client_id, "profile_version": p.version, "field": ruta,
            "value": dato.value, "declared": dato.declared, "source": dato.source.value,
            "confidence": dato.confidence, "confidence_basis": dato.confidence_basis,
            "flags": [f.value for f in dato.flags],
            "evidence": [e.model_dump(mode="json") for e in dato.evidence],
        }

    # ================= escritura =================

    def crear(self, client_id: str | None = None) -> Perfil:
        """Crea el cliente con un perfil vacío en borrador; si ya existe, devuelve el vigente."""
        cid = client_id or f"cliente-{uuid.uuid4().hex[:8]}"
        if (existente := self.repo.ultima_version(cid)) is not None:
            return existente
        p = Perfil(client_id=cid, created_at=self._reloj(), reason="creación", author=AUTOR_SISTEMA)
        self._consolidar(p, None)
        if self.repo.crear_cliente_con_perfil(p):
            self._publicar(None, p)
            return p
        return self.perfil(cid)  # otra petición lo creó a la vez

    def comprobar_cambio(self, cambio: ActualizacionCampo, autor: str) -> ActualizacionCampo:
        """Valida un cambio contra el esquema y las reglas de autoría y lo devuelve normalizado."""
        e = esquema.espec(cambio.field)
        if e.calculado or cambio.source == Fuente.calculated:
            raise EscrituraNoPermitida(f"{cambio.field}: los datos calculados solo los pone el backend")
        if es_asesor(autor):
            fuente = Fuente.advisor
        elif cambio.source == Fuente.advisor:
            raise EscrituraNoPermitida(f"{cambio.field}: solo una persona de la entidad escribe source=advisor")
        else:
            fuente = cambio.source

        valor = esquema.normalizar(cambio.field, cambio.value)
        declarado = esquema.normalizar(cambio.field, cambio.declared)
        if es_agente(autor) and valor is not None and not cambio.evidence:
            raise EscrituraNoPermitida(f"{cambio.field}: un dato sacado de la conversación necesita su evidencia")

        flags = set(cambio.flags)
        if declarado is not None and declarado == valor:
            declarado = None
        if declarado is not None and fuente == Fuente.demonstrated:
            flags.add(Flag.declared_vs_demonstrated)
        if declarado is None:
            flags.discard(Flag.declared_vs_demonstrated)
        if fuente == Fuente.advisor:
            flags.discard(Flag.low_confidence)  # la persona de la entidad asume el dato
        elif calculos.es_confianza_baja(cambio.confidence):
            flags.add(Flag.low_confidence)
        return cambio.model_copy(update={
            "source": fuente, "value": valor, "declared": declarado,
            "flags": sorted(flags, key=_ORDEN_FLAG.index),
        })

    def aplicar(self, client_id: str, cambios: Iterable[ActualizacionCampo], motivo: str, autor: str,
                version_esperada: int | None = None) -> Perfil:
        """Escribe datos. Si alguno no es válido, no se escribe ninguno."""
        normalizados = [self.comprobar_cambio(c, autor) for c in cambios]

        def mutar(p: Perfil) -> str:
            cambiado = False
            for c in normalizados:
                previo = p.mifid.get(c.field)
                if c.value is None:
                    cambiado |= p.mifid.pop(c.field, None) is not None
                    continue
                nuevo = Fact(value=c.value, declared=c.declared, source=c.source, confidence=c.confidence,
                             confidence_basis=c.confidence_basis, evidence=c.evidence, flags=c.flags,
                             updated_at=p.created_at, updated_by=autor)
                if previo is None or not _iguales(previo, nuevo):
                    p.mifid[c.field] = nuevo
                    cambiado = True
            if not cambiado:
                raise _SinCambios
            return motivo

        return self._escribir(client_id, mutar, autor, version_esperada,
                              estado=lambda p: estados.tras_cambio(p, por_asesor=es_asesor(autor)))

    def anadir_alertas(self, client_id: str, alertas: Iterable[Alerta], autor: str = AUTOR_VERIFICADOR) -> Perfil:
        """Añade alertas nuevas; ignora las que ya están abiertas para el mismo tipo y dato."""
        alertas = list(alertas)
        for a in alertas:
            if a.field is not None:
                esquema.espec(a.field)

        def mutar(p: Perfil) -> str:
            abiertas = {(a.type, a.field) for a in p.alertas_abiertas()}
            ids = {a.id for a in p.alerts}
            nuevas = []
            for a in alertas:
                if (a.type, a.field) in abiertas or a.id in ids:
                    continue
                nuevas.append(a.model_copy(update={"created_by": a.created_by or autor,
                                                   "created_at": p.created_at,
                                                   "status": EstadoAlerta.open}))
                abiertas.add((a.type, a.field))
                ids.add(a.id)
            if not nuevas:
                raise _SinCambios
            p.alerts.extend(nuevas)
            return f"{len(nuevas)} alerta(s) de {autor}"

        return self._escribir(client_id, mutar, autor,
                              estado=lambda p: estados.tras_cambio(p, por_asesor=es_asesor(autor)))

    def resolver_alerta(self, client_id: str, alerta_id: str, autor: str) -> Perfil:
        def mutar(p: Perfil) -> str:
            i = next((i for i, a in enumerate(p.alerts) if a.id == alerta_id), None)
            if i is None:
                raise NoEncontrado(f"{client_id}: alerta {alerta_id}")
            if p.alerts[i].status == EstadoAlerta.resolved:
                raise _SinCambios
            self._resolver(p, i, autor)
            return f"alerta {alerta_id} resuelta por {autor}"

        return self._escribir(client_id, mutar, autor,
                              estado=lambda p: estados.tras_cambio(p, por_asesor=es_asesor(autor)))

    def _resolver(self, p: Perfil, i: int, autor: str) -> None:
        a = p.alerts[i]
        p.alerts[i] = a.model_copy(update={"status": EstadoAlerta.resolved,
                                           "resolved_at": p.created_at, "resolved_by": autor})
        # La marca del dato se quita, salvo declarado-vs-demostrado, que describe el propio dato.
        sigue_abierta = any(o.type == a.type and o.field == a.field for o in p.alertas_abiertas())
        if a.field in p.mifid and a.type in _TIPOS_FLAG and a.type != Flag.declared_vs_demonstrated.value \
                and not sigue_abierta:
            dato = p.mifid[a.field]
            p.mifid[a.field] = dato.model_copy(update={"flags": [f for f in dato.flags if f.value != a.type]})

    def validar(self, client_id: str, asesor_id: str,
                correcciones: Iterable[ActualizacionCampo] = ()) -> Perfil:
        """La persona de la entidad corrige (opcional) y valida: el perfil pasa a 'active'."""
        actual = self.perfil(client_id)
        if actual.status not in (EstadoPerfil.draft, EstadoPerfil.pending_validation):
            raise TransicionNoPermitida(f"No se puede validar un perfil en estado '{actual.status.value}'")
        autor = autor_asesor(asesor_id)
        correcciones = list(correcciones)
        if correcciones:
            self.aplicar(client_id, correcciones, f"advisor_correction: {asesor_id}", autor)

        def mutar(p: Perfil) -> str:
            # Al validar, la persona de la entidad da por revisadas las alertas que pedían revisión humana.
            for i, a in enumerate(p.alerts):
                if a.status == EstadoAlerta.open and a.type == Flag.needs_advisor.value:
                    self._resolver(p, i, autor)
            p.review = Revision(
                validated_by=asesor_id, validated_at=p.created_at,
                next_review=(p.created_at + timedelta(days=S.DIAS_HASTA_REVISION)).date().isoformat(),
            )
            return f"validado por {asesor_id}"

        def estado(p: Perfil) -> EstadoPerfil:
            listo = estados.tras_cambio(p, por_asesor=True)
            if listo != EstadoPerfil.pending_validation:
                faltan = ", ".join(p.assessments.suitability.missing) or "ninguno"
                raise TransicionNoPermitida(f"El perfil no está listo para validar. Faltan o hay que repreguntar: {faltan}")
            p.status = listo
            return EstadoPerfil.active

        return self._escribir(client_id, mutar, autor, estado=estado)

    def pedir_repregunta(self, client_id: str, asesor_id: str, rutas: Iterable[str], motivo: str) -> Perfil:
        """La persona de la entidad devuelve el perfil a borrador para repreguntar ciertos datos."""
        rutas = list(rutas)
        for r in rutas:
            esquema.espec(r)
        autor = autor_asesor(asesor_id)

        def mutar(p: Perfil) -> str:
            if p.status not in (EstadoPerfil.draft, EstadoPerfil.pending_validation):
                raise TransicionNoPermitida(f"No se puede repreguntar con el perfil en '{p.status.value}'")
            for r in rutas:
                if r in p.mifid and Flag.low_confidence not in p.mifid[r].flags:
                    dato = p.mifid[r]
                    p.mifid[r] = dato.model_copy(update={"flags": sorted({*dato.flags, Flag.low_confidence},
                                                                         key=_ORDEN_FLAG.index)})
                p.alerts.append(Alerta(id=f"a-{uuid.uuid4().hex[:8]}", type=Flag.low_confidence.value, field=r,
                                       message=motivo, created_at=p.created_at, created_by=autor))
            return f"repreguntar ({asesor_id}): {', '.join(rutas)}"

        return self._escribir(client_id, mutar, autor, estado=lambda p: EstadoPerfil.draft)

    def marcar_revision(self, client_id: str, motivo: str, autor: str) -> Perfil:
        """Evento vital o revisión periódica: un perfil activo pasa a 'review_due'."""
        return self._escribir(client_id, lambda p: motivo, autor, estado=lambda p: EstadoPerfil.review_due)

    def reabrir(self, client_id: str, autor: str) -> Perfil:
        """Empieza una entrevista corta sobre lo que cambió: 'review_due' → 'draft'."""
        return self._escribir(client_id, lambda p: "reevaluación: empieza una entrevista corta", autor,
                              estado=lambda p: EstadoPerfil.draft)

    # ================= capa personal =================

    def guardar_personal(self, client_id: str, datos: dict[str, Any], consentimiento: bool, autor: str) -> CapaPersonal:
        self.perfil(client_id)
        with self._candado(client_id):
            previa = self.repo.ultima_personal(client_id)
            momento = self._reloj()
            consentido_en = None
            if consentimiento:
                consentido_en = previa.consent_at if previa and previa.consent_given else momento
            try:
                capa = CapaPersonal(client_id=client_id, version=(previa.version + 1) if previa else 1,
                                    consent_given=consentimiento, consent_at=consentido_en,
                                    data=datos, author=autor, created_at=momento)
            except ValidationError as e:
                raise CampoInvalido(f"Capa personal no válida: {e.errors()[0]['msg']}") from e
            self.repo.insertar_personal(capa)
            return capa

    def borrar_personal(self, client_id: str) -> int:
        """Derecho de supresión: borra la capa personal. El registro MiFID no se toca."""
        self.perfil(client_id)
        return self.repo.borrar_personal(client_id)

    # ================= fixtures (datos simulados) =================

    def cargar_fixture(self, nombre: str) -> Perfil:
        """Carga un perfil de ejemplo como versión nueva (reinicio de demo). Queda registrado en el historial."""
        ruta = FIXTURES_DIR / f"{nombre}.json"
        if not ruta.is_file():
            raise NoEncontrado(f"fixture {nombre}")
        datos = json.loads(ruta.read_text("utf-8"))
        cid = datos["client_id"]
        cambios = [self.comprobar_cambio(ActualizacionCampo(field=r, **d), AUTOR_FIXTURE)
                   for r, d in datos.get("mifid", {}).items()]
        alertas = [Alerta.model_validate(a) for a in datos.get("alerts", [])]
        self.crear(cid)

        def mutar(p: Perfil) -> str:
            p.mifid = {
                c.field: Fact(value=c.value, declared=c.declared, source=c.source, confidence=c.confidence,
                              confidence_basis=c.confidence_basis, evidence=c.evidence, flags=c.flags,
                              updated_at=p.created_at, updated_by=AUTOR_FIXTURE)
                for c in cambios if c.value is not None
            }
            p.alerts = [a.model_copy(update={"created_by": a.created_by or AUTOR_FIXTURE}) for a in alertas]
            p.review = Revision()
            p.status = EstadoPerfil.draft  # reinicio de demo: fuera del flujo normal, queda en el motivo
            return datos.get("reason", f"fixture {nombre}")

        perfil = self._escribir(cid, mutar, AUTOR_FIXTURE, estado=lambda p: estados.tras_cambio(p, False))
        if "personal" in datos:
            self.guardar_personal(cid, datos["personal"].get("data", {}),
                                  datos["personal"].get("consent_given", False), AUTOR_FIXTURE)
        return perfil

    # ================= núcleo =================

    def _escribir(self, client_id: str, mutar: Callable[[Perfil], str], autor: str,
                  version_esperada: int | None = None,
                  estado: Callable[[Perfil], EstadoPerfil] | None = None) -> Perfil:
        with self._candado(client_id):
            for _ in range(MAX_REINTENTOS):
                actual = self.perfil(client_id)
                if version_esperada is not None and actual.version != version_esperada:
                    raise ConflictoVersion(
                        f"Se esperaba la versión {version_esperada} y la vigente es la {actual.version}")
                nueva = actual.model_copy(deep=True)
                nueva.version = actual.version + 1
                nueva.created_at = self._reloj()
                nueva.author = autor
                try:
                    nueva.reason = mutar(nueva)
                except _SinCambios:
                    return actual
                self._consolidar(nueva, actual)
                if estado is not None:
                    destino = estado(nueva)
                    estados.comprobar(nueva.status, destino)
                    nueva.status = destino
                try:
                    self.repo.insertar_version(nueva)
                except ConflictoVersion:
                    if version_esperada is not None:
                        raise
                    continue  # otra escritura (p. ej. de otro proceso) se adelantó: releer y reintentar
                self._publicar(actual, nueva)
                return nueva
        raise ConflictoVersion(f"{client_id}: demasiadas escrituras simultáneas, inténtalo de nuevo")

    def _consolidar(self, nueva: Perfil, anterior: Perfil | None) -> None:
        """Recalcula todo lo derivado: datos calculados, marcas de alertas, evaluaciones y contador."""
        for r in esquema.CALCULADOS:
            nueva.mifid.pop(r, None)
        for r, dato in calculos.campos_calculados(nueva.mifid, nueva.created_at).items():
            previo = anterior.mifid.get(r) if anterior else None
            mismo = previo is not None and previo.value == dato.value and previo.inputs == dato.inputs
            nueva.mifid[r] = previo if mismo else dato
        for a in nueva.alertas_abiertas():
            if a.field in nueva.mifid and a.type in _TIPOS_FLAG:
                dato = nueva.mifid[a.field]
                if Flag(a.type) not in dato.flags:
                    nueva.mifid[a.field] = dato.model_copy(
                        update={"flags": sorted({*dato.flags, Flag(a.type)}, key=_ORDEN_FLAG.index)})
        nueva.assessments = evaluaciones.evaluar(nueva)
        nueva.review.open_flags = len(nueva.alertas_abiertas())

    def _publicar(self, anterior: Perfil | None, nueva: Perfil) -> None:
        cid, v = nueva.client_id, nueva.version
        previos = anterior.mifid if anterior else {}
        for r in sorted(set(previos) | set(nueva.mifid)):
            if previos.get(r) != nueva.mifid.get(r):
                dato = nueva.mifid.get(r)
                self.bus.publicar(Evento("profile.patch", cid, v, {
                    "path": r, "fact": dato.model_dump(mode="json") if dato else None}))
        ids_previos = {a.id for a in anterior.alerts} if anterior else set()
        for a in nueva.alerts:
            if a.id not in ids_previos:
                self.bus.publicar(Evento("flag.raised", cid, v, {
                    "path": a.field, "flag": a.type, "message": a.message, "alert_id": a.id}))
        self.bus.publicar(Evento("profile.status", cid, v, {
            "status": nueva.status.value,
            "complete": nueva.assessments.suitability.complete,
            "missing": nueva.assessments.suitability.missing,
        }))
