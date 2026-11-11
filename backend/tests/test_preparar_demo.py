"""El script que prepara el .env local: rellena solo lo vacío, no repite secretos y no cambia lo que ya hay."""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("preparar_demo", REPO / "backend" / "scripts" / "preparar_demo.py")
preparar_demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preparar_demo)


def _raiz(tmp_path: Path) -> Path:
    (tmp_path / "frontend").mkdir()
    (tmp_path / ".env.example").write_text((REPO / ".env.example").read_text("utf-8"), "utf-8")
    (tmp_path / "frontend" / ".env.example").write_text((REPO / "frontend" / ".env.example").read_text("utf-8"), "utf-8")
    return tmp_path


def test_rellena_los_secretos_vacios_con_valores_validos_y_distintos(tmp_path):
    raiz = _raiz(tmp_path)
    hecho = preparar_demo.preparar(raiz)
    back = preparar_demo.leer(raiz / ".env")
    front = preparar_demo.leer(raiz / "frontend" / ".env.local")
    valores = [back[n] for n in preparar_demo.SECRETOS]
    assert all(len(v.encode()) >= 32 for v in valores)
    assert len(set(valores)) == len(valores)
    assert front["DEMO_ADVISOR_TOKEN"] == back["DEMO_ADVISOR_TOKEN"]
    assert back["DEMO_ADVISOR_MODE"] == front["DEMO_ADVISOR_MODE"] == "1"
    assert back["ANTHROPIC_API_KEY"] == "" and back["ELEVENLABS_API_KEY"] == ""
    assert not any(v in linea for v in valores for linea in hecho), "el resumen no puede contener secretos"


def test_no_cambia_lo_que_ya_estaba_y_es_idempotente(tmp_path):
    raiz = _raiz(tmp_path)
    propio = "x" * 40
    (raiz / ".env").write_text(f"CLIENT_ACCESS_SECRET={propio}\nANTHROPIC_API_KEY=mi-clave\n# comentario\n", "utf-8")
    preparar_demo.preparar(raiz, modo_asesor=False)
    back = preparar_demo.leer(raiz / ".env")
    assert back["CLIENT_ACCESS_SECRET"] == propio and back["ANTHROPIC_API_KEY"] == "mi-clave"
    assert "DEMO_ADVISOR_MODE" not in back
    assert "# comentario" in (raiz / ".env").read_text("utf-8")
    antes = (raiz / ".env").read_text("utf-8"), (raiz / "frontend" / ".env.local").read_text("utf-8")
    assert preparar_demo.preparar(raiz, modo_asesor=False) == []
    assert antes == ((raiz / ".env").read_text("utf-8"), (raiz / "frontend" / ".env.local").read_text("utf-8"))


def test_la_plantilla_generada_pasa_las_comprobaciones_del_backend(tmp_path, monkeypatch):
    import app.main  # noqa: F401  (orden de importación de la aplicación)
    from app import asesor_demo
    from app.mcp import demo as mcp_demo

    raiz = _raiz(tmp_path)
    preparar_demo.preparar(raiz)
    for nombre, valor in preparar_demo.leer(raiz / ".env").items():
        monkeypatch.setenv(nombre, valor)
    assert mcp_demo.configuracion() is not None
    assert asesor_demo.configuracion() is not None
