"""Finalizar la revisión del inversor (sesión) frente a validar el perfil MiFID (entidad).

Contrato: se ejecuta con cada almacén (memoria, SQLite y, si existe, Postgres local). Sin Claude ni
ElevenLabs: las escrituras simulan lo que haría el extractor. DATOS SIMULADOS: fixture carmen-68.
"""

from __future__ import annotations

import itertools

import pytest

from app.perfil import store
from app.perfil.modelos import EstadoPerfil, Evidencia, Parche

C = "carmen-68"
AHORRO, PLAZO = "financial.liquid_savings_eur", "objectives.o1.horizon_years"
_turnos = itertools.count(1)


def decir(ruta: str, valor, texto: str = "DATOS SIMULADOS"):
    f = store.perfil(C).mifid.get(ruta)
    misma = f is not None and f.value == valor
    p = Parche(path=ruta, value=valor, source=f.source if misma else "declared",
               confidence=f.confidence if misma else None,
               evidence=[Evidencia(session_id="s-cierre", turn_id=f"t-{next(_turnos):03d}", t=(1.0, 2.0), quote=texto)])
    return store.aplicar(C, [p], "extractor · s-cierre", "agent:extractor")


def huella(p):
    """Lo que no debe cambiar al cerrar: datos, evidencias, resultados, alertas y estado."""
    return ({r: (f.value, f.declared, len(f.evidence), f.confirmed_at) for r, f in p.mifid.items()},
            p.assessments.model_dump(), [(a.id, a.status) for a in p.alerts], p.status)


@pytest.fixture
def validada(carmen):
    return store.validar(C, "asesor-07", [])


# ---------- store.cerrar_revision ----------

def test_cerrar_no_toca_datos_ni_estado(validada):
    p = decir(AHORRO, 80000, "Los ahorros siguen igual")  # confirmación: sigue active
    c = store.cerrar_revision(C, "review_closed:sin_cambios", p.version)
    assert c.version == p.version + 1 and c.reason == "review_closed:sin_cambios" and c.author == "system"
    assert huella(c) == huella(p) and c.status == EstadoPerfil.active


def test_cerrar_con_cambios_no_reactiva(validada):
    p = decir(PLAZO, 1, "Lo necesitaré el año que viene")
    c = store.cerrar_revision(C, "review_closed:pendiente_de_validacion", p.version)
    assert c.status == EstadoPerfil.review_due and huella(c) == huella(p)
    assert store.revision_pendiente(C).paths == [PLAZO]  # GPTadvisor sigue avisado


def test_cerrar_con_version_obsoleta_no_escribe(validada):
    p = decir(AHORRO, 80000, "Los ahorros siguen igual")
    decir(PLAZO, 1, "Lo necesitaré el año que viene")  # otra respuesta se adelanta
    antes = store.versiones(C)
    with pytest.raises(store.Conflicto, match="ha cambiado"):
        store.cerrar_revision(C, "review_closed:sin_cambios", p.version)
    assert store.versiones(C) == antes


def test_cerrar_exige_motivo(validada):
    with pytest.raises(store.DatoInvalido):
        store.cerrar_revision(C, " ", validada.version)
