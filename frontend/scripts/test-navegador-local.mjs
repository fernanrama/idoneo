// UI real en Chromium. Requiere frontend/backend locales ya iniciados, sin claves de proveedores.
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const front = process.env.IDONEO_FRONT_URL;
const api = process.env.IDONEO_API_URL;
for (const valor of [front, api]) {
  assert.ok(valor, "Indica IDONEO_FRONT_URL e IDONEO_API_URL del entorno aislado.");
  const u = new URL(valor);
  assert.ok(u.hostname === "127.0.0.1" && !["3000", "8000", ""].includes(u.port), "Solo puertos locales aislados.");
}
const { chromium } = await import(process.env.IDONEO_PLAYWRIGHT_MODULE ?? "playwright");
const salida = mkdtempSync(join(tmpdir(), "idoneo-navegador-"));
const browser = await chromium.launch({ headless: true,
  ...(process.env.IDONEO_BROWSER_EXECUTABLE ? { executablePath: process.env.IDONEO_BROWSER_EXECUTABLE } : {}),
  args: ["--disable-background-networking"] });
const casos = [], capturas = [], errores = [], respuestas = [], consola = [];
let pagina;
async function contexto(viewport = { width: 1440, height: 1000 }, movil = false) {
  const c = await browser.newContext({ viewport, isMobile: movil, hasTouch: movil, locale: "es-ES", reducedMotion: "reduce" });
  await c.route("**/*", r => new Set([front, api]).has(new URL(r.request().url()).origin) ? r.continue() : r.abort());
  c.on("page", p => {
    p.setDefaultTimeout(7000);
    p.on("pageerror", e => errores.push(e.message));
    p.on("console", m => { if (m.type() === "error") consola.push(m.text()); });
    p.on("response", r => { if (r.status() >= 400) respuestas.push({ ruta: new URL(r.url()).pathname, status: r.status() }); });
  });
  return c;
}
function pasa(nombre) { casos.push(nombre); console.log(`OK ${nombre}`); }
async function foto(p, nombre) {
  const archivo = join(salida, `${nombre}.png`);
  await p.screenshot({ path: archivo, fullPage: true }); capturas.push(archivo);
}
async function alta(c) {
  const r = await c.request.post(`${api}/api/sessions`, { data: { channel: "text" } });
  assert.equal(r.status(), 200); return r.json();
}
async function registrar(c, s) {
  await c.addInitScript(({ s, origen }) => {
    if (location.origin !== origen) return;
    sessionStorage.setItem("idoneo.acceso.v1", JSON.stringify({ clientes: { [s.client_id]: s.access_token }, sesiones: { [s.session_id]: s.client_id } }));
    const { access_token, ...metadata } = s; void access_token;
    localStorage.setItem("idoneo.sesion", JSON.stringify(metadata));
  }, { s, origen: front });
}
const headers = s => ({ Authorization: `Bearer ${s.access_token}` });
async function memoria(c, s) { return c.request.get(`${api}/api/sessions/${s.session_id}/memory`, { headers: headers(s) }); }

try {
  const lento = await contexto();
  await lento.route("**/api/demo/profile", async r => {
    const response = await r.fetch(); await new Promise(ok => setTimeout(ok, 3500));
    await r.fulfill({ response });
  });
  pagina = await lento.newPage(); await pagina.goto(`${front}/escenario?cliente=carmen-68`);
  await pagina.getByRole("heading", { name: /Perfil inversor, listo para validar/ }).waitFor({ timeout: 5500 });
  pasa("El sondeo no descarta todas las respuestas cuando la red tarda más que su intervalo");
  await lento.close();
  // Reproducción: la respuesta pública inicial llega después de restaurar al propietario.
  const carrera = await contexto(); const propietario = await alta(carrera); await registrar(carrera, propietario);
  let respuestaAnterior;
  const anterior = new Promise(ok => { respuestaAnterior = ok; });
  await carrera.route("**/api/demo/profile", async r => {
    const response = await r.fetch(); await new Promise(ok => setTimeout(ok, 800));
    await r.fulfill({ response }); respuestaAnterior();
  });
  pagina = await carrera.newPage(); await pagina.goto(`${front}/onboarding/perfil`);
  await pagina.getByRole("heading", { name: "Recordar cómo prefieres hablar" }).waitFor();
  await anterior; await pagina.waitForTimeout(100);
  assert.equal(await pagina.getByText("80.000 €", { exact: true }).count(), 0, "Una respuesta de Carmen sustituyó el perfil actual");
  pasa("Respuesta tardía del cliente anterior no sustituye el perfil restaurado"); await carrera.close();

  for (const [dispositivo, viewport, movil] of [["escritorio", { width: 1440, height: 1000 }, false], ["movil", { width: 390, height: 844 }, true]]) {
    const c = await contexto(viewport, movil); pagina = await c.newPage();
    await pagina.goto(front);
    await pagina.locator('a[href="/onboarding/entrevista"]:visible').first().click();
    await pagina.waitForURL("**/onboarding/entrevista");
    await pagina.getByRole("button", { name: /Ver la demo guiada/ }).click();
    await pagina.getByRole("button", { name: "Quitar el sonido" }).click();
    await pagina.getByRole("button", { name: "Pausar la demo" }).click();
    await pagina.getByRole("button", { name: "Reanudar la demo" }).waitFor();
    const cabecera = await pagina.getByText(/Demo guiada · \d+ de \d+/).textContent();
    const total = Number(cabecera.match(/de (\d+)/)[1]);
    await foto(pagina, `${dispositivo}-demo-inicial`);
    for (let i = 0; i < 8; i++) await pagina.getByRole("button", { name: "Saltar al siguiente turno" }).click();
    await foto(pagina, `${dispositivo}-demo-progreso`);
    const anotados = await pagina.getByText(/Anotado · \d+ datos/).first().textContent().catch(() => "panel compacto");
    assert.ok(Number(anotados.match(/· (\d+)/)?.[1]) > 0, "El perfil no progresa durante la demo");
    for (let i = 8; i < total; i++) {
      await pagina.getByRole("button", { name: "Saltar al siguiente turno" }).click();
    }
    await pagina.getByRole("heading", { name: "Listo. El perfil de Carmen está preparado." }).waitFor();
    await pagina.getByRole("link", { name: "Ver el perfil de Carmen" }).click();
    await pagina.getByText("80.000 €", { exact: true }).first().waitFor();
    await pagina.getByRole("button", { name: /Ahorro disponible/ }).click();
    await foto(pagina, `${dispositivo}-perfil-evidencia`);
    assert.equal(await pagina.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    pasa(`${dispositivo}: navegación, demo progresiva (${anotados}), final y evidencia`);
    await pagina.goto(`${front}/escenario`);
    await pagina.getByRole("button", { name: /Ver la demo guiada/ }).click();
    await pagina.getByRole("button", { name: "Quitar el sonido" }).click();
    await pagina.getByRole("button", { name: "Pausar la demo" }).click();
    for (let i = 0; i < 9; i++) await pagina.getByRole("button", { name: "Saltar al siguiente turno" }).click();
    const panel = pagina.getByRole("region", { name: "Lo que recibe la entidad" });
    assert.ok((await panel.innerText()).includes("Datos"));
    await foto(pagina, `${dispositivo}-escenario-progreso`);
    await pagina.goto(`${front}/entidad/carmen-68`);
    await pagina.getByRole("button", { name: "Validar perfil" }).waitFor();
    assert.equal(await pagina.getByRole("button", { name: "Validar perfil" }).isDisabled(), true);
    for (const nombre of ["Evidencias", "Historial", "Agente · MCP"]) {
      await pagina.getByRole("tab", { name: nombre }).click();
      if (nombre === "Historial") await pagina.getByText(/ejemplo fijo sin historial persistido/).waitFor();
    }
    await foto(pagina, `${dispositivo}-entidad-restricciones`);
    await pagina.goto(`${front}/onboarding/productos`);
    await pagina.getByRole("heading", { name: "Productos para ti" }).waitFor();
    assert.equal(await pagina.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    pasa(`${dispositivo}: escenario, pestañas de entidad, autovalidación bloqueada y productos`);
    await c.close();
  }

  const c = await contexto(); const a = await alta(c), b = await alta(c); await registrar(c, a);
  pagina = await c.newPage(); await pagina.goto(`${front}/onboarding/perfil`);
  const consentimiento = pagina.getByLabel(/Autorizo a guardar estas preferencias/);
  const guardar = pagina.getByRole("button", { name: "Guardar preferencias" });
  await consentimiento.waitFor(); assert.equal(await guardar.isDisabled(), true); assert.equal(await consentimiento.isChecked(), false);
  await consentimiento.check(); await guardar.click(); await pagina.getByText(/Preferencias guardadas/).waitFor();
  assert.equal(await consentimiento.isChecked(), false);
  await pagina.getByRole("combobox", { name: /Ritmo/ }).selectOption("slow");
  await consentimiento.check(); await guardar.click(); await pagina.getByText(/Preferencias guardadas/).waitFor();
  const antes = await memoria(c, a); const revision = antes.headers().etag;
  assert.equal((await antes.json()).data.communication.pace, "slow");
  await pagina.getByRole("button", { name: "Borrar memoria personal" }).click();
  await pagina.getByText(/Hemos borrado tus preferencias/).waitFor();
  assert.equal(await guardar.isDisabled(), true);
  const ruta = `${api}/api/sessions/${a.session_id}/memory`;
  const body = { consent_given: true, updates: { concerns: ["dato ficticio" ] } };
  assert.equal((await c.request.put(ruta, { headers: headers(a), data: body })).status(), 428);
  assert.equal((await c.request.put(ruta, { headers: { ...headers(a), "If-Match": revision }, data: body })).status(), 412);
  for (const metodo of ["get", "put", "delete"]) {
    const opciones = { headers: { ...headers(b), "If-Match": revision }, ...(metodo === "put" ? { data: body } : {}) };
    assert.equal((await c.request[metodo](ruta, opciones)).status(), 404);
  }
  await consentimiento.check(); await guardar.click(); await pagina.getByText(/Preferencias guardadas/).waitFor();
  const reactivada = await (await memoria(c, a)).json();
  assert.equal(reactivada.enabled, true);
  assert.equal(reactivada.data.communication.pace, "normal");
  assert.equal(reactivada.data.concerns, undefined);
  // Otro poseedor de la misma revisión la cambia; el formulario debe exigir recarga y nueva decisión.
  await consentimiento.check();
  const vigente = await memoria(c, a);
  await c.request.put(ruta, { headers: { ...headers(a), "If-Match": vigente.headers().etag }, data: body });
  await guardar.click(); await pagina.getByRole("alert").filter({ hasText: "412" }).waitFor();
  assert.equal(await consentimiento.isChecked(), false); assert.equal(await guardar.isDisabled(), true);
  await pagina.getByRole("button", { name: "Volver a cargar la memoria" }).click();
  await consentimiento.check(); await guardar.click(); await pagina.getByText(/Preferencias guardadas/).waitFor();
  assert.equal(await pagina.evaluate(() => localStorage.getItem("idoneo.sesion").includes("access_token")), false);
  await foto(pagina, "memoria-consentimiento-reactivada");
  pasa("Memoria: consentimiento, guardado, edición, borrado, 428/412, aislamiento y nueva aceptación tras conflicto");

  const movil = await contexto({ width: 390, height: 844 }, true); await registrar(movil, a);
  const pantallaMovil = await movil.newPage(); await pantallaMovil.goto(`${front}/onboarding/perfil`);
  await pantallaMovil.getByLabel(/Autorizo a guardar estas preferencias/).check();
  await pantallaMovil.getByRole("combobox", { name: /Nivel de detalle/ }).selectOption("high");
  await pantallaMovil.getByRole("button", { name: "Guardar preferencias" }).click();
  await pantallaMovil.getByText(/Preferencias guardadas/).waitFor();
  assert.equal(await pantallaMovil.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await foto(pantallaMovil, "movil-memoria-guardada"); await movil.close();
  pasa("Móvil: consentimiento y edición de memoria con controles reales, sin desbordamiento");

  assert.equal((await c.request.post(`${front}/api/entidad/${a.client_id}/validar`, { headers: headers(a), data: { advisor_id: "asesor-falso" } })).status(), 403);
  assert.equal((await c.request.post(`${api}/api/clients/${a.client_id}/validate`, { headers: headers(a), data: { advisor_id: "asesor-falso" } })).status(), 401);
  for (const herramienta of ["get_client_profile", "get_investment_constraints", "get_evidence", "get_client_context"]) {
    const r = await c.request.post(`${api}/mcp`, { headers: { ...headers(b), Accept: "application/json, text/event-stream" }, data: {
      jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: herramienta, arguments: { client_id: a.client_id, ...(herramienta === "get_evidence" ? { field: "financial.debts_eur" } : {}) } } } });
    assert.equal(r.status(), 200); assert.equal((await r.json()).result.isError, true);
    const permitida = await c.request.post(`${api}/mcp`, { headers: { ...headers(a), Accept: "application/json, text/event-stream" }, data: {
      jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: herramienta, arguments: { client_id: a.client_id, ...(herramienta === "get_evidence" ? { field: "financial.debts_eur" } : {}) } } } });
    assert.equal(permitida.status(), 200); assert.notEqual((await permitida.json()).result.isError, true);
  }
  assert.equal((await c.request.post(`${api}/api/voice/bootstrap`, { headers: headers(b), data: { session_id: a.session_id } })).status(), 404);
  assert.equal((await c.request.post(`${api}/api/voice/bootstrap`, { headers: headers(a), data: { session_id: a.session_id } })).status(), 503);
  const voz = await c.request.get(`${api}/api/voice/context/${a.session_id}`, { headers: headers(a) });
  assert.equal(voz.status(), 200);
  const variables = await voz.json();
  assert.equal(variables.dynamic_variables.personal_memory_enabled, true);
  assert.equal(variables.dynamic_variables.session_id, a.session_id);
  assert.ok(variables.user_id.startsWith("usr_"));
  pasa("REST/MCP/bootstrap: permisos coherentes y autovalidación rechazada sin usar proveedores");
  await c.close();
  assert.deepEqual(errores, [], "Errores JavaScript en el recorrido");
  assert.deepEqual(consola.filter(s => !/Failed to load resource:.*status of 412/.test(s)), [], "Errores de consola no esperados");
  console.log(`Capturas y evidencia: ${salida}`);
} catch (e) {
  if (pagina && !pagina.isClosed()) await foto(pagina, "fallo").catch(() => {});
  console.error(e.message); console.error(`Evidencia del fallo: ${salida}`); process.exitCode = 1;
} finally {
  writeFileSync(join(salida, "resultado.json"), JSON.stringify({ casos, errores, consola, respuestas, capturas }, null, 2));
  await browser.close();
}
