"""Sube el prompt del entrevistador (prompts/entrevistador.md) al agente de voz de ElevenLabs.

Así el prompt vive en un solo sitio, el repo: el modo texto y la voz dicen lo mismo y cada cambio queda
en git. Solo cambia el texto de las instrucciones del agente; la voz, el primer mensaje, el idioma, el
modelo y las herramientas se quedan como estén en el panel de ElevenLabs.

Uso (desde backend/, con ELEVENLABS_API_KEY y ELEVENLABS_AGENT_ID en ../.env):

    python scripts/sincronizar_voz.py            # solo compara: no cambia nada
    python scripts/sincronizar_voz.py --aplicar  # guarda una copia del prompt actual y sube el nuevo
    python scripts/sincronizar_voz.py --crear    # crea el agente (si aún no existe) y escribe su ID

`--crear` solo necesita ELEVENLABS_API_KEY: crea el agente en español con nuestro prompt y un primer
mensaje con el aviso de IA, y te da el ID para el .env. La voz se elige luego en el panel.

API usada (SDK oficial `elevenlabs`, conversational_ai.agents): GET y PATCH /v1/convai/agents/{agent_id},
con el prompt en conversation_config.agent.prompt.prompt. Se lee el objeto `prompt` actual y se devuelve
entero con solo el texto cambiado, para no tocar el resto de su configuración.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
load_dotenv(RAIZ.parent / ".env")
load_dotenv(RAIZ / ".env")

from app.agentes import chat  # noqa: E402

API = "https://api.elevenlabs.io/v1/convai/agents/{agente}"
API_CREAR = "https://api.elevenlabs.io/v1/convai/agents/create"
NOMBRE = "Idóneo – entrevista"
# El primer mensaje lo dice el agente al conectar: aviso de IA, revisión humana, propósito y consentimiento.
PRIMER_MENSAJE = ("Hola, soy el asistente de perfil inversor del banco. Soy una inteligencia artificial y una "
                  "persona del banco revisará todo. Le haré unas preguntas para conocer su situación antes de "
                  "ofrecerle productos de inversión. ¿Le parece bien que grabemos la conversación?")
# Un agente que no habla inglés necesita un modelo de voz multilingüe (los «v2_5»).
MODELO_VOZ = "eleven_flash_v2_5"


def crear(clave: str) -> int:
    if os.getenv("ELEVENLABS_AGENT_ID", "").strip():
        print("Ya hay un ELEVENLABS_AGENT_ID en el .env: no creo otro. Usa el script sin --crear para sincronizar.")
        return 2
    cuerpo = {
        "name": NOMBRE,
        "conversation_config": {
            "agent": {"language": "es", "first_message": PRIMER_MENSAJE, "prompt": {"prompt": chat._sistema().strip()}},
            "tts": {"model_id": MODELO_VOZ},
        },
    }
    with httpx.Client(timeout=30) as http:
        r = http.post(API_CREAR, headers={"xi-api-key": clave}, json=cuerpo)
    if r.status_code != 200:
        print(f"ElevenLabs respondió {r.status_code} al crear el agente: {r.text[:400]}")
        return 1
    agente = r.json()["agent_id"]
    print(f"Agente creado: {NOMBRE}\nAñade esta línea al .env:\n\nELEVENLABS_AGENT_ID={agente}\n")
    print("Después elige la voz en el panel de ElevenLabs (Agents → el agente → Voice).")
    return 0


COPIAS = RAIZ / "scripts" / ".copias_voz"  # ignorado por git: puede contener ajustes del panel


def principal(aplicar: bool, nuevo_agente: bool = False) -> int:
    clave, agente = os.getenv("ELEVENLABS_API_KEY", "").strip(), os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    if nuevo_agente:
        if not clave:
            print("Falta ELEVENLABS_API_KEY en el .env.")
            return 2
        return crear(clave)
    if not clave or not agente:
        print("Faltan ELEVENLABS_API_KEY y/o ELEVENLABS_AGENT_ID en el .env.")
        return 2
    url, cabeceras = API.format(agente=agente), {"xi-api-key": clave}
    with httpx.Client(timeout=20) as http:
        r = http.get(url, headers=cabeceras)
        if r.status_code != 200:
            print(f"ElevenLabs respondió {r.status_code} al leer el agente: {r.text[:300]}")
            return 1
        datos = r.json()
        prompt = ((datos.get("conversation_config") or {}).get("agent") or {}).get("prompt") or {}
        actual, nuevo = (prompt.get("prompt") or "").strip(), chat._sistema().strip()
        print(f"Agente: {datos.get('name', '?')} ({agente})")
        if actual == nuevo:
            print("El prompt ya está al día. Nada que hacer.")
            return 0
        diff = list(difflib.unified_diff(actual.splitlines(), nuevo.splitlines(), "ElevenLabs", "repo", lineterm="", n=1))
        print("\n".join(diff[:120]) + ("\n…" if len(diff) > 120 else ""))
        if not aplicar:
            print("\nSolo comparación. Para subirlo: python scripts/sincronizar_voz.py --aplicar")
            return 0

        COPIAS.mkdir(exist_ok=True)
        copia = COPIAS / f"{agente}-{datetime.now():%Y%m%d-%H%M%S}.json"
        copia.write_text(json.dumps(prompt, ensure_ascii=False, indent=2), encoding="utf-8")
        cuerpo = {"conversation_config": {"agent": {"prompt": {**prompt, "prompt": nuevo}}}}
        r = http.patch(url, headers=cabeceras, json=cuerpo)
        if r.status_code != 200:
            print(f"ElevenLabs respondió {r.status_code} al actualizar: {r.text[:300]}")
            return 1
    print(f"\nPrompt subido. Copia del anterior en {copia}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--aplicar", action="store_true", help="sube el prompt (sin esto solo compara)")
    p.add_argument("--crear", action="store_true", help="crea el agente de voz si aún no existe")
    a = p.parse_args()
    sys.exit(principal(a.aplicar, a.crear))
