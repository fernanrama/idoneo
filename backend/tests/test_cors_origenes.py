"""Los orígenes del front se leen de CORS_ORIGINS con tolerancia a errores de escritura habituales."""

from app.main import origenes_permitidos


def test_origenes_separados_por_comas_y_sin_barra_final():
    assert origenes_permitidos("https://a.example/, http://localhost:3000 ,") == ["https://a.example", "http://localhost:3000"]


def test_un_dominio_sin_esquema_se_toma_como_https():
    assert origenes_permitidos("idoneo-app.vercel.app") == ["https://idoneo-app.vercel.app"]


def test_valor_vacio_no_permite_nada():
    assert origenes_permitidos("") == []
