"""Sube el prompt del entrevistador (prompts/entrevistador.md) al agente de voz de ElevenLabs.

Así el prompt vive en un solo sitio, el repo: el modo texto y la voz dicen lo mismo y cada cambio queda
en git. Cambia el texto de las instrucciones del agente y se asegura de que tenga la herramienta
`datos_pendientes` (la crea en el workspace si no existe); la voz, el primer mensaje, el idioma, el modelo
y el resto de herramientas se quedan como estén en el panel de ElevenLabs.

`datos_pendientes` es una herramienta de cliente: cuando el agente la llama, el navegador (frontend,
useEntrevista.ts) pide GET /api/sessions/{id}/pending al backend y le devuelve qué falta por preguntar.

Uso (desde backend/, con ELEVENLABS_API_KEY y ELEVENLABS_AGENT_ID en ../.env):

    python scripts/sincronizar_voz.py            # solo compara: no cambia nada
    python scripts/sincronizar_voz.py --aplicar  # guarda una copia del prompt actual y sube el nuevo
    python scripts/sincronizar_voz.py --crear    # crea el agente (si aún no existe) y escribe su ID

`--crear` solo necesita ELEVENLABS_API_KEY: crea el agente en español con nuestro prompt y un primer
mensaje con el aviso de IA, y te da el ID para el .env. La voz se elige luego en el panel.

API usada (SDK oficial `elevenlabs` 2.77, conversational_ai.agents y .tools): GET y PATCH
/v1/convai/agents/{agent_id}, con el prompt en conversation_config.agent.prompt.prompt y las herramientas
en .prompt.tool_ids; GET y POST /v1/convai/tools. Se lee el objeto `prompt` actual y se devuelve entero
con solo el texto y la lista de herramientas cambiados, para no tocar el resto de su configuración.
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
API_HERRAMIENTAS = "https://api.elevenlabs.io/v1/convai/tools"
NOMBRE = "Idóneo – entrevista"
# El primer mensaje lo dice el agente al conectar: aviso de IA, revisión humana, propósito y consentimiento.
PRIMER_MENSAJE = ("Hola, soy el asistente de perfil inversor del banco. Soy una inteligencia artificial y una "
                  "persona del banco revisará todo. Le haré unas preguntas para conocer su situación antes de "
                  "ofrecerle productos de inversión. ¿Le parece bien que grabemos la conversación?")
# Un agente que no habla inglés necesita un modelo de voz multilingüe (los «v2_5»).
MODELO_VOZ = "eleven_flash_v2_5"
HERRAMIENTA = {
    "type": "client",
    "name": "datos_pendientes",
    "description": ("Devuelve qué datos del perfil faltan, cuáles conviene volver a preguntar y qué conocimientos "
                    "falta comprobar. Llámala al terminar cada bloque del guion y siempre antes de despedirte."),
    "expects_response": True,
    "response_timeout_secs": 10,
}


class ErrorElevenLabs(Exception):
    pass


def herramienta(http: httpx.Client, cabeceras: dict, crear_si_falta: bool) -> str | None:
    """ID de `datos_pendientes` en el workspace; la crea si falta y se pide."""
    r = http.get(API_HERRAMIENTAS, headers=cabeceras, params={"search": HERRAMIENTA["name"]})
    if r.status_code != 200:
        raise ErrorElevenLabs(f"ElevenLabs respondió {r.status_code} al listar herramientas: {r.text[:300]}")
    for t in r.json().get("tools", []):
        if (t.get("tool_config") or {}).get("name") == HERRAMIENTA["name"]:
            return t["id"]
    if not crear_si_falta:
        return None
    r = http.post(API_HERRAMIENTAS, headers=cabeceras, json={"tool_config": HERRAMIENTA})
    if r.status_code != 200:
        raise ErrorElevenLabs(f"ElevenLabs respondió {r.status_code} al crear la herramienta: {r.text[:300]}")
    print(f"Herramienta {HERRAMIENTA['name']} creada en el workspace.")
    return r.json()["id"]


def crear(clave: str) -> int:
    if os.getenv("ELEVENLABS_AGENT_ID", "").strip():
        print("Ya hay un ELEVENLABS_AGENT_ID en el .env: no creo otro. Usa el script sin --crear para sincronizar.")
        return 2
    with httpx.Client(timeout=30) as http:
        cabeceras = {"xi-api-key": clave}
        id_herramienta = herramienta(http, cabeceras, crear_si_falta=True)
        cuerpo = {
            "name": NOMBRE,
            "conversation_config": {
                "agent": {"language": "es", "first_message": PRIMER_MENSAJE,
                          "prompt": {"prompt": chat._sistema().strip(), "tool_ids": [id_herramienta]}},
                "tts": {"model_id": MODELO_VOZ},
            },
        }
        r = http.post(API_CREAR, headers=cabeceras, json=cuerpo)
    if r.status_code != 200:
        print(f"ElevenLabs respondió {r.status_code} al crear el agente: {r.text[:400]}")
        return 1
    agente = r.json()["agent_id"]
    print(f"Agente creado: {NOMBRE}\nAñade esta línea al .env:\n\nELEVENLABS_AGENT_ID={agente}\n")
    print("Después elige la voz en el panel de ElevenLabs (Agents → el agente → Voice).")
    return 0


COPIAS = RAIZ / "scripts" / ".copias_voz"  # ignorado por git: puede contener ajustes del panel


def principal(aplicar: bool, nuevo_agente: bool = False) -> int:
    try:
        return _principal(aplicar, nuevo_agente)
    except ErrorElevenLabs as e:
        print(e)
        return 1


def _principal(aplicar: bool, nuevo_agente: bool) -> int:
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
        ids = list(prompt.get("tool_ids") or [])
        id_herramienta = herramienta(http, cabeceras, crear_si_falta=False)
        falta_herramienta = id_herramienta is None or id_herramienta not in ids
        print(f"Agente: {datos.get('name', '?')} ({agente})")
        if actual == nuevo and not falta_herramienta:
            print("El prompt y la herramienta datos_pendientes ya están al día. Nada que hacer.")
            return 0
        if actual != nuevo:
            diff = list(difflib.unified_diff(actual.splitlines(), nuevo.splitlines(), "ElevenLabs", "repo", lineterm="", n=1))
            print("\n".join(diff[:120]) + ("\n…" if len(diff) > 120 else ""))
        if falta_herramienta:
            print(f"Al agente le falta la herramienta {HERRAMIENTA['name']}.")
        if not aplicar:
            print("\nSolo comparación. Para subirlo: python scripts/sincronizar_voz.py --aplicar")
            return 0

        if falta_herramienta:
            id_herramienta = id_herramienta or herramienta(http, cabeceras, crear_si_falta=True)
            ids.append(id_herramienta)
        COPIAS.mkdir(exist_ok=True)
        copia = COPIAS / f"{agente}-{datetime.now():%Y%m%d-%H%M%S}.json"
        copia.write_text(json.dumps(prompt, ensure_ascii=False, indent=2), encoding="utf-8")
        # `tools` es la forma antigua de `tool_ids`; enviar las dos a la vez puede chocar.
        resto = {k: v for k, v in prompt.items() if k != "tools"}
        cuerpo = {"conversation_config": {"agent": {"prompt": {**resto, "prompt": nuevo, "tool_ids": ids}}}}
        r = http.patch(url, headers=cabeceras, json=cuerpo)
        if r.status_code != 200:
            print(f"ElevenLabs respondió {r.status_code} al actualizar: {r.text[:300]}")
            return 1
    print(f"\nAgente actualizado. Copia del prompt anterior en {copia}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--aplicar", action="store_true", help="sube el prompt (sin esto solo compara)")
    p.add_argument("--crear", action="store_true", help="crea el agente de voz si aún no existe")
    a = p.parse_args()
    sys.exit(principal(a.aplicar, a.crear))
