"""Compatibilidad del verificador actual (stub de Pablo, app/agentes/verificador.py) con el perfil nuevo.

Hallazgo: el verificador importa `Alerta` y `Evidencia` del modelo v0 (app/perfil/modelos.py) y
construye sus alertas con las evidencias del perfil. Con el perfil nuevo, Pydantic rechaza esas
evidencias porque son de otra clase. Al cambiar la API al núcleo nuevo hay que cambiar su import a
`app.perfil.dominio.modelos` (fichero de Pablo: pedírselo, no tocarlo).

El test está marcado como fallo esperado y estricto: cuando se actualice el import pasará, y pytest
avisará para quitar la marca.
"""

from __future__ import annotations

import asyncio

import pytest

from app.agentes import verificador
from app.perfil.dominio.modelos import AUTOR_EXTRACTOR, ActualizacionCampo, Alerta, Evidencia, Fuente


@pytest.mark.xfail(strict=True, reason="verificador.py usa los modelos v0; hay que actualizar su import")
def test_verificador_con_perfil_nuevo(servicios):
    servicios.perfiles.crear("c1")
    ev = [Evidencia(session_id="s", t=(1, 2), quote="eso no puede pasar")]
    p = servicios.perfiles.aplicar("c1", [ActualizacionCampo(
        field="knowledge.equity_funds", value="none", declared="high", source=Fuente.demonstrated,
        confidence=1.0, evidence=ev)], "x", AUTOR_EXTRACTOR)

    alertas = asyncio.run(verificador.verificar(p, []))
    assert [(a.type, a.field) for a in alertas] == [("declared_vs_demonstrated", "knowledge.equity_funds")]
    p = servicios.perfiles.anadir_alertas("c1", [Alerta.model_validate(a.model_dump()) for a in alertas])
    assert len(p.alertas_abiertas()) == 1
