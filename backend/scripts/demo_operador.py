"""Operador de la demostración: autoriza, lista y revoca clientes ficticios nuevos (DATOS SIMULADOS).

Se ejecuta en el ordenador del backend. Lee ADMIN_TOKEN del entorno o del .env de la raíz, sin mostrarlo,
y solo habla con un backend local. Ver docs/MODO_ASESOR_DEMO.md.

    python scripts/demo_operador.py autorizar <client_id> --confirmo-ficticio [--ttl 7200]
    python scripts/demo_operador.py listar
    python scripts/demo_operador.py revocar <client_id>
    python scripts/demo_operador.py revocar-todo

`autorizar` escribe en stdout SOLO el token MCP de ese cliente (lo demás va a stderr) y se niega a escribirlo
directamente en la terminal (se vería en pantalla y en el scroll): captúralo en una variable.

    export IDONEO_MCP_TOKEN="$(python scripts/demo_operador.py autorizar cliente-… --confirmo-ficticio)"
    claude mcp add --transport http idoneo-cliente http://localhost:8000/mcp -H "Authorization: Bearer $IDONEO_MCP_TOKEN"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parents[2]
LOCALES = {"localhost", "127.0.0.1", "::1"}


def _admin() -> str:
    valor = os.getenv("ADMIN_TOKEN") or dotenv_values(RAIZ / ".env").get("ADMIN_TOKEN") or ""
    if not valor.strip():
        sys.exit("Falta ADMIN_TOKEN (en el entorno o en el .env de la raíz).")
    return valor.strip()


def _base() -> str:
    base = os.getenv("IDONEO_API_URL", "http://127.0.0.1:8000").rstrip("/")
    if urlsplit(base).hostname not in LOCALES:
        sys.exit("El operador solo habla con un backend local (IDONEO_API_URL debe ser localhost o 127.0.0.1).")
    return base


def _pedir(metodo: str, ruta: str, **kw) -> dict:
    try:
        r = httpx.request(metodo, f"{_base()}/api/demo/operador{ruta}", headers={"X-Admin-Token": _admin()},
                          timeout=10, **kw)
    except httpx.HTTPError:
        sys.exit("No se pudo contactar con el backend local. ¿Está arrancado?")
    if r.status_code >= 400:
        try:
            detalle = r.json().get("detail")
        except ValueError:
            detalle = ""
        sys.exit(f"Error {r.status_code}: {detalle or 'sin detalle'}"
                 + (" (¿DEMO_ADVISOR_MODE=1 en el .env y backend reiniciado?)" if r.status_code == 404 else ""))
    return r.json()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)
    a = sub.add_parser("autorizar", help="autoriza un cliente ficticio y emite su token MCP de lectura")
    a.add_argument("client_id")
    a.add_argument("--confirmo-ficticio", action="store_true", required=True,
                   help="confirmas que el cliente es ficticio (DATOS SIMULADOS)")
    a.add_argument("--ttl", type=int, default=7200, help="segundos de validez (60–28800; por defecto 7200)")
    a.add_argument("--mostrar-token", action="store_true",
                   help="permite escribir el token en la terminal (no recomendado con la pantalla proyectada)")
    sub.add_parser("listar", help="autorizaciones vigentes (sin tokens)")
    r = sub.add_parser("revocar", help="revoca la autorización y el token MCP de un cliente")
    r.add_argument("client_id")
    sub.add_parser("revocar-todo", help="revoca todas las autorizaciones")
    args = p.parse_args(argv)

    if args.orden == "autorizar":
        if sys.stdout.isatty() and not args.mostrar_token:
            # Se comprueba ANTES de autorizar: no se crea ningún token que no se pueda guardar.
            sys.exit("No escribo el token en la pantalla. Captúralo así (no se crea nada hasta entonces):\n"
                     f'  export IDONEO_MCP_TOKEN="$(python scripts/demo_operador.py autorizar {args.client_id} --confirmo-ficticio)"')
        d = _pedir("POST", "/autorizaciones", json={"client_id": args.client_id, "ficticio": True, "ttl_s": args.ttl})
        print(f"Autorizado {d['client_id']} (perfil v{d['profile_version']}, {d['profile_status']}) "
              f"hasta {d['expires_at_iso']}. Arranque del backend: {d['boot']}.", file=sys.stderr)
        print("El asesor ya puede validarlo en /entidad/" + d["client_id"] + " (recarga la página).", file=sys.stderr)
        print(d["mcp_token"])  # único dato en stdout
    elif args.orden == "listar":
        d = _pedir("GET", "/autorizaciones")
        print(f"Arranque del backend: {d['boot']}")
        for x in d["autorizaciones"]:
            print(f"  {x['client_id']}: caduca en {x['expires_in_s'] // 60} min")
        if not d["autorizaciones"]:
            print("  (ninguna)")
    elif args.orden == "revocar":
        d = _pedir("DELETE", f"/autorizaciones/{args.client_id}")
        print(f"{d['client_id']}: {'revocada' if d['revocada'] else 'no tenía autorización vigente'}")
    else:
        print(f"Revocadas: {_pedir('DELETE', '/autorizaciones')['revocadas']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
