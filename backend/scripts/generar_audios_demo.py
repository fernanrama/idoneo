"""Graba con ElevenLabs las voces de la demo guiada (entrevistador y Carmen) y las deja en el front.

La demo guiada repite siempre la misma entrevista simulada (frontend/src/lib/guion-carmen.json), así que
sus audios se generan una vez y se suben al repo: en la demo no se gasta ni un crédito. Si un turno no
tiene audio, el front usa la voz del navegador como respaldo.

Uso (desde backend/, con ELEVENLABS_API_KEY en ../.env):

    python scripts/generar_audios_demo.py                       # solo cuenta: qué falta y cuántos caracteres
    python scripts/generar_audios_demo.py --voz-carmen ID --aplicar
    python scripts/generar_audios_demo.py --voz-carmen ID --aplicar --forzar   # regraba todo

- La voz del entrevistador es la del agente de voz (ELEVENLABS_AGENT_ID), para que suene igual que en la
  entrevista real. Se puede cambiar con --voz-entrevistador ID.
- La voz de Carmen se elige en la biblioteca de voces de ElevenLabs (una mujer mayor, castellano de España)
  y se pasa con --voz-carmen ID o ELEVENLABS_VOZ_CARMEN en el .env.
- La clave necesita el permiso «Text to Speech» (y leer agentes, si no se pasa --voz-entrevistador).
- Coste aproximado: un crédito por carácter con eleven_multilingual_v2. El guion completo ronda los
  1.700 caracteres. Solo se regraban los turnos cuyo texto o voz han cambiado.

Salida: frontend/public/demo/carmen/NN-agent.mp3 / NN-client.mp3 y manifest.json, que el front lee para saber
qué turnos tienen audio y que el texto coincide.

API: POST /v1/text-to-speech/{voice_id}?output_format=mp3_44100_128 con {text, model_id, voice_settings};
GET /v1/convai/agents/{agent_id} para leer conversation_config.tts.voice_id.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ.parent / ".env")
load_dotenv(RAIZ / ".env")

GUION = RAIZ.parent / "frontend" / "src" / "lib" / "guion-carmen.json"
SALIDA = RAIZ.parent / "frontend" / "public" / "demo" / "carmen"
API_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voz}"
API_AGENTE = "https://api.elevenlabs.io/v1/convai/agents/{agente}"
MODELO = "eleven_multilingual_v2"
AJUSTES = {
    # El entrevistador, sereno y claro; Carmen, algo más expresiva.
    "agent": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True},
    "client": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True},
}


def voz_del_agente(http: httpx.Client, clave: str) -> str | None:
    agente = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    if not agente:
        return None
    r = http.get(API_AGENTE.format(agente=agente), headers={"xi-api-key": clave})
    if r.status_code != 200:
        print(f"No he podido leer el agente ({r.status_code}): {r.text[:200]}")
        return None
    return ((r.json().get("conversation_config") or {}).get("tts") or {}).get("voice_id")


def principal() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--voz-carmen", default=os.getenv("ELEVENLABS_VOZ_CARMEN", "").strip())
    ap.add_argument("--voz-entrevistador", default=os.getenv("ELEVENLABS_VOZ_ENTREVISTADOR", "").strip())
    ap.add_argument("--aplicar", action="store_true", help="genera los audios (gasta créditos)")
    ap.add_argument("--forzar", action="store_true", help="regraba también los que ya existen")
    a = ap.parse_args()

    clave = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not clave:
        print("Falta ELEVENLABS_API_KEY en el .env.")
        return 2
    turnos = json.loads(GUION.read_text(encoding="utf-8"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_manifiesto = SALIDA / "manifest.json"
    manifiesto = json.loads(ruta_manifiesto.read_text(encoding="utf-8")) if ruta_manifiesto.exists() else {"turnos": {}}

    with httpx.Client(timeout=60) as http:
        voces = {"agent": a.voz_entrevistador or voz_del_agente(http, clave), "client": a.voz_carmen}
        if not voces["agent"]:
            print("No sé qué voz usar para el entrevistador: pon ELEVENLABS_AGENT_ID o --voz-entrevistador ID.")
            return 2
        if not voces["client"]:
            print("Falta la voz de Carmen: elige una en la biblioteca de ElevenLabs y pásala con --voz-carmen ID.")
            return 2

        pendientes = []
        for i, t in enumerate(turnos):
            nombre = f"{i:02d}-{t['speaker']}.mp3"
            previo = manifiesto["turnos"].get(str(i))
            al_dia = previo and previo["texto"] == t["text"] and previo["voz"] == voces[t["speaker"]] and (SALIDA / nombre).exists()
            if a.forzar or not al_dia:
                pendientes.append((i, t, nombre))
        caracteres = sum(len(t["text"]) for _, t, _ in pendientes)
        print(f"Turnos: {len(turnos)} · por grabar: {len(pendientes)} · unos {caracteres} caracteres (≈ créditos).")
        if not pendientes:
            print("Todo al día. Nada que hacer.")
            return 0
        if not a.aplicar:
            print("Solo cuenta. Para grabarlos: añade --aplicar")
            return 0

        for i, t, nombre in pendientes:
            cuerpo = {"text": t["text"], "model_id": MODELO, "voice_settings": AJUSTES[t["speaker"]]}
            r = http.post(
                API_TTS.format(voz=voces[t["speaker"]]),
                params={"output_format": "mp3_44100_128"},
                headers={"xi-api-key": clave, "Content-Type": "application/json"},
                json=cuerpo,
            )
            if r.status_code != 200:
                print(f"Turno {i}: ElevenLabs respondió {r.status_code}: {r.text[:300]}")
                if r.status_code in (401, 403):
                    print("Revisa que la clave tenga el permiso «Text to Speech».")
                return 1
            (SALIDA / nombre).write_bytes(r.content)
            manifiesto["turnos"][str(i)] = {"archivo": nombre, "texto": t["text"], "voz": voces[t["speaker"]]}
            ruta_manifiesto.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  {nombre}  ({len(t['text'])} caracteres)")
    print(f"Listo. Audios en {SALIDA.relative_to(RAIZ.parent)}. Súbelos al repo con git add frontend/public/demo.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
