"""Garantías de la base de datos (solo añadir, claves ajenas) y sesiones con transcripción."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.perfil.dominio.errores import CampoInvalido, EscrituraNoPermitida, NoEncontrado
from app.perfil.dominio.modelos import EstadoPerfil, Turno
from app.perfil.servicios.eventos import BusEventos, Evento


# ---------- registro de solo añadir ----------

@pytest.mark.parametrize("sql", [
    "update profile_versions set reason = 'manipulado'",
    "delete from profile_versions",
])
def test_el_registro_de_versiones_no_se_puede_modificar(carmen, servicios, sql):
    with pytest.raises(DBAPIError):
        with servicios.motor.begin() as c:
            c.execute(text(sql))
    assert servicios.perfiles.perfil("carmen-68").reason == carmen.reason


def test_la_transcripcion_no_se_puede_modificar(servicios):
    s = servicios.sesiones.crear("c1")
    servicios.sesiones.anadir_turno(s["session_id"], Turno(speaker="client", text="hola"))
    for sql in ("update turns set text = 'otra cosa'", "delete from turns"):
        with pytest.raises(DBAPIError):
            with servicios.motor.begin() as c:
                c.execute(text(sql))


def test_capa_personal_se_borra_pero_no_se_edita(carmen, servicios):
    with pytest.raises(DBAPIError):
        with servicios.motor.begin() as c:
            c.execute(text("update personal_versions set consent_given = false"))
    assert servicios.perfiles.borrar_personal("carmen-68") == 1


def test_claves_ajenas_activas(servicios):
    with pytest.raises(IntegrityError):
        with servicios.motor.begin() as c:
            c.execute(text("insert into sessions (session_id, client_id, channel, started_at) "
                           "values ('s-x', 'no-existe', 'voice', CURRENT_TIMESTAMP)"))


def test_otra_violacion_no_se_confunde_con_conflicto_de_version(servicios):
    from app.perfil.dominio.errores import ConflictoVersion
    from app.perfil.dominio.modelos import Perfil

    with pytest.raises(IntegrityError) as info:
        servicios.repo.insertar_version(Perfil(client_id="no-existe", version=2))  # viola la clave ajena
    assert not isinstance(info.value, ConflictoVersion)


# ---------- sesiones ----------

def test_sesion_crea_cliente_y_guarda_turnos_en_orden(servicios):
    s = servicios.sesiones.crear(canal="text")
    assert servicios.perfiles.perfil(s["client_id"]).status == EstadoPerfil.draft
    sid = s["session_id"]
    assert servicios.sesiones.anadir_turno(sid, Turno(speaker="agent", text="Hola, soy una IA")) == (0, True)
    assert servicios.sesiones.anadir_turno(sid, Turno(speaker="client", text="Hola", t_start=1, t_end=2)) == (1, True)
    detalle = servicios.sesiones.sesion(sid)
    assert detalle["channel"] == "text" and [t["text"] for t in detalle["turns"]] == ["Hola, soy una IA", "Hola"]


def test_reenviar_un_turno_no_lo_duplica(servicios):
    sid = servicios.sesiones.crear("c1")["session_id"]
    turno = Turno(turn_id="t-1", speaker="client", text="Hola")
    assert servicios.sesiones.anadir_turno(sid, turno) == (0, True)
    assert servicios.sesiones.anadir_turno(sid, turno) == (0, False)
    assert len(servicios.sesiones.turnos(sid)) == 1


def test_sesion_cerrada_no_admite_turnos(servicios):
    sid = servicios.sesiones.crear("c1")["session_id"]
    cerrada = servicios.sesiones.cerrar(sid, conversation_id="conv-123")
    assert cerrada["ended_at"] is not None and cerrada["conversation_id"] == "conv-123"
    with pytest.raises(EscrituraNoPermitida):
        servicios.sesiones.anadir_turno(sid, Turno(speaker="client", text="tarde"))


def test_errores_de_sesion(servicios):
    with pytest.raises(NoEncontrado):
        servicios.sesiones.sesion("s-nada")
    with pytest.raises(CampoInvalido):
        servicios.sesiones.crear(canal="paloma")


# ---------- eventos para el panel en vivo ----------

def test_eventos_de_cambios(servicios):
    servicios.perfiles.crear("c1")
    cola = servicios.bus.suscribir("c1")
    servicios.perfiles.cargar_fixture("carmen-68")  # no es c1: no debe llegar nada
    assert cola.empty()
    from app.perfil.dominio.modelos import AUTOR_EXTRACTOR, ActualizacionCampo, Evidencia, Fuente
    ev = [Evidencia(session_id="s", quote="no debo nada")]
    servicios.perfiles.aplicar("c1", [ActualizacionCampo(field="financial.debts_eur", value=0,
                                                         source=Fuente.declared, evidence=ev)], "x", AUTOR_EXTRACTOR)
    eventos = []
    while not cola.empty():
        eventos.append(cola.get_nowait())
    assert [e.tipo for e in eventos] == ["profile.patch", "profile.status"]
    assert eventos[0].datos["path"] == "financial.debts_eur" and eventos[0].version == 2


def test_bus_descarta_si_el_suscriptor_no_lee():
    bus = BusEventos(capacidad=1)
    cola = bus.suscribir("c")
    bus.publicar(Evento("profile.status", "c", 1))
    bus.publicar(Evento("profile.status", "c", 2))  # no bloquea ni falla
    assert cola.get_nowait().version == 1 and cola.empty()
    bus.cancelar("c", cola)
    bus.publicar(Evento("profile.status", "c", 3))
    assert cola.empty()
