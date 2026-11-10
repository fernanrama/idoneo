"""Credenciales ficticias explícitas para los tests que verifican reglas de negocio.

Los tests de autorización usan TestClient sin este helper. No existe ningún modo de bypass
en producción: aquí se firma con el secreto sintético configurado por la fixture de pruebas.
"""

import os

from fastapi.testclient import TestClient

from app import acceso
from app.main import app


def cabeceras_cliente(client_id: str = "carmen-68", *, servicio: bool = True) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {acceso.emitir_credencial(client_id)}"}
    if servicio:
        headers["X-Admin-Token"] = os.environ["ADMIN_TOKEN"]
    return headers


def cliente_autorizado(client_id: str = "carmen-68", *, servicio: bool = True) -> TestClient:
    return TestClient(app, headers=cabeceras_cliente(client_id, servicio=servicio))
