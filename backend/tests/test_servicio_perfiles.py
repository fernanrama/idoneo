"""Servicio de perfiles sobre base de datos real (SQLite y, si está configurado, Postgres local)."""

from __future__ import annotations

import threading

import pytest

from app.perfil.dominio import supuestos as S
from app.perfil.dominio.errores import (
    CampoInvalido,
    ConflictoVersion,
    EscrituraNoPermitida,
    NoEncontrado,
    TransicionNoPermitida,
)
from app.perfil.dominio.modelos import (
    AUTOR_EXTRACTOR,
    AUTOR_VERIFICADOR,
    ActualizacionCampo,
    Alerta,
    Conveniencia,
    EstadoAlerta,
    EstadoPerfil,
    Evidencia,
    Flag,
    Fuente,
    PerfilRiesgo,
    autor_asesor,
)

EV = [Evidencia(session_id="s-1", turn_id="t-1", t=(1.0, 2.0), quote="lo que dijo")]


def cambio(campo, valor, fuente=Fuente.declared, **extra):
    return ActualizacionCampo(field=campo, value=valor, source=fuente, evidence=EV, **extra)


# ---------- Carmen de punta a punta ----------

def test_carmen_queda_pendiente_de_validar(carmen, servicios):
    assert carmen.status == EstadoPerfil.pending_validation
    ido = carmen.assessments.suitability
    assert ido.complete and ido.risk_profile == PerfilRiesgo.CONSERVADOR
    assert ido.max_sri == S.SRI_MAX_POR_PERFIL[PerfilRiesgo.CONSERVADOR]
    assert carmen.assessments.appropriateness["equity_funds"] == Conveniencia.not_appropriate
    assert carmen.valor("financial.loss_capacity_eur") == 74600
    assert Flag.declared_vs_demonstrated in carmen.mifid["knowledge.equity_funds"].flags
    r = servicios.perfiles.restricciones("carmen-68")
    assert not r.usable and r.funds_query.asset_type == ["Monetario", "Renta Fija"]


def test_validar_activa_y_hace_usable(carmen, servicios):
    p = servicios.perfiles.validar("carmen-68", "asesor-07")
    assert p.status == EstadoPerfil.active and p.version == carmen.version + 1
    assert p.review.validated_by == "asesor-07" and p.review.next_review
    assert servicios.perfiles.restricciones("carmen-68").usable


def test_cambio_tras_validar_obliga_a_revisar(carmen, servicios):
    servicios.perfiles.validar("carmen-68", "asesor-07")
    p = servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 5000)], "nuevo préstamo",
                                   AUTOR_EXTRACTOR)
    assert p.status == EstadoPerfil.review_due
    assert not servicios.perfiles.restricciones("carmen-68").usable


def test_correccion_del_asesor_no_obliga_a_revisar(carmen, servicios):
    servicios.perfiles.validar("carmen-68", "asesor-07")
    p = servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 100)], "corrección",
                                   autor_asesor("asesor-07"))
    assert p.status == EstadoPerfil.active
    assert p.mifid["financial.debts_eur"].source == Fuente.advisor


# ---------- versiones: nada se sobrescribe ----------

def test_las_versiones_anteriores_no_cambian(carmen, servicios):
    antes = servicios.perfiles.perfil("carmen-68", carmen.version).model_dump()
    servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 1000)], "cambio", AUTOR_EXTRACTOR)
    assert servicios.perfiles.perfil("carmen-68", carmen.version).model_dump() == antes
    historial = servicios.perfiles.historial("carmen-68")
    assert [h["version"] for h in historial] == list(range(1, carmen.version + 2))
    assert historial[-1]["reason"] == "cambio" and historial[-1]["author"] == AUTOR_EXTRACTOR


def test_reescribir_lo_mismo_no_crea_version(carmen, servicios):
    dato = carmen.mifid["financial.debts_eur"]
    p = servicios.perfiles.aplicar("carmen-68", [ActualizacionCampo(
        field="financial.debts_eur", value=0, source=Fuente.declared, confidence=dato.confidence,
        evidence=dato.evidence)], "repetido", AUTOR_EXTRACTOR)
    assert p.version == carmen.version


def test_calculados_se_recalculan(carmen, servicios):
    p = servicios.perfiles.aplicar("carmen-68", [cambio("financial.liquid_savings_eur", 10000)], "x",
                                   AUTOR_EXTRACTOR)
    assert p.valor("financial.loss_capacity_eur") == 10000 - 6 * 900
    assert p.mifid["financial.loss_capacity_eur"].source == Fuente.calculated


# ---------- reglas de escritura ----------

def test_agente_no_escribe_calculados_ni_como_asesor(servicios):
    servicios.perfiles.crear("c1")
    with pytest.raises(EscrituraNoPermitida):
        servicios.perfiles.aplicar("c1", [cambio("financial.loss_capacity_eur", 1)], "x", AUTOR_EXTRACTOR)
    with pytest.raises(EscrituraNoPermitida):
        servicios.perfiles.aplicar("c1", [cambio("financial.debts_eur", 1, Fuente.advisor)], "x", AUTOR_EXTRACTOR)
    with pytest.raises(EscrituraNoPermitida):
        servicios.perfiles.aplicar("c1", [ActualizacionCampo(field="financial.debts_eur", value=1,
                                                             source=Fuente.declared)], "x", AUTOR_EXTRACTOR)


def test_un_cambio_invalido_anula_todo_el_lote(servicios):
    servicios.perfiles.crear("c1")
    with pytest.raises(CampoInvalido):
        servicios.perfiles.aplicar("c1", [cambio("financial.debts_eur", 10), cambio("knowledge.cripto", "high")],
                                   "x", AUTOR_EXTRACTOR)
    assert servicios.perfiles.perfil("c1").version == 1


def test_marcas_automaticas(servicios):
    servicios.perfiles.crear("c1")
    p = servicios.perfiles.aplicar("c1", [
        cambio("knowledge.etfs", "basic", Fuente.demonstrated, declared="high", confidence=0.9),
        cambio("knowledge.stocks", "medium", Fuente.demonstrated, declared="medium", confidence=0.5),
    ], "x", AUTOR_EXTRACTOR)
    assert p.mifid["knowledge.etfs"].flags == [Flag.declared_vs_demonstrated]
    assert p.mifid["knowledge.stocks"].declared is None  # igual a lo demostrado: no se guarda
    assert p.mifid["knowledge.stocks"].flags == [Flag.low_confidence]


def test_cliente_inexistente(servicios):
    with pytest.raises(NoEncontrado):
        servicios.perfiles.perfil("nadie")
    with pytest.raises(NoEncontrado):
        servicios.perfiles.aplicar("nadie", [cambio("financial.debts_eur", 1)], "x", AUTOR_EXTRACTOR)


# ---------- estados ----------

def test_no_se_valida_incompleto(servicios):
    servicios.perfiles.crear("c1")
    with pytest.raises(TransicionNoPermitida):
        servicios.perfiles.validar("c1", "asesor-07")


def test_no_se_valida_dos_veces(carmen, servicios):
    servicios.perfiles.validar("carmen-68", "asesor-07")
    with pytest.raises(TransicionNoPermitida):
        servicios.perfiles.validar("carmen-68", "asesor-07")


def test_alerta_de_revision_humana_bloquea_y_el_asesor_la_cierra(carmen, servicios):
    p = servicios.perfiles.anadir_alertas("carmen-68", [Alerta(
        id="a-x", type="needs_advisor", field="objectives.o1.amount_eur", message="Revisar importe")])
    assert p.status == EstadoPerfil.draft
    assert Flag.needs_advisor in p.mifid["objectives.o1.amount_eur"].flags
    p = servicios.perfiles.validar("carmen-68", "asesor-07")
    assert p.status == EstadoPerfil.active
    assert next(a for a in p.alerts if a.id == "a-x").status == EstadoAlerta.resolved
    assert Flag.needs_advisor not in p.mifid["objectives.o1.amount_eur"].flags


def test_alertas_duplicadas_no_crean_version(carmen, servicios):
    alerta = Alerta(id="a-otra", type="declared_vs_demonstrated", field="knowledge.equity_funds", message="dup")
    p = servicios.perfiles.anadir_alertas("carmen-68", [alerta], AUTOR_VERIFICADOR)
    assert p.version == carmen.version


def test_repreguntar_devuelve_a_borrador(carmen, servicios):
    p = servicios.perfiles.pedir_repregunta("carmen-68", "asesor-07", ["objectives.o1.horizon_years"],
                                            "No está claro el plazo")
    assert p.status == EstadoPerfil.draft and not p.assessments.suitability.complete
    with pytest.raises(TransicionNoPermitida):
        servicios.perfiles.validar("carmen-68", "asesor-07")
    # El agente vuelve a preguntar y el dato queda con buena confianza: vuelve a estar listo
    p = servicios.perfiles.aplicar("carmen-68", [cambio("objectives.o1.horizon_years", 8, confidence=1.0)],
                                   "repregunta", AUTOR_EXTRACTOR)
    alerta = next(a for a in p.alerts if a.type == "low_confidence")
    p = servicios.perfiles.resolver_alerta("carmen-68", alerta.id, autor_asesor("asesor-07"))
    assert p.status == EstadoPerfil.pending_validation


def test_revision_por_evento_vital_y_reentrevista(carmen, servicios):
    servicios.perfiles.validar("carmen-68", "asesor-07")
    p = servicios.perfiles.marcar_revision("carmen-68", "life_event:herencia", "advisor:asesor-07")
    assert p.status == EstadoPerfil.review_due
    servicios.sesiones.crear("carmen-68")  # empieza la entrevista corta
    assert servicios.perfiles.perfil("carmen-68").status == EstadoPerfil.draft
    with pytest.raises(TransicionNoPermitida):
        servicios.perfiles.marcar_revision("carmen-68", "x", "system")  # ya no está activo
    p = servicios.perfiles.aplicar("carmen-68", [cambio("objectives.o2.goal", "ayudar a su nieta")],
                                   "nuevo objetivo", AUTOR_EXTRACTOR)
    assert p.status == EstadoPerfil.pending_validation  # sigue completo: vuelve a validación


# ---------- concurrencia ----------

def test_version_esperada_detecta_conflicto(carmen, servicios):
    servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 1)], "a", AUTOR_EXTRACTOR)
    with pytest.raises(ConflictoVersion):
        servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 2)], "b", AUTOR_EXTRACTOR,
                                   version_esperada=carmen.version)


def test_escrituras_simultaneas_no_se_pierden(carmen, servicios):
    rutas = ["financial.debts_eur", "financial.other_assets_eur", "experience.education",
             "risk_tolerance.past_behaviour", "objectives.o2.goal", "objectives.o2.horizon_years"]
    valores = [1, 2, "FP", "no vendió", "viaje", 3]
    errores = []

    def escribir(r, v):
        try:
            servicios.perfiles.aplicar("carmen-68", [cambio(r, v)], f"hilo {r}", AUTOR_EXTRACTOR)
        except Exception as e:  # pragma: no cover
            errores.append(e)

    hilos = [threading.Thread(target=escribir, args=rv) for rv in zip(rutas, valores)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert not errores
    p = servicios.perfiles.perfil("carmen-68")
    assert p.version == carmen.version + len(rutas)
    assert all(p.valor(r) is not None for r in rutas)


def test_conflicto_entre_procesos_se_reintenta(carmen, servicios):
    """Simula otro proceso que inserta la misma versión justo antes: el servicio relee y reintenta."""
    from app.perfil.servicios.perfiles import ServicioPerfiles

    otro = ServicioPerfiles(servicios.repo)  # otro proceso: sin candado compartido
    original = servicios.repo.insertar_version
    llamadas = {"n": 0}

    def insertar_con_carrera(perfil):
        if llamadas["n"] == 0:
            llamadas["n"] += 1
            otro.aplicar("carmen-68", [cambio("experience.education", "FP")], "otro proceso", AUTOR_EXTRACTOR)
        return original(perfil)

    servicios.repo.insertar_version = insertar_con_carrera
    p = servicios.perfiles.aplicar("carmen-68", [cambio("financial.debts_eur", 9)], "este", AUTOR_EXTRACTOR)
    assert p.version == carmen.version + 2
    assert p.valor("experience.education") == "FP" and p.valor("financial.debts_eur") == 9


# ---------- capa personal ----------

def test_capa_personal_separada_y_borrable(carmen, servicios):
    capa = servicios.perfiles.personal("carmen-68")
    assert capa.consent_given and capa.data["exclusions"] == ["armas", "tabaco"]
    versiones_mifid = len(servicios.perfiles.historial("carmen-68"))
    assert servicios.perfiles.borrar_personal("carmen-68") == 1
    assert servicios.perfiles.personal("carmen-68") is None
    assert len(servicios.perfiles.historial("carmen-68")) == versiones_mifid  # MiFID intacto
    assert "personal" not in servicios.perfiles.exportar("carmen-68")
    filtros = {f.field for f in servicios.perfiles.restricciones("carmen-68").post_filters}
    assert "top_sectors" not in filtros


def test_capa_personal_sin_consentimiento_rechaza_datos(servicios):
    servicios.perfiles.crear("c1")
    with pytest.raises(CampoInvalido):
        servicios.perfiles.guardar_personal("c1", {"exclusions": ["armas"]}, False, "system")


# ---------- salidas ----------

def test_exportar_con_forma_del_contrato_04(carmen, servicios):
    e = servicios.perfiles.exportar("carmen-68")
    assert e["mifid"]["knowledge"]["equity_funds"]["value"] == "none"
    assert e["mifid"]["objectives"][0]["id"] == "o1"
    assert e["assessments"]["suitability"]["risk_profile"] == "CONSERVADOR"
    assert e["personal"]["consent"]["given"] is True


def test_evidencia_de_un_dato(carmen, servicios):
    ev = servicios.perfiles.evidencia("carmen-68", "knowledge.equity_funds")
    assert "banco" in ev["evidence"][0]["quote"] and ev["evidence"][0]["t"] == [212.4, 219.8]
    with pytest.raises(CampoInvalido):
        servicios.perfiles.evidencia("carmen-68", "knowledge.etfs.nada")  # ruta que no existe
    with pytest.raises(NoEncontrado):
        servicios.perfiles.evidencia("carmen-68", "experience.education")  # ruta válida, sin dato
