"""Pruebas del sincronizador de ElevenLabs con un transporte HTTP simulado."""

import importlib.util
import json
from pathlib import Path

import httpx

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "sincronizar_voz.py"
COLGAR_PUESTO = {"end_call": {"name": "end_call", "params": {"system_tool_type": "end_call"}}}


def cargar(
    monkeypatch,
    tmp_path,
    prompt_actual,
    placeholders=None,
    herramientas=None,
    tool_ids=("t1",),
    integradas=COLGAR_PUESTO,
):
    herramientas = (
        [{"id": "t1", "tool_config": {"name": "datos_pendientes"}}]
        if herramientas is None else herramientas
    )
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_prueba")
    monkeypatch.setattr(modulo, "COPIAS", tmp_path)
    peticiones = []

    def responder(req: httpx.Request) -> httpx.Response:
        peticiones.append(req)
        assert req.headers["xi-api-key"] == "clave-de-prueba"
        if req.url.path == "/v1/convai/tools":
            if req.method == "POST":
                return httpx.Response(200, json={"id": "t-nueva"})
            return httpx.Response(200, json={"tools": herramientas, "has_more": False})
        if req.method == "GET":
            return httpx.Response(200, json={"name": "Entrevista", "conversation_config": {"agent": {
                "first_message": "Hola",
                "prompt": {
                    "prompt": prompt_actual,
                    "llm": "modelo-del-panel",
                    "tool_ids": list(tool_ids),
                    "tools": [{"name": "vieja"}],
                    "built_in_tools": integradas,
                },
                "dynamic_variables": {
                    "dynamic_variable_placeholders": placeholders or {"variable_panel": "se conserva"},
                    "otra_configuracion": "se conserva",
                },
            }}})
        return httpx.Response(200, json={})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        modulo.httpx,
        "Client",
        lambda **kwargs: cliente_real(transport=httpx.MockTransport(responder), **kwargs),
    )
    return modulo, peticiones


def test_sin_aplicar_solo_compara(monkeypatch, tmp_path):
    modulo, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo")
    assert modulo.principal(aplicar=False) == 0
    assert all(p.method == "GET" for p in peticiones)


def test_aplicar_sincroniza_todo_y_guarda_copia(monkeypatch, tmp_path):
    modulo, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo")
    assert modulo.principal(aplicar=True) == 0
    patch = peticiones[-1]
    assert patch.method == "PATCH" and patch.url.path == "/v1/convai/agents/agent_prueba"
    agente = json.loads(patch.content)["conversation_config"]["agent"]
    prompt = agente["prompt"]
    assert prompt["prompt"] == modulo.chat.sistema_voz().strip()
    assert prompt["llm"] == "modelo-del-panel"
    assert prompt["tool_ids"] == ["t1"] and "tools" not in prompt
    assert prompt["built_in_tools"] == COLGAR_PUESTO
    assert agente["dynamic_variables"]["dynamic_variable_placeholders"] == {
        "variable_panel": "se conserva",
        **modulo.PLACEHOLDERS,
    }
    assert agente["dynamic_variables"]["otra_configuracion"] == "se conserva"
    copias = list(tmp_path.glob("*.json"))
    copia = json.loads(copias[0].read_text("utf-8"))
    assert len(copias) == 1 and copia["prompt"]["prompt"] == "prompt viejo"
    assert copia["dynamic_variables"]["otra_configuracion"] == "se conserva"


def test_al_dia_no_sube_nada(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("s", RUTA)
    referencia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referencia)
    modulo, peticiones = cargar(
        monkeypatch, tmp_path, referencia.chat.sistema_voz(), referencia.PLACEHOLDERS
    )
    assert modulo.principal(aplicar=True) == 0
    assert all(p.method == "GET" for p in peticiones)


def test_crea_y_engancha_la_herramienta_si_falta(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("s", RUTA)
    referencia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(referencia)
    modulo, peticiones = cargar(
        monkeypatch, tmp_path, referencia.chat.sistema_voz(), referencia.PLACEHOLDERS,
        herramientas=[], tool_ids=("otra",),
    )
    assert modulo.principal(aplicar=True) == 0
    creadas = [p for p in peticiones if p.method == "POST"]
    assert len(creadas) == 1
    assert json.loads(creadas[0].content)["tool_config"]["name"] == "datos_pendientes"
    prompt = json.loads(peticiones[-1].content)["conversation_config"]["agent"]["prompt"]
    assert prompt["tool_ids"] == ["otra", "t-nueva"]


def test_herramienta_existente_pero_sin_enganchar(monkeypatch, tmp_path):
    modulo, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo", tool_ids=())
    assert modulo.principal(aplicar=True) == 0
    assert not [p for p in peticiones if p.method == "POST"]
    prompt = json.loads(peticiones[-1].content)["conversation_config"]["agent"]["prompt"]
    assert prompt["tool_ids"] == ["t1"]


def test_engancha_colgar_si_falta_y_respeta_las_demas(monkeypatch, tmp_path):
    otras = {"language_detection": {"name": "language_detection"}}
    modulo, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo", integradas=otras)
    assert modulo.principal(aplicar=True) == 0
    integradas = json.loads(peticiones[-1].content)["conversation_config"]["agent"]["prompt"]["built_in_tools"]
    assert integradas["end_call"]["params"]["system_tool_type"] == "end_call"
    assert integradas["language_detection"] == {"name": "language_detection"}


def test_crear_agente_en_espanol_con_prompt_memoria_y_herramientas(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    enviados = []

    def responder(req):
        enviados.append(req)
        if req.url.path == "/v1/convai/tools":
            return httpx.Response(200, json={"tools": [{"id": "t1", "tool_config": {"name": "datos_pendientes"}}]})
        return httpx.Response(200, json={"agent_id": "agent_nuevo"})

    cliente_real = httpx.Client
    monkeypatch.setattr(
        modulo.httpx, "Client",
        lambda **kwargs: cliente_real(transport=httpx.MockTransport(responder), **kwargs),
    )
    assert modulo.principal(aplicar=False, nuevo_agente=True) == 0
    cuerpo = json.loads(enviados[-1].content)
    agente = cuerpo["conversation_config"]["agent"]
    assert enviados[-1].url.path == "/v1/convai/agents/create"
    assert agente["language"] == "es" and "inteligencia artificial" in agente["first_message"]
    assert agente["prompt"]["prompt"] == modulo.chat.sistema_voz().strip()
    assert agente["prompt"]["tool_ids"] == ["t1"]
    assert agente["prompt"]["built_in_tools"]["end_call"] == modulo.COLGAR
    assert agente["dynamic_variables"]["dynamic_variable_placeholders"] == modulo.PLACEHOLDERS
    assert "ELEVENLABS_AGENT_ID=agent_nuevo" in capsys.readouterr().out


def test_no_crea_un_segundo_agente(monkeypatch):
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_ya")
    assert modulo.principal(aplicar=False, nuevo_agente=True) == 2
