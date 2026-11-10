"""Sincroniza el agente de voz de ElevenLabs con la configuración versionada en el repo.

El prompt vive en ``app/agentes/prompts/entrevistador.md`` y se comparte con el modo texto. El script
sincroniza sus instrucciones, los valores de preview de las variables dinámicas de memoria, la herramienta
de cliente ``datos_pendientes`` y la herramienta de sistema ``end_call``. Conserva la voz, el modelo, el
primer mensaje y cualquier otra configuración o herramienta que se haya definido en el panel.

``datos_pendientes`` la ejecuta el navegador: consulta ``GET /api/sessions/{id}/pending`` y devuelve al
agente qué falta preguntar. ``end_call`` permite que el agente cuelgue después de despedirse.

Uso (desde backend/, con ELEVENLABS_API_KEY y ELEVENLABS_AGENT_ID en ../.env):

    python scripts/sincronizar_voz.py            # solo compara
    python scripts/sincronizar_voz.py --aplicar  # guarda una copia y sincroniza
    python scripts/sincronizar_voz.py --crear    # crea el agente si aún no existe
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
PRIMER_MENSAJE = (
    "Hola, soy el asistente de perfil inversor del banco. Soy una inteligencia artificial y una "
    "persona del banco revisará todo. Le haré unas preguntas para conocer su situación antes de "
    "ofrecerle productos de inversión. ¿Le parece bien que grabemos la conversación?"
)
MODELO_VOZ = "eleven_flash_v2_5"
HERRAMIENTA = {
    "type": "client",
    "name": "datos_pendientes",
    "description": (
        "Devuelve qué datos del perfil faltan, cuáles conviene volver a preguntar y qué conocimientos "
        "falta comprobar. Llámala al terminar cada bloque del guion y siempre antes de despedirte."
    ),
    "expects_response": True,
    "response_timeout_secs": 10,
}
COLGAR = {
    "type": "system",
    "name": "end_call",
    "description": "Cuelga la llamada. Úsala justo después de despedirte, o cuando el cliente pida terminar.",
    "params": {"system_tool_type": "end_call"},
}
PLACEHOLDERS = {
    "personal_memory_enabled": False,
    "personal_memory_context": "Sin preferencias personales autorizadas para esta conversación.",
    "next_focus": "avisos y consentimiento",
    "session_id": "s-preview",
}


class ErrorElevenLabs(Exception):
    pass


def herramienta(http: httpx.Client, cabeceras: dict, crear_si_falta: bool) -> str | None:
    """Devuelve el ID de ``datos_pendientes`` y, si se solicita, la crea cuando no existe."""
    r = http.get(API_HERRAMIENTAS, headers=cabeceras, params={"search": HERRAMIENTA["name"]})
    if r.status_code != 200:
        raise ErrorElevenLabs(f"ElevenLabs respondió {r.status_code} al listar herramientas: {r.text[:300]}")
    for item in r.json().get("tools", []):
        if (item.get("tool_config") or {}).get("name") == HERRAMIENTA["name"]:
            return item["id"]
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
                "agent": {
                    "language": "es",
                    "first_message": PRIMER_MENSAJE,
                    "prompt": {
                        "prompt": chat.sistema_voz().strip(),
                        "tool_ids": [id_herramienta],
                        "built_in_tools": {"end_call": COLGAR},
                    },
                    "dynamic_variables": {"dynamic_variable_placeholders": PLACEHOLDERS},
                },
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


COPIAS = RAIZ / "scripts" / ".copias_voz"


def principal(aplicar: bool, nuevo_agente: bool = False) -> int:
    try:
        return _principal(aplicar, nuevo_agente)
    except ErrorElevenLabs as exc:
        print(exc)
        return 1


def _principal(aplicar: bool, nuevo_agente: bool) -> int:
    clave = os.getenv("ELEVENLABS_API_KEY", "").strip()
    agente = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
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
        config_agente = ((datos.get("conversation_config") or {}).get("agent") or {})
        prompt = config_agente.get("prompt") or {}
        dinamicas = config_agente.get("dynamic_variables") or {}
        placeholders = dinamicas.get("dynamic_variable_placeholders") or {}
        nuevos_placeholders = {**placeholders, **PLACEHOLDERS}
        actual, nuevo = (prompt.get("prompt") or "").strip(), chat.sistema_voz().strip()
        ids = list(prompt.get("tool_ids") or [])
        id_herramienta = herramienta(http, cabeceras, crear_si_falta=False)
        falta_herramienta = id_herramienta is None or id_herramienta not in ids
        integradas = dict(prompt.get("built_in_tools") or {})
        falta_colgar = not integradas.get("end_call")
        prompt_cambio = actual != nuevo
        variables_cambio = placeholders != nuevos_placeholders

        print(f"Agente: {datos.get('name', '?')} ({agente})")
        if not prompt_cambio and not variables_cambio and not falta_herramienta and not falta_colgar:
            print("El prompt, las variables dinámicas y las herramientas ya están al día. Nada que hacer.")
            return 0
        if prompt_cambio:
            diff = list(difflib.unified_diff(
                actual.splitlines(), nuevo.splitlines(), "ElevenLabs", "repo", lineterm="", n=1
            ))
            print("\n".join(diff[:120]) + ("\n…" if len(diff) > 120 else ""))
        if variables_cambio:
            print("Variables dinámicas a sincronizar: " + ", ".join(PLACEHOLDERS))
        if falta_herramienta:
            print(f"Al agente le falta la herramienta {HERRAMIENTA['name']}.")
        if falta_colgar:
            print("Al agente le falta la herramienta de sistema end_call (colgar la llamada).")
        if not aplicar:
            print("\nSolo comparación. Para subirlo: python scripts/sincronizar_voz.py --aplicar")
            return 0

        if falta_herramienta:
            id_herramienta = id_herramienta or herramienta(http, cabeceras, crear_si_falta=True)
            ids.append(id_herramienta)
        if falta_colgar:
            integradas["end_call"] = COLGAR

        COPIAS.mkdir(exist_ok=True)
        copia = COPIAS / f"{agente}-{datetime.now():%Y%m%d-%H%M%S}.json"
        copia.write_text(
            json.dumps({"prompt": prompt, "dynamic_variables": dinamicas}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        resto_prompt = {k: v for k, v in prompt.items() if k != "tools"}
        cuerpo = {"conversation_config": {"agent": {
            "prompt": {
                **resto_prompt,
                "prompt": nuevo,
                "tool_ids": ids,
                "built_in_tools": integradas,
            },
            "dynamic_variables": {
                **dinamicas,
                "dynamic_variable_placeholders": nuevos_placeholders,
            },
        }}}
        r = http.patch(url, headers=cabeceras, json=cuerpo)
        if r.status_code != 200:
            print(f"ElevenLabs respondió {r.status_code} al actualizar: {r.text[:300]}")
            return 1
    print(f"\nAgente actualizado. Copia de la configuración anterior en {copia}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="sincroniza (sin esto solo compara)")
    parser.add_argument("--crear", action="store_true", help="crea el agente de voz si aún no existe")
    args = parser.parse_args()
    sys.exit(principal(args.aplicar, args.crear))
