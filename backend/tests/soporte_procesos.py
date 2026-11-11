"""Trabajo de cada proceso en test_concurrencia_procesos.py (se importa en procesos hijos con `spawn`).

Cada hijo crea su propio almacén (motor y pool propios), como dos backends distintos sobre la misma base.
Sin red: el hijo hereda PYTHONPATH con tests/aislamiento y arranca con claves vacías y red bloqueada.
"""

from __future__ import annotations

CLIENTE_FIXTURE = "carmen-68"  # DATOS SIMULADOS
CLIENTE = "c-concurrencia-test"
TURNOS_POR_PROCESO = 10
VERSIONES_POR_PROCESO = 8


def _error(e: BaseException) -> str:
    return f"{type(e).__name__}: {str(e).splitlines()[0][:120] if str(e) else ''}"


def ejecutar(url: str, quien: int, sesion: str, barrera, cola) -> None:
    resultados: dict = {}
    try:
        from app.perfil import store
        from app.perfil.modelos import Evidencia, Parche, Turno

        store.configurar("bd", url)

        barrera.wait(60)  # 1. dos asesores validan a la vez
        try:
            resultados["validar"] = ("validado", store.validar(CLIENTE_FIXTURE, f"asesor-{quien}").version)
        except store.Conflicto as e:
            resultados["validar"] = ("conflicto", _error(e))

        barrera.wait(60)  # 2. dos guardados de memoria sobre la misma revisión vista (0)
        try:
            capa = store.actualizar_personal(CLIENTE, {"communication": {"pace": ("slow", "fast")[quien]}}, [],
                                             "agent:memory", version_esperada=0, consentimiento=True)
            resultados["memoria"] = ("confirmada", capa.version)
        except store.RevisionObsoleta:
            resultados["memoria"] = ("obsoleta", None)

        barrera.wait(60)  # 3. turnos a la vez en la misma sesión
        errores = []
        for i in range(TURNOS_POR_PROCESO):
            try:
                store.anadir_turno(sesion, Turno(speaker="client", text=f"p{quien}-{i}",
                                                 t_start=float(i), t_end=float(i) + 0.5))
            except Exception as e:  # noqa: BLE001 - se informa al test
                errores.append(_error(e))
        resultados["turnos"] = errores

        barrera.wait(60)  # 4. versiones a la vez en el mismo cliente
        ev = [Evidencia(session_id="s-1", turn_id="t-001", t=(1.0, 2.0), quote="DATOS SIMULADOS")]
        confirmadas, conflictos, otros = 0, 0, []
        for i in range(VERSIONES_POR_PROCESO):
            try:
                store.aplicar(CLIENTE, [Parche(path="financial.debts_eur", value=quien * 1000 + i,
                                               source="declared", evidence=ev)],
                              f"concurrencia {quien}-{i}", "agent:extractor")
                confirmadas += 1
            except store.Conflicto:
                conflictos += 1  # 409 tras agotar los reintentos: no se escribe nada
            except Exception as e:  # noqa: BLE001
                otros.append(_error(e))
        resultados["versiones"] = (confirmadas, conflictos, otros)
        store.configurar("memoria")
    except BaseException as e:  # noqa: BLE001 - cualquier fallo llega al test con su motivo
        resultados["fallo"] = _error(e)
    cola.put((quien, resultados))
