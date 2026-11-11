"""La clave de Anthropic se usa limpia, aunque la variable de entorno traiga espacios o un salto de línea.

Con la clave tal cual, la cabecera HTTP es inválida y el SDK devuelve APIConnectionError en cada llamada
(visto en producción el 11/11/2026). Sin red: solo se construye el cliente.
"""
import pytest

from app.agentes import claude


@pytest.fixture
def sin_cliente(monkeypatch):
    monkeypatch.setattr(claude, "_cliente", None)
    yield
    claude._cliente = None


@pytest.mark.parametrize("sucia", ["sk-ant-ficticia-de-prueba\n", "  sk-ant-ficticia-de-prueba \r\n", "\tsk-ant-ficticia-de-prueba"])
def test_la_clave_se_pasa_limpia_al_sdk(monkeypatch, sin_cliente, sucia):
    monkeypatch.setenv("ANTHROPIC_API_KEY", sucia)
    assert claude._cliente_async().api_key == "sk-ant-ficticia-de-prueba"


def test_sin_clave_no_se_crea_el_cliente(monkeypatch, sin_cliente):
    monkeypatch.setenv("ANTHROPIC_API_KEY", " \n")
    with pytest.raises(claude.ClaudeNoDisponible):
        claude._cliente_async()


@pytest.mark.parametrize("pegada", ["sk-ant-ficticia-de-prueba\nMODEL_VERIFICADOR=claude-opus-5-5","sk-ant-ficticia de-prueba"])
def test_una_clave_con_varias_lineas_se_rechaza_sin_mostrarla(monkeypatch, sin_cliente, pegada):
    """Varias líneas del .env pegadas en el valor (visto en producción): error claro y la clave no aparece."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", pegada)
    with pytest.raises(claude.ClaudeNoDisponible) as e:
        claude._cliente_async()
    assert "mal formada" in str(e.value)
    assert "ficticia" not in str(e.value)
    assert claude._cliente is None
