"""Sube el prompt del entrevistador (prompts/entrevistador.md) al agente de voz de ElevenLabs.

Así el prompt vive en un solo sitio, el repo: el modo texto y la voz dicen lo mismo y cada cambio queda
en git. Solo cambia el texto de las instrucciones del agente; la voz, el primer mensaje, el idioma, el
modelo y las herramientas se quedan como estén en el panel de ElevenLabs.

Uso (desde backend/, con ELEVENLABS_API_KEY y ELEVENLABS_AGENT_ID en ../.env):

    python scripts/sincronizar_voz.py            # solo compara: no cambia nada
    python scripts/sincronizar_voz.py --aplicar  # guarda una copia del prompt actual y sube el nuevo

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
COPIAS = RAIZ / "scripts" / ".copias_voz"  # ignorado por git: puede contener ajustes del panel


def principal(aplicar: bool) -> int:
    clave, agente = os.getenv("ELEVENLABS_API_KEY", "").strip(), os.getenv("ELEVENLABS_AGENT_ID", "").strip()
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
    sys.exit(principal(p.parse_args().aplicar))
