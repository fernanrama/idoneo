// Requiere un build previo y Python con las dependencias ya instaladas. Sin proveedores.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { existsSync } from "node:fs";
import { createServer } from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as pausa } from "node:timers/promises";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = resolve(frontend, "../backend");
const python = process.env.IDONEO_PYTHON;
assert.ok(python && existsSync(python), "Indica IDONEO_PYTHON con el entorno Python ya instalado.");
assert.ok(existsSync(resolve(frontend, ".next/BUILD_ID")), "Ejecuta antes el build del frontend integrado.");
async function puertoLibre() {
  const servidor = createServer();
  servidor.listen(0, "127.0.0.1");
  await once(servidor, "listening");
  const puerto = servidor.address().port;
  await new Promise((ok, error) => servidor.close(e => e ? error(e) : ok()));
  assert.ok(puerto !== 3000 && puerto !== 8000);
  return puerto;
}
const puertoApi = await puertoLibre();
let puertoFront = await puertoLibre();
while (puertoFront === puertoApi) puertoFront = await puertoLibre();
const api = `http://127.0.0.1:${puertoApi}`;
const front = `http://127.0.0.1:${puertoFront}`;
const env = { ...process.env, PERFIL_ALMACEN: "memoria", DATA_PERSIST: "0", DATABASE_URL: "",
  TEST_POSTGRES_URL: "", ANTHROPIC_API_KEY: "", ELEVENLABS_API_KEY: "", ELEVENLABS_AGENT_ID: "",
  NEXT_PUBLIC_ELEVENLABS_AGENT_ID: "", LOAD_DEMO_FIXTURE: "0", DEMO_ENDPOINTS: "1",
  CLIENT_ACCESS_SECRET: "material-sintetico-exclusivo-de-test-local", CLIENT_ACCESS_TTL_S: "28800",
  ADMIN_TOKEN: "servicio-ficticio-exclusivo-de-test-local", API_URL_SERVIDOR: api,
  ELEVENLABS_WEBHOOK_SECRET: "", NEXT_TELEMETRY_DISABLED: "1" };
const hijos = [];
function iniciar(comando, args, cwd) {
  const hijo = spawn(comando, args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
  hijo.on("error", () => {});
  // Consumir salidas sin imprimirlas: nunca registrar respuestas ni credenciales.
  hijo.stdout.resume(); hijo.stderr.resume();
  hijos.push(hijo);
  return hijo;
}
async function listo(base, hijo, ruta) {
  for (let i = 0; i < 100; i++) {
    assert.equal(hijo.exitCode, null, "Terminó el proceso aislado antes de estar listo");
    try { if ((await fetch(base + ruta, { signal: AbortSignal.timeout(500) })).ok) return; }
    catch { /* proceso arrancando */ }
    await pausa(100);
  }
  throw new Error("El servidor aislado no arrancó a tiempo");
}
async function pedir(base, ruta, method = "GET", token, body, etag, extra = {}) {
  return fetch(base + ruta, { method, headers: { "Content-Type": "application/json", ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(etag ? { "If-Match": etag } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(5000) });
}
try {
  const apiHijo = iniciar(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
    "--port", String(puertoApi), "--no-access-log", "--log-level", "warning"], backend);
  await listo(api, apiHijo, "/api/health");
  const frontHijo = iniciar(process.execPath, ["node_modules/next/dist/bin/next", "start",
    "--hostname", "127.0.0.1", "--port", String(puertoFront)], frontend);
  await listo(front, frontHijo, "/");
  for (const ruta of ["/", "/onboarding/entrevista", "/onboarding/perfil", "/onboarding/productos",
    "/escenario", "/entidad/carmen-68"]) {
    const r = await pedir(front, ruta);
    assert.equal(r.status, 200, `Render servidor: ${ruta}`);
    assert.ok(!(await r.text()).includes(env.ADMIN_TOKEN));
  }
  const a = await (await pedir(api, "/api/sessions", "POST", undefined, {})).json();
  const b = await (await pedir(api, "/api/sessions", "POST", undefined, {})).json();
  const ruta = `/api/sessions/${a.session_id}/memory`;
  const mifid = await (await pedir(api, `/api/clients/${a.client_id}/profile`, "GET", a.access_token)).json();
  const inicial = await pedir(api, ruta, "GET", a.access_token);
  const body = { consent_given: true, updates: { concerns: ["Preferencia ficticia del test HTTP"] } };
  assert.equal((await pedir(api, ruta, "PUT", a.access_token, body)).status, 428);
  const guardada = await pedir(api, ruta, "PUT", a.access_token, body, inicial.headers.get("ETag"));
  assert.equal(guardada.status, 200);
  const revision = guardada.headers.get("ETag");
  for (const metodo of ["GET", "PUT", "DELETE"]) {
    assert.equal((await pedir(api, ruta, metodo, b.access_token,
      metodo === "PUT" ? body : undefined, revision)).status, 404);
  }
  assert.equal((await pedir(api, "/api/sessions", "POST", b.access_token, { client_id: a.client_id })).status, 404);
  const borrada = await pedir(api, ruta, "DELETE", a.access_token, undefined, revision);
  assert.equal(borrada.status, 200);
  assert.equal((await pedir(api, ruta, "PUT", a.access_token, body, revision)).status, 412);
  const vigente = borrada.headers.get("ETag");
  assert.equal((await pedir(api, ruta, "PUT", a.access_token, { ...body, consent_given: false }, vigente)).status, 422);
  assert.equal((await pedir(api, ruta, "PUT", a.access_token, body, vigente)).status, 200);
  const despues = await (await pedir(api, `/api/clients/${a.client_id}/profile`, "GET", a.access_token)).json();
  assert.equal(despues.version, mifid.version);
  assert.deepEqual(despues.mifid, mifid.mifid);
  assert.equal((await pedir(api, `/api/clients/${a.client_id}/validate`, "POST", a.access_token,
    { advisor_id: "asesor-falso", changes: [] })).status, 401);
  for (const token of [undefined, a.access_token]) {
    const r = await pedir(front, `/api/entidad/${a.client_id}/validar`, "POST", token,
      { advisor_id: "asesor-falso", changes: [] }, undefined, { "X-Forwarded-Host": "localhost" });
    assert.equal(r.status, 403);
    assert.equal(r.headers.get("Cache-Control"), "no-store");
    assert.ok(!(await r.text()).includes(env.ADMIN_TOKEN));
  }
  assert.equal((await pedir(front, "/api/entidad/reset", "POST", a.access_token, {})).status, 403);
  assert.equal((await pedir(api, "/api/voice/bootstrap", "POST", b.access_token, { session_id: a.session_id })).status, 404);
  assert.equal((await pedir(api, "/api/voice/bootstrap", "POST", a.access_token, { session_id: a.session_id })).status, 503);
  assert.deepEqual((await (await pedir(api, "/api/demo/profile")).json()).personal, {});
  console.log("Integración HTTP Next/API correcta: 6 pantallas, aislamiento, CAS, consentimiento, MiFID, proxy sin elevación y bootstrap sin proveedores.");
} finally {
  for (const hijo of hijos.reverse()) {
    if (hijo.exitCode !== null) continue;
    const fin = once(hijo, "exit");
    hijo.kill("SIGTERM");
    await Promise.race([fin, pausa(5000)]);
    if (hijo.exitCode === null && hijo.signalCode === null) hijo.kill("SIGKILL");
  }
}
