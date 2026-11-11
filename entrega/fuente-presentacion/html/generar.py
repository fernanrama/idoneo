"""Genera entrega/Idoneo_presentacion.html: el deck animado en UN solo archivo.

Mete dentro las fuentes (Sora e IBM Plex Mono, licencia OFL), el logo, el icono, el sello y la captura
de la entidad, para que funcione sin internet en el portátil que proyecta.

Uso (desde la raíz del repo):  python entrega/fuente-presentacion/html/generar.py
Las diapositivas se editan en deck.html, junto a este script.
"""
import base64
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
MARCA = RAIZ / "frontend" / "public" / "marca"
SALIDA = RAIZ / "entrega" / "Idoneo_presentacion.html"


def b64(ruta: Path) -> str:
    return base64.b64encode(ruta.read_bytes()).decode()


def svg(nombre: str, onda: bool = False) -> str:
    t = (MARCA / nombre).read_text(encoding="utf-8")
    t = re.sub(r"\s(width|height)=\"[^\"]+\"", "", t, count=2)  # que escale con su contenedor
    t = t.replace('role="img"', 'role="img" style="width:100%;height:auto;display:block"')
    if onda:  # el acento de la «ó» es una onda de audio: se anima
        t = t.replace("<rect ", '<rect class="onda" ')
    return t


def main() -> None:
    html = (AQUI / "deck.html").read_text(encoding="utf-8")
    sustituciones = {
        "{{FONT_SORA}}": b64(AQUI / "fuentes" / "sora-latin-wght-normal.woff2"),
        "{{FONT_SORA_EXT}}": b64(AQUI / "fuentes" / "sora-latin-ext-wght-normal.woff2"),
        "{{FONT_MONO}}": b64(AQUI / "fuentes" / "ibm-plex-mono-latin-400-normal.woff2"),
        "{{LOGO_OSCURO}}": svg("idoneo-logo-sobre-oscuro.svg", onda=True),
        "{{LOGO_OSCURO_PEQ}}": svg("idoneo-logo-sobre-oscuro.svg"),
        "{{ICONO}}": svg("idoneo-icono-app.svg", onda=True),
        "{{ICONO_B64}}": b64(MARCA / "idoneo-icono-app.svg"),
        "{{SELLO_CLARO}}": svg("powered-by-idoneo-claro.svg"),
        "{{CAP_ENTIDAD}}": b64(AQUI.parent / "assets" / "entidad_carmen.jpg"),
    }
    for clave, valor in sustituciones.items():
        if clave not in html:
            raise SystemExit(f"Falta {clave} en deck.html")
        html = html.replace(clave, valor)
    if "{{" in html:
        raise SystemExit("Queda algún marcador {{…}} sin sustituir")
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Escrito {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
