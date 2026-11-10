"""Bootstrap de ElevenLabs y webhook post-llamada, todo con red simulada."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import httpx
from fastapi.testclient import TestClient

from app import voz
from app.main import app
from app.perfil import store


def firma(raw: bytes, secreto: str, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    digest = hmac.new(secreto.encode(), str(timestamp).encode() + b"." + raw, hashlib.sha256).hexdigest()
    return f"t={timestamp},v0={digest}"


def evento(session_id: str, conversation_id: str = "conv_prueba") -> bytes:
    return json.dumps({
        "type": "post_call_transcription",
        "data": {
            "conversation_id": conversation_id,
            "conversation_initiation_client_data": {"dynamic_variables": {"session_id": session_id}},
            "transcript": [{"role": "user", "message": "dato que no debe convertirse en memoria"}],
        },
    }, separators=(",", ":")).encode()


def test_bootstrap_incluye_url_contexto_y_user_id_opaco(monkeypatch):
    api = TestClient(app)
    sesion = api.post("/api/sessions", json={}).json()
    monkeypatch.setenv("ELEVENLABS_API_KEY", "clave")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agente")
    monkeypatch.setenv("VOICE_USER_ID_SECRET", "secreto")

    def responder(req: httpx.Request) -> httpx.Response:
        assert req.headers["xi-api-key"] == "clave" and req.url.params["agent_id"] == "agente"
        return httpx.Response(200, json={"signed_url": "wss://elevenlabs.test/signed"})

    real = httpx.AsyncClient
    monkeypatch.setattr(voz.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(responder), **kw))
    r = api.post("/api/voice/bootstrap", json={"session_id": sesion["session_id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["signed_url"].startswith("wss://")
    assert body["user_id"].startswith("usr_") and sesion["client_id"] not in body["user_id"]
    assert body["dynamic_variables"]["session_id"] == sesion["session_id"]
    assert "client_id" not in body["dynamic_variables"]


def test_bootstrap_sin_claves_falla_pero_contexto_publico_funciona(monkeypatch):
    api = TestClient(app)
    sesion = api.post("/api/sessions", json={}).json()
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    assert api.post("/api/voice/bootstrap", json={"session_id": sesion["session_id"]}).status_code == 503
    assert api.get(f"/api/voice/context/{sesion['session_id']}").status_code == 200


def test_webhook_firmado_cierra_sesion_y_es_idempotente(monkeypatch):
    api = TestClient(app)
    sesion = api.post("/api/sessions", json={}).json()
    secreto = "webhook-secret"
    monkeypatch.setenv("ELEVENLABS_WEBHOOK_SECRET", secreto)
    raw = evento(sesion["session_id"])
    headers = {"Content-Type": "application/json", "ElevenLabs-Signature": firma(raw, secreto)}

    r = api.post("/api/webhooks/elevenlabs", content=raw, headers=headers)
    assert r.status_code == 200 and r.json()["processed"] is True
    estado = store.sesion(sesion["session_id"])
    assert estado["conversation_id"] == "conv_prueba" and estado["ended_at"] is not None
    assert store.personal(sesion["client_id"]) is None  # la transcripción no se memoriza

    r = api.post("/api/webhooks/elevenlabs", content=raw, headers=headers)
    assert r.status_code == 200 and r.json()["processed"] is False
    assert api.post(f"/api/sessions/{sesion['session_id']}/turns", json={
        "speaker": "client", "text": "tarde", "t_start": 1, "t_end": 2,
    }).status_code == 409


def test_webhook_rechaza_firma_invalida_antigua_y_conflicto(monkeypatch):
    api = TestClient(app)
    sesion = api.post("/api/sessions", json={}).json()
    secreto = "webhook-secret"
    monkeypatch.setenv("ELEVENLABS_WEBHOOK_SECRET", secreto)
    raw = evento(sesion["session_id"])
    assert api.post("/api/webhooks/elevenlabs", content=raw, headers={
        "ElevenLabs-Signature": "t=1,v0=falsa", "Content-Type": "application/json",
    }).status_code == 401
    assert api.post("/api/webhooks/elevenlabs", content=raw, headers={
        "ElevenLabs-Signature": firma(raw, secreto, int(time.time()) - voz.MAX_WEBHOOK_AGE_S - 1),
        "Content-Type": "application/json",
    }).status_code == 401

    headers = {"ElevenLabs-Signature": firma(raw, secreto), "Content-Type": "application/json"}
    assert api.post("/api/webhooks/elevenlabs", content=raw, headers=headers).status_code == 200
    otro = evento(sesion["session_id"], "conv_distinta")
    assert api.post("/api/webhooks/elevenlabs", content=otro, headers={
        "ElevenLabs-Signature": firma(otro, secreto), "Content-Type": "application/json",
    }).status_code == 409


def test_webhook_limita_el_cuerpo_antes_de_verificarlo(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_WEBHOOK_SECRET", "secreto")
    raw = b"x" * (voz.MAX_WEBHOOK_BYTES + 1)
    r = TestClient(app).post("/api/webhooks/elevenlabs", content=raw, headers={
        "ElevenLabs-Signature": "t=1,v0=no-importa", "Content-Type": "application/json",
    })
    assert r.status_code == 413
