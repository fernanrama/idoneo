// Modo asesor de demo de punta a punta: backend + Next reales en puertos efímeros, sin proveedores.
// Requiere el build del front (next build) e IDONEO_PYTHON. Con IDONEO_PLAYWRIGHT_MODULE añade el
// recorrido en Chromium (pulsar «Validar perfil»). Nunca usa los puertos 3000/8000 ni datos reales.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { existsSync, mkdtempSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { setTimeout as pausa } from "node:timers/promises";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = resolve(frontend, "../backend");
const python = process.env.IDONEO_PYTHON;
assert.ok(python && existsSync(python), "Indica IDONEO_PYTHON con el entorno Python ya instalado.");
assert.ok(existsSync(resolve(frontend, ".next/BUILD_ID")), "Ejecuta antes el build del frontend.");

const C = "carmen-68";
const TOKEN = "asesor-demo-ficticio-exclusivo-de-test-local-0123456789";
const ADMIN = "servicio-ficticio-exclusivo-de-test-local";

async function puertoLibre(usados) {
  for (;;) {
    const s = createServer(); s.listen(0, "127.0.0.1"); await once(s, "listening");
    const p = s.address().port; await new Promise((ok) => s.close(ok));
    if (![3000, 8000, ...usados].includes(p)) return p;
  }
}
const puertos = [];
for (let i = 0; i < 4; i++) puertos.push(await puertoLibre(puertos));
const [pApi, pFront, pFrontMal, pFrontOff] = puertos;
const api = `http://127.0.0.1:${pApi}`;
const front = `http://127.0.0.1:${pFront}`;
const frontMal = `http://127.0.0.1:${pFrontMal}`;
const frontOff = `http://127.0.0.1:${pFrontOff}`;

const base = { ...process.env, PERFIL_ALMACEN: "memoria", DATA_PERSIST: "0", DATABASE_URL: "", TEST_POSTGRES_URL: "",
  ANTHROPIC_API_KEY: "", ELEVENLABS_API_KEY: "", ELEVENLABS_AGENT_ID: "", NEXT_PUBLIC_ELEVENLABS_AGENT_ID: "",
  ELEVENLABS_WEBHOOK_SECRET: "", LOAD_DEMO_FIXTURE: "1", DEMO_ENDPOINTS: "1", NEXT_TELEMETRY_DISABLED: "1",
  CLIENT_ACCESS_SECRET: "material-sintetico-exclusivo-de-test-local", CLIENT_ACCESS_TTL_S: "28800",
  DEMO_ADVISOR_MODE: "", DEMO_ADVISOR_TOKEN: "", ADMIN_TOKEN: "" };
const hijos = [];
function iniciar(comando, args, cwd, env) {
  const hijo = spawn(comando, args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
  hijo.on("error", () => {}); hijo.stdout.resume(); hijo.stderr.resume(); // no registrar salidas
  hijos.push(hijo); return hijo;
}
async function listo(url, hijo, ruta) {
  for (let i = 0; i < 150; i++) {
    assert.equal(hijo.exitCode, null, `Terminó antes de estar listo: ${url}`);
    try { if ((await fetch(url + ruta, { signal: AbortSignal.timeout(500) })).ok) return; } catch { /* arrancando */ }
    await pausa(100);
  }
  throw new Error(`No arrancó a tiempo: ${url}`);
}
function nextStart(puerto, env) {
  return iniciar(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(puerto)],
    frontend, { ...base, API_URL_SERVIDOR: api, ...env });
}
async function pedir(url, method = "GET", headers = {}, body) {
  return fetch(url, { method, headers: { "Content-Type": "application/json", ...headers },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(8000) });
}
const mismoOrigen = (o) => ({ Origin: o, "Sec-Fetch-Site": "same-origin" });
async function mcpRestricciones() {
  const r = await pedir(`${api}/mcp`, "POST", { "X-Admin-Token": ADMIN, Accept: "application/json, text/event-stream" },
    { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "get_investment_constraints", arguments: { client_id: C } } });
  assert.equal(r.status, 200, "MCP con credencial de servicio");
  return JSON.parse((await r.json()).result.content[0].text);
}
function sinToken(texto, donde) { assert.ok(!texto.includes(TOKEN), `El token de asesor aparece en ${donde}`); }
function archivos(dir) {
  return readdirSync(dir).flatMap((n) => { const r = join(dir, n); return statSync(r).isDirectory() ? archivos(r) : [r]; });
}

let navegador;
try {
  // Bundle del navegador: el token es de ejecución, pero se comprueba que ningún archivo lo contiene.
  for (const f of archivos(resolve(frontend, ".next/static"))) sinToken(readFileSync(f, "utf8"), f);

  const apiHijo = iniciar(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(pApi),
    "--no-access-log", "--log-level", "warning"], backend,
    { ...base, ADMIN_TOKEN: ADMIN, DEMO_ADVISOR_MODE: "1", DEMO_ADVISOR_TOKEN: TOKEN,
      CORS_ORIGINS: [front, frontMal, frontOff].join(",") });
  await listo(api, apiHijo, "/api/health");
  const modos = [nextStart(pFront, { DEMO_ADVISOR_MODE: "1", DEMO_ADVISOR_TOKEN: TOKEN }),
    nextStart(pFrontMal, { DEMO_ADVISOR_MODE: "1", DEMO_ADVISOR_TOKEN: TOKEN.replace("0123", "9999") }),
    nextStart(pFrontOff, {})];
  await Promise.all([listo(front, modos[0], "/"), listo(frontMal, modos[1], "/"), listo(frontOff, modos[2], "/")]);

  // 1. Estado comprobado por el servidor y sin secretos.
  const estado = await pedir(`${front}/api/entidad/asesor`);
  assert.equal(estado.headers.get("Cache-Control"), "no-store");
  const textoEstado = await estado.text(); sinToken(textoEstado, "el estado");
  assert.deepEqual(JSON.parse(textoEstado), { enabled: true, clients: [C, "carmen-corta"], advisor_id: "asesor-demo" });
  assert.deepEqual(await (await pedir(`${frontMal}/api/entidad/asesor`)).json(), { enabled: false, clients: [] });
  assert.deepEqual(await (await pedir(`${frontOff}/api/entidad/asesor`)).json(), { enabled: false, clients: [] });
  const html = await (await pedir(`${front}/entidad/${C}`)).text(); sinToken(html, "el HTML de la entidad");

  // 2. Expediente persistido de Carmen, aún sin validar.
  const antes = await (await pedir(`${front}/api/entidad/${C}/asesor`)).json();
  assert.equal(antes.profile.status, "pending_validation"); assert.equal(antes.constraints.usable, false);
  assert.equal((await mcpRestricciones()).usable, false);

  // 3. Intentos no autorizados: ninguno cambia el perfil.
  const s = await (await pedir(`${api}/api/sessions`, "POST", {}, { channel: "text" })).json(); // cliente real nuevo
  const bearer = { Authorization: `Bearer ${s.access_token}` };
  const rechazos = [
    [frontOff, C, mismoOrigen(frontOff), 403, "modo apagado (comportamiento de la PR #21)"],
    [frontMal, C, mismoOrigen(frontMal), 401, "token del servidor que el backend no acepta"],
    [front, C, {}, 403, "sin Origin"],
    [front, C, { Origin: "https://atacante.example" }, 403, "otro origen"],
    [front, C, { ...mismoOrigen(front), "X-Forwarded-For": "203.0.113.9" }, 403, "detrás de un proxy"],
    [front, s.client_id, { ...mismoOrigen(front), ...bearer }, 404, "cliente real fuera de la lista"],
    [front, "../clients", mismoOrigen(front), 404, "ruta manipulada"],
  ];
  for (const [origen, cid, cabeceras, esperado, caso] of rechazos) {
    const r = await pedir(`${origen}/api/entidad/${encodeURIComponent(cid)}/validar`, "POST", cabeceras, { advisor_id: "intruso", changes: [] });
    assert.equal(r.status, esperado, caso); sinToken(await r.text(), caso);
  }
  for (const cabeceras of [{ "X-Demo-Advisor-Token": s.access_token }, bearer, { "X-Admin-Token": ADMIN }, {}]) {
    assert.equal((await pedir(`${api}/api/demo/asesor/clientes/${C}/validar`, "POST", cabeceras)).status, 401);
  }
  assert.equal((await pedir(`${api}/api/clients/${s.client_id}/profile`, "GET", bearer).then((r) => r.json())).version, 1);
  const intacto = await (await pedir(`${front}/api/entidad/${C}/asesor`)).json();
  assert.equal(intacto.profile.version, antes.profile.version); assert.equal(intacto.profile.status, "pending_validation");

  // 4. Recorrido permitido: validar → activo → disponible por MCP y REST de servicio.
  const v = await pedir(`${front}/api/entidad/${C}/validar`, "POST", mismoOrigen(front), {});
  assert.equal(v.status, 200);
  const validado = await v.json();
  assert.equal(validado.status, "active"); assert.equal(validado.review.validated_by, "asesor-demo");
  assert.equal((await pedir(`${front}/api/entidad/${C}/validar`, "POST", mismoOrigen(front), {})).status, 409);
  const mcp = await mcpRestricciones();
  assert.equal(mcp.usable, true); assert.equal(mcp.profile_version, validado.version);
  const rest = await (await pedir(`${api}/api/clients/${C}/constraints`, "GET", { "X-Admin-Token": ADMIN })).json();
  assert.equal(rest.usable, true);

  // 5. Reinicio para repetir el ensayo.
  const re = await pedir(`${front}/api/entidad/reset`, "POST", mismoOrigen(front), {});
  assert.equal(re.status, 200); assert.equal((await re.json()).status, "pending_validation");
  assert.equal((await mcpRestricciones()).usable, false);
  console.log("HTTP: estado verificado, 11 intentos rechazados, validación, MCP/REST utilizables y reinicio.");

  // 5b. Cliente ficticio nuevo: invisible para el asesor hasta que el operador lo autoriza (solo backend, X-Admin-Token).
  const nuevo = await (await pedir(`${api}/api/sessions`, "POST", {}, { channel: "text" })).json();
  const ruta = `/api/entidad/${nuevo.client_id}`;
  assert.deepEqual((await (await pedir(`${front}/api/entidad/asesor`)).json()).clients, [C, "carmen-corta"]);
  assert.equal((await pedir(`${front}${ruta}/asesor`)).status, 404);
  const op = `${api}/api/demo/operador/autorizaciones`;
  assert.equal((await pedir(op, "POST", { Authorization: `Bearer ${nuevo.access_token}` }, { client_id: nuevo.client_id, ficticio: true })).status, 401);
  assert.equal((await pedir(op, "POST", { "X-Admin-Token": TOKEN }, { client_id: nuevo.client_id, ficticio: true })).status, 401);
  const aut = await pedir(op, "POST", { "X-Admin-Token": ADMIN }, { client_id: nuevo.client_id, ficticio: true });
  assert.equal(aut.status, 201);
  const tokenNuevo = (await aut.json()).mcp_token;
  assert.ok((await (await pedir(`${front}/api/entidad/asesor`)).json()).clients.includes(nuevo.client_id));
  const exp = await (await pedir(`${front}${ruta}/asesor`)).json();
  assert.equal(exp.profile.status, "draft");
  assert.equal((await pedir(`${front}${ruta}/validar`, "POST", mismoOrigen(front), {})).status, 409); // incompleto: MiFID manda
  const mcpNuevo = await pedir(`${api}/mcp`, "POST", { Authorization: `Bearer ${tokenNuevo}`, Accept: "application/json, text/event-stream" },
    { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "get_investment_constraints", arguments: { client_id: nuevo.client_id } } });
  assert.equal(JSON.parse((await mcpNuevo.json()).result.content[0].text).usable, false);
  assert.equal((await pedir(`${op}/${nuevo.client_id}`, "DELETE", { "X-Admin-Token": ADMIN })).status, 200);
  assert.equal((await pedir(`${front}${ruta}/asesor`)).status, 404);
  console.log("HTTP: cliente nuevo invisible sin operador; autorizado → visible, validación sujeta a MiFID (409 incompleto), MCP propio; revocado → invisible.");

  // 6. Navegador real (opcional): el botón se habilita solo con el modo confirmado y valida.
  if (process.env.IDONEO_PLAYWRIGHT_MODULE) {
    const { chromium } = await import(pathToFileURL(process.env.IDONEO_PLAYWRIGHT_MODULE).href);
    navegador = await chromium.launch({ headless: true, args: ["--disable-background-networking"] });
    const capturas = mkdtempSync(join(tmpdir(), "idoneo-asesor-demo-"));
    const ctx = await navegador.newContext({ viewport: { width: 1440, height: 1000 }, locale: "es-ES", reducedMotion: "reduce" });
    const salientes = [];
    // El bundle apunta a NEXT_PUBLIC_API_URL (localhost:8000, la demo del usuario): se reescribe al
    // backend aislado antes de salir del navegador. Todo lo demás se corta.
    const apiDelBuild = "http://localhost:8000";
    await ctx.route("**/*", (r) => {
      const url = new URL(r.request().url());
      salientes.push({ origen: url.origin, cabeceras: r.request().headers() });
      if ([front, frontMal, frontOff].includes(url.origin)) return r.continue();
      if (url.origin === apiDelBuild) return r.continue({ url: api + url.pathname + url.search });
      return r.abort();
    });
    for (const [origen, nombre] of [[frontOff, "apagado"], [frontMal, "token-rechazado"]]) {
      const p = await ctx.newPage(); await p.goto(`${origen}/entidad/${C}`);
      const boton = p.getByRole("button", { name: "Validar perfil" }); await boton.waitFor();
      assert.equal(await boton.isDisabled(), true, `botón deshabilitado: ${nombre}`);
      await p.close();
    }
    const p = await ctx.newPage(); await p.goto(`${front}/entidad/${C}`);
    await p.getByText("Modo asesor de demostración").waitFor();
    const boton = p.getByRole("button", { name: "Validar perfil" });
    await boton.waitFor(); assert.equal(await boton.isDisabled(), false);
    await p.screenshot({ path: join(capturas, "1-antes.png"), fullPage: true });
    await boton.click();
    await p.getByText(/Validado · v\d+/).waitFor({ timeout: 8000 });
    await p.getByRole("tab", { name: "Agente · MCP" }).click();
    await p.getByText(/Usable · v\d+/).waitFor();
    await p.screenshot({ path: join(capturas, "2-validado-mcp.png"), fullPage: true });
    assert.equal((await mcpRestricciones()).usable, true);
    await p.getByRole("tab", { name: "Historial" }).click();
    await p.getByText("validated", { exact: false }).first().waitFor();
    await p.getByRole("button", { name: "Reiniciar la demo" }).click();
    await p.getByRole("button", { name: "Validar perfil" }).waitFor({ timeout: 8000 });
    const almacenado = await p.evaluate(() => JSON.stringify({ ...sessionStorage }) + JSON.stringify({ ...localStorage }));
    sinToken(almacenado, "el almacenamiento del navegador");
    for (const { cabeceras } of salientes) {
      assert.equal(cabeceras["x-demo-advisor-token"], undefined); assert.equal(cabeceras["x-admin-token"], undefined);
      sinToken(JSON.stringify(cabeceras), "una petición del navegador");
    }
    assert.ok(salientes.every((x) => x.origen !== api), "El navegador no llama directamente al backend aislado");
    const directas = salientes.filter((x) => x.origen === apiDelBuild).length;
    assert.ok(directas > 0, "Sin modo, la vista usa el ejemplo fijo del backend");
    // Cliente nuevo en la vista de la entidad: aviso al operador, y tras autorizar, expediente por el modo asesor.
    const otro = await (await pedir(`${api}/api/sessions`, "POST", {}, { channel: "text" })).json();
    const pn = await ctx.newPage(); await pn.goto(`${front}/entidad/${otro.client_id}`);
    await pn.getByText("este cliente aún no está autorizado").waitFor();
    assert.equal((await pedir(op, "POST", { "X-Admin-Token": ADMIN }, { client_id: otro.client_id, ficticio: true })).status, 201);
    await pn.reload(); await pn.getByText("Modo asesor de demostración: cliente ficticio").waitFor();
    assert.equal(await pn.getByText("este cliente aún no está autorizado").count(), 0);
    assert.equal(await pn.getByRole("button", { name: "Reiniciar la demo" }).count(), 0);
    await pn.screenshot({ path: join(capturas, "3-cliente-nuevo-autorizado.png"), fullPage: true });
    console.log(`Navegador: deshabilitado sin modo o con token rechazado; validado y reiniciado con el modo; cliente nuevo con aviso y luego autorizado. Capturas en ${capturas}`);
  }
} finally {
  await navegador?.close();
  for (const hijo of hijos.reverse()) {
    if (hijo.exitCode !== null) continue;
    const fin = once(hijo, "exit"); hijo.kill("SIGTERM");
    await Promise.race([fin, pausa(5000)]);
    if (hijo.exitCode === null && hijo.signalCode === null) hijo.kill("SIGKILL");
  }
}
