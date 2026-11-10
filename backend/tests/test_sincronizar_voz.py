"""Script que sube el prompt del entrevistador a ElevenLabs (sin red: transporte simulado)."""

import importlib.util
import json
from pathlib import Path

import httpx

RUTA = Path(__file__).resolve().parents[1] / "scripts" / "sincronizar_voz.py"


def cargar(monkeypatch, tmp_path, prompt_actual):
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_prueba")
    monkeypatch.setattr(m, "COPIAS", tmp_path)
    peticiones = []

    def responder(req: httpx.Request) -> httpx.Response:
        peticiones.append(req)
        assert req.headers["xi-api-key"] == "clave-de-prueba"
        if req.method == "GET":
            return httpx.Response(200, json={"name": "Entrevista", "conversation_config": {"agent": {
                "first_message": "Hola", "prompt": {"prompt": prompt_actual, "llm": "modelo-del-panel", "tool_ids": ["t1"]}}}})
        return httpx.Response(200, json={})

    real = httpx.Client
    monkeypatch.setattr(m.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(responder), **kw))
    return m, peticiones


def test_sin_aplicar_solo_compara(monkeypatch, tmp_path):
    m, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo")
    assert m.principal(aplicar=False) == 0
    assert [p.method for p in peticiones] == ["GET"]


def test_aplicar_cambia_solo_el_texto_y_guarda_copia(monkeypatch, tmp_path):
    m, peticiones = cargar(monkeypatch, tmp_path, "prompt viejo")
    assert m.principal(aplicar=True) == 0
    patch = peticiones[-1]
    assert patch.method == "PATCH" and patch.url.path == "/v1/convai/agents/agent_prueba"
    prompt = json.loads(patch.content)["conversation_config"]["agent"]["prompt"]
    assert prompt["prompt"] == m.chat._sistema().strip()
    assert prompt["llm"] == "modelo-del-panel" and prompt["tool_ids"] == ["t1"]
    copias = list(tmp_path.glob("*.json"))
    assert len(copias) == 1 and json.loads(copias[0].read_text("utf-8"))["prompt"] == "prompt viejo"


def test_al_dia_no_sube_nada(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("s", RUTA)
    s = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s)
    m, peticiones = cargar(monkeypatch, tmp_path, s.chat._sistema())
    assert m.principal(aplicar=True) == 0
    assert [p.method for p in peticiones] == ["GET"]


def test_crear_agente_en_espanol_con_nuestro_prompt(monkeypatch, tmp_path, capsys):
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    enviados = []

    def responder(req):
        enviados.append(req)
        return httpx.Response(200, json={"agent_id": "agent_nuevo"})

    real = httpx.Client
    monkeypatch.setattr(m.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(responder), **kw))
    assert m.principal(aplicar=False, nuevo_agente=True) == 0
    cuerpo = json.loads(enviados[0].content)
    agente = cuerpo["conversation_config"]["agent"]
    assert enviados[0].url.path == "/v1/convai/agents/create"
    assert agente["language"] == "es" and "inteligencia artificial" in agente["first_message"]
    assert agente["prompt"]["prompt"] == m.chat._sistema().strip()
    assert "ELEVENLABS_AGENT_ID=agent_nuevo" in capsys.readouterr().out


def test_no_crea_un_segundo_agente(monkeypatch):
    spec = importlib.util.spec_from_file_location("sincronizar_voz", RUTA)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_ya")
    assert m.principal(aplicar=False, nuevo_agente=True) == 2
