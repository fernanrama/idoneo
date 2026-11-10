"""Contrato real entre el cliente TypeScript y la API, solo en un servidor local aislado.

No usa navegador ni proveedores. Los módulos TS se compilan a un temporal y Node usa
fetch contra uvicorn en un puerto efímero. Ninguna petición utiliza los puertos de la demo.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

import pytest

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"

CLIENTE = r'''
const assert = require('node:assert/strict');
const { join } = require('node:path');
function almacenamiento() {
  const datos = new Map();
  return {getItem: k => datos.get(k) ?? null, setItem: (k,v) => datos.set(k,String(v)),
          removeItem: k => datos.delete(k), clear: () => datos.clear()};
}
global.window = {sessionStorage: almacenamiento(), localStorage: almacenamiento()};
const {api, ErrorAPI} = require(join(process.env.IDONEO_CLIENT_BUILD,'api.js'));
const cred = require(join(process.env.IDONEO_CLIENT_BUILD,'credenciales.js'));
const {opcionesVoz} = require(join(process.env.IDONEO_CLIENT_BUILD,'iniciarVoz.js'));
const base = process.env.NEXT_PUBLIC_API_URL;
assert.equal(new URL(base).hostname, '127.0.0.1');
async function raw(path, token, method='GET', body, etag) {
  return fetch(base + path, {method, headers: {'Content-Type':'application/json',
    ...(token ? {Authorization:`Bearer ${token}`} : {}), ...(etag ? {'If-Match':etag}: {})},
    ...(body === undefined ? {} : {body:JSON.stringify(body)})});
}
(async () => {
  const a = await api.crearSesion(undefined,'text');
  const tokenA = cred.tokenCliente(a.client_id);
  assert.ok(tokenA);
  assert.equal(a.access_token, undefined);
  cred.persistirSesion(a);
  assert.ok(!window.localStorage.getItem(cred.CLAVE_SESION).includes(tokenA));
  const anterior = await api.perfil(a.client_id);
  const inicial = await api.memoria(a.session_id);
  assert.deepEqual([inicial.enabled,inicial.version,inicial.etag],[false,0,'"personal-0"']);
  const cambio = {communication:{pace:'slow'},concerns:['No repetir conceptos']};
  const guardada = await api.guardarMemoria(a.session_id,inicial.etag,true,cambio);
  assert.deepEqual([guardada.enabled,guardada.version],[true,1]);

  const b = await api.crearSesion(undefined,'text');
  const tokenB = cred.tokenCliente(b.client_id);
  const rutaA = `/api/sessions/${a.session_id}/memory`;
  assert.equal((await raw(rutaA,tokenB)).status,404);
  assert.equal((await raw(rutaA,tokenB,'PUT',{consent_given:true,updates:cambio},guardada.etag)).status,404);
  assert.equal((await raw(rutaA,tokenB,'DELETE',undefined,guardada.etag)).status,404);
  assert.equal((await raw(`/api/clients/${a.client_id}/profile`,tokenB)).status,404);
  assert.equal((await raw(`/api/voice/context/${a.session_id}`,tokenB)).status,404);
  assert.equal((await raw('/api/sessions',tokenB,'POST',{client_id:a.client_id})).status,404);

  const reanudada = await raw('/api/sessions',tokenA,'POST',{client_id:a.client_id,channel:'text'});
  assert.equal(reanudada.status,200);
  assert.equal(Object.hasOwn(await reanudada.json(),'access_token'),false);
  assert.equal((await raw(rutaA,tokenA,'PUT',{consent_given:true,updates:cambio})).status,428);
  assert.equal((await raw(rutaA,tokenA,'DELETE')).status,428);
  assert.equal((await raw(rutaA,tokenA,'DELETE',undefined,'*')).status,412);

  const borrada = await api.borrarMemoria(a.session_id,guardada.etag);
  assert.deepEqual([borrada.enabled,borrada.version],[false,2]);
  await assert.rejects(api.guardarMemoria(a.session_id,guardada.etag,true,cambio),
    e => e instanceof ErrorAPI && e.status===412);
  const vigente = await api.memoria(a.session_id);
  assert.deepEqual([vigente.enabled,vigente.version],[false,2]);
  await assert.rejects(api.guardarMemoria(a.session_id,vigente.etag,false,cambio),e => e.status===422);
  const nueva = await api.guardarMemoria(a.session_id,vigente.etag,true,{communication:{pace:'fast'}});
  assert.deepEqual([nueva.enabled,nueva.version],[true,3]);
  assert.equal(nueva.data.concerns,undefined);
  const posterior = await api.perfil(a.client_id);
  assert.equal(posterior.version,anterior.version);
  assert.deepEqual(posterior.mifid,anterior.mifid);

  // El bootstrap sin claves responde localmente 503. Solo construimos opciones del
  // fallback: jamás se instancia ni conecta un SDK de voz a un servicio externo.
  const voz = await opcionesVoz(a.session_id,'agente-ficticio-no-conectado');
  assert.equal(voz.agentId,'agente-ficticio-no-conectado');
  assert.equal(voz.dynamicVariables.session_id,a.session_id);
  assert.equal(voz.dynamicVariables.personal_memory_enabled,true);

  const demo = await api.perfilDemo();
  assert.equal(demo.client_id,'carmen-68');
  assert.deepEqual(demo.personal,{});
  assert.equal((await api.restriccionesDemo()).usable,false);
  assert.equal(cred.tokenCliente('carmen-68'),null);
  console.log('Contrato TS/API local correcto: autorización, CAS, consentimiento, MiFID, demo y opciones de voz.');
})().catch(e => { console.error(e.name, e.message); process.exitCode=1; });
'''


def test_cliente_typescript_con_api_local_real(tmp_path):
    node = shutil.which("node")
    if node is None or not (FRONTEND / "node_modules" / "typescript" / "bin" / "tsc").is_file():
        pytest.skip("Necesita Node y las dependencias del frontend: ejecuta `npm install` en frontend/")
    compilado = tmp_path / "cliente"
    fuentes = ["tipos.ts", "credenciales.ts", "api.ts", "iniciarVoz.ts"]
    compilacion = subprocess.run([
        node, "node_modules/typescript/bin/tsc", "--outDir", str(compilado),
        "--module", "commonjs", "--moduleResolution", "node", "--target", "ES2020",
        "--lib", "ES2020,DOM", "--esModuleInterop", "--skipLibCheck", "--strict",
        *[f"src/lib/{f}" for f in fuentes],
    ], cwd=FRONTEND, capture_output=True, text=True, timeout=60)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    with socket.socket() as conexion:
        conexion.bind(("127.0.0.1", 0))
        puerto = conexion.getsockname()[1]
    base = f"http://127.0.0.1:{puerto}"
    entorno = {**os.environ, "PERFIL_ALMACEN": "memoria", "DATA_PERSIST": "0", "DATABASE_URL": "",
               "TEST_POSTGRES_URL": "", "ANTHROPIC_API_KEY": "", "ELEVENLABS_API_KEY": "",
               "ELEVENLABS_AGENT_ID": "", "LOAD_DEMO_FIXTURE": "0", "DEMO_ENDPOINTS": "1",
               "ADMIN_TOKEN": "", "CLIENT_ACCESS_SECRET": "solo-pruebas-locales-" * 3,
               "CLIENT_ACCESS_TTL_S": "28800", "NEXT_PUBLIC_API_URL": base,
               "IDONEO_CLIENT_BUILD": str(compilado)}
    script = tmp_path / "cliente.cjs"
    script.write_text(CLIENTE, encoding="utf-8")
    with (tmp_path / "uvicorn.log").open("w") as log:
        proceso = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                                    "--host", "127.0.0.1", "--port", str(puerto), "--log-level", "warning"],
                                   cwd=BACKEND, env=entorno, stdout=log, stderr=subprocess.STDOUT)
        try:
            with httpx.Client(timeout=0.5, trust_env=False) as cliente:
                for _ in range(80):
                    assert proceso.poll() is None, "El backend de prueba terminó al arrancar"
                    try:
                        if cliente.get(base + "/api/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                else:
                    raise AssertionError("El backend local de prueba no arrancó")
            resultado = subprocess.run([node, str(script)], cwd=FRONTEND, env=entorno,
                                       capture_output=True, text=True, timeout=30)
            assert resultado.returncode == 0, resultado.stdout + resultado.stderr
        finally:
            proceso.terminate()
            proceso.wait(timeout=10)
