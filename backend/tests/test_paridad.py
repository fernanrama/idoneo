"""El mismo recorrido produce exactamente el mismo resultado en memoria y en base de datos.

Es la prueba de que cambiar PERFIL_ALMACEN no cambia nada que vean el front, los agentes o el MCP.
"""

from __future__ import annotations

from app.perfil import calculos, store
from app.perfil.modelos import Alerta, Evidencia, Flag, Parche, Turno

C = "carmen-68"
EV = [Evidencia(session_id="s", turn_id="t-001", t=(1.0, 2.0), quote="q")]
VOLATILES = {"created_at", "updated_at", "confirmed_at", "validated_at", "resolved_at", "next_review",
             "started_at", "session_id"}


def _sin_volatiles(x):
    if isinstance(x, dict):
        return {k: _sin_volatiles(v) for k, v in x.items() if k not in VOLATILES}
    if isinstance(x, list):
        return [_sin_volatiles(v) for v in x]
    return x


def _recorrido() -> dict:
    store.reiniciar()
    store.cargar_fixture(C)
    store.aplicar(C, [Parche(path="knowledge.etfs", value="none", declared="high", source="demonstrated",
                             evidence=EV)], "extractor", "agent:extractor")
    store.anadir_alertas(C, [Alerta(id="a-p", path="objectives.o1.goal", flag=Flag.inconsistent, message="m")])
    store.guardar_personal(C, {"exclusions": ["tabaco"]}, True, "system")
    store.validar(C, "asesor-07", [Parche(path="financial.debts_eur", value=100, source="declared")])
    store.aplicar(C, [Parche(path="financial.debts_eur", value=200, source="declared", evidence=EV)],
                  "nuevo dato", "agent:extractor")
    s = store.crear_sesion(C)
    store.anadir_turno(s["session_id"], Turno(speaker="client", text="hola", t_start=0, t_end=1))
    store.cargar_fixture(C)  # reinicio de demo
    return _sin_volatiles({
        "perfil": store.perfil(C).model_dump(mode="json"),
        "consumidor": store.perfil_para_consumidor(C).model_dump(mode="json"),
        "restricciones": calculos.restricciones(store.perfil_para_consumidor(C)).model_dump(mode="json"),
        "versiones": [dict(v, status=v["status"].value) for v in store.versiones(C)],
        "v3": store.perfil(C, 3).model_dump(mode="json"),
        "turnos": [t.model_dump() for t in store.sesion(s["session_id"])["turns"]],
    })


def test_memoria_y_base_de_datos_dan_lo_mismo():
    store.configurar("memoria")
    en_memoria = _recorrido()
    store.configurar("bd", "sqlite://")
    en_bd = _recorrido()
    assert en_memoria == en_bd
    assert [v["reason"] for v in en_bd["versiones"]][-1].startswith("demo_reset")
