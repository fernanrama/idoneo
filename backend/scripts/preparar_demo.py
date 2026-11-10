"""Prepara los ficheros de configuración local para probar el proyecto o hacer la demo.

Uso (desde backend/; no necesita el entorno virtual, solo Python):

    python scripts/preparar_demo.py

Qué hace:
- crea `.env` (raíz) desde `.env.example` y `frontend/.env.local` desde `frontend/.env.example`, si faltan;
- rellena con valores aleatorios y distintos los secretos locales que estén VACÍOS: `CLIENT_ACCESS_SECRET`
  (sin él no se pueden crear clientes), `ADMIN_TOKEN`, `VOICE_USER_ID_SECRET`, `DEMO_ADVISOR_TOKEN` (el mismo
  en los dos ficheros) y `MCP_DEMO_TOKEN`;
- activa el modo asesor de demostración (`DEMO_ADVISOR_MODE=1`), que solo funciona en local y con clientes
  ficticios (docs/MODO_ASESOR_DEMO.md). Con `--sin-modo-asesor` no lo toca.

Qué no hace: no muestra ningún secreto, no cambia valores que ya estén puestos y no toca las claves de
Claude ni de ElevenLabs (esas las pone cada persona a mano). Se puede ejecutar las veces que haga falta.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SECRETOS = ("CLIENT_ACCESS_SECRET", "ADMIN_TOKEN", "VOICE_USER_ID_SECRET", "DEMO_ADVISOR_TOKEN", "MCP_DEMO_TOKEN")
LINEA = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=(.*)$")


def leer(fichero: Path) -> dict[str, str]:
    """Variables definidas (sin comentar) en un fichero .env."""
    valores = {}
    for linea in fichero.read_text("utf-8").splitlines():
        m = LINEA.match(linea)
        if m:
            valores[m.group(1)] = m.group(2).strip().strip("'\"")
    return valores


def poner(fichero: Path, cambios: dict[str, str]) -> None:
    """Escribe cada variable en su línea (o al final si no existe), sin tocar el resto del fichero."""
    lineas = fichero.read_text("utf-8").splitlines()
    pendientes = dict(cambios)
    for i, linea in enumerate(lineas):
        m = LINEA.match(linea)
        if m and m.group(1) in pendientes:
            lineas[i] = f"{m.group(1)}={pendientes.pop(m.group(1))}"
    lineas += [f"{k}={v}" for k, v in pendientes.items()]
    fichero.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    try:
        os.chmod(fichero, 0o600)
    except OSError:
        pass


def nuevo_secreto(usados: set[str]) -> str:
    """48 bytes aleatorios en [A-Za-z0-9_-], que empieza por letra y no repite ninguno existente."""
    while True:
        s = secrets.token_urlsafe(48)
        if s[0].isalpha() and s not in usados:
            usados.add(s)
            return s


def preparar(raiz: Path = RAIZ, modo_asesor: bool = True) -> list[str]:
    """Devuelve la lista de cosas hechas (nombres de variables, nunca valores)."""
    hecho: list[str] = []
    env, env_front = raiz / ".env", raiz / "frontend" / ".env.local"
    for destino, plantilla in ((env, raiz / ".env.example"), (env_front, raiz / "frontend" / ".env.example")):
        if not destino.exists():
            shutil.copyfile(plantilla, destino)
            hecho.append(f"creado {destino.relative_to(raiz)}")

    back, front = leer(env), leer(env_front)
    usados = {v for v in (*back.values(), *front.values()) if v}
    cambios_back: dict[str, str] = {}
    cambios_front: dict[str, str] = {}
    for nombre in SECRETOS:
        if nombre == "DEMO_ADVISOR_TOKEN":
            # El mismo valor en los dos ficheros: manda el que ya exista (primero el del backend).
            valor = back.get(nombre) or front.get(nombre) or nuevo_secreto(usados)
            if back.get(nombre) != valor:
                cambios_back[nombre] = valor
            if front.get(nombre) != valor:
                cambios_front[nombre] = valor
        elif not back.get(nombre):
            cambios_back[nombre] = nuevo_secreto(usados)
    if modo_asesor:
        if back.get("DEMO_ADVISOR_MODE") != "1":
            cambios_back["DEMO_ADVISOR_MODE"] = "1"
        if front.get("DEMO_ADVISOR_MODE") != "1":
            cambios_front["DEMO_ADVISOR_MODE"] = "1"

    for fichero, cambios in ((env, cambios_back), (env_front, cambios_front)):
        if cambios:
            poner(fichero, cambios)
            hecho.append(f"{fichero.relative_to(raiz)}: " + ", ".join(sorted(cambios)))
    return hecho


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sin-modo-asesor", action="store_true", help="no activa DEMO_ADVISOR_MODE")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cosas = preparar(modo_asesor=not a.sin_modo_asesor)
    if not cosas:
        print("Todo estaba ya preparado; no se ha cambiado nada.")
    else:
        for c in cosas:
            print(f"- {c}")
        print("Los valores no se muestran. Reinicia el backend y el frontend para que los lean.")
