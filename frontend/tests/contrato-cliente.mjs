import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const { api, ErrorAPI } = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "api.js")))).default;
const cred = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "credenciales.js")))).default;
const { opcionesVoz } = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "iniciarVoz.js")))).default;

function almacen() {
  const datos = new Map();
  return { getItem: (k) => datos.get(k) ?? null, setItem: (k,v) => datos.set(k,String(v)), removeItem: (k) => datos.delete(k), valores: () => [...datos.values()].join(" "), clear: () => datos.clear() };
}
const alta = { client_id: "cliente-A", session_id: "sesion-A", started_at: "2026-11-10", access_token: "prueba-posesion-A" };
let llamadas;
function respuesta(body, status = 200, headers = {}) { return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } }); }
function mock(fn) {
  global.fetch = async (url, init) => {
    llamadas.push({ url: String(url), init });
    return fn(String(url), init);
  };
}
function autenticar() { cred.registrarSesion(alta); }
function auth(n=0) { return llamadas[n].init.headers.Authorization; }

beforeEach(() => {
  global.window = { sessionStorage: almacen(), localStorage: almacen() };
  llamadas = [];
  mock(() => { throw new Error("Petición de red inesperada"); });
});

test("alta: recibe credencial una vez y devuelve solo metadatos", async () => {
  mock(() => respuesta(alta));
  const s = await api.crearSesion(undefined, "text");
  assert.equal(s.access_token, undefined);
  assert.equal(auth(), undefined);
  assert.deepEqual(JSON.parse(llamadas[0].init.body), { channel: "text" });
  assert.equal(cred.tokenSesion(s.session_id), alta.access_token);
  assert.equal(window.localStorage.valores(), "");
  assert.ok(window.sessionStorage.valores().includes(alta.access_token));
});

test("localStorage conserva metadatos sin token y recarga solo con credencial de pestaña", () => {
  const s = cred.persistirSesion(alta);
  assert.equal(s.access_token, undefined);
  assert.ok(!window.localStorage.valores().includes(alta.access_token));
  assert.deepEqual(cred.restaurarSesion(), s);
  window.sessionStorage.clear();
  assert.equal(cred.restaurarSesion(), null);
  assert.equal(window.localStorage.valores(), "");
});

test("metadatos manipulados o antiguos no renuevan credenciales", () => {
  window.localStorage.setItem(cred.CLAVE_SESION, JSON.stringify(alta));
  assert.equal(cred.restaurarSesion(), null);
  assert.equal(cred.tokenCliente(alta.client_id), null);
  assert.ok(!window.localStorage.valores().includes(alta.access_token));
});

test("reanudar cliente requiere bearer existente y no reemplaza su credencial", async () => {
  autenticar();
  mock(() => respuesta({ ...alta, session_id: "sesion-B", access_token: undefined }));
  await api.crearSesion(alta.client_id, "voice");
  assert.equal(auth(), `Bearer ${alta.access_token}`);
  assert.equal(cred.tokenSesion("sesion-B"), alta.access_token);
});

test("conocer client_id o session_id no inicia peticiones protegidas sin token", async () => {
  await assert.rejects(async () => api.crearSesion(alta.client_id), e => e.status === 401);
  await assert.rejects(async () => api.perfil(alta.client_id), e => e.status === 401);
  await assert.rejects(async () => api.memoria(alta.session_id), e => e.status === 401);
  assert.equal(llamadas.length, 0);
});

test("bearer se envía solo en cabecera para perfil, restricciones, turnos, chat y pendientes", async () => {
  autenticar();
  mock(() => respuesta({}));
  await api.perfil(alta.client_id);
  await api.restricciones(alta.client_id);
  await api.versiones(alta.client_id);
  await api.enviarTurno(alta.session_id, { speaker: "client", text: "hola", t_start: 0, t_end: 1 });
  await api.chat(alta.session_id, "hola");
  await api.pendientes(alta.session_id);
  for (const {url,init} of llamadas) {
    assert.equal(init.headers.Authorization, `Bearer ${alta.access_token}`);
    assert.ok(!url.includes(alta.access_token));
    assert.ok(!String(init.body).includes(alta.access_token));
  }
});

test("demo anónima usa fixture fijo; jamás cliente persistido o credencial nueva", async () => {
  mock(() => respuesta({}));
  await api.perfil(cred.CLIENTE_DEMO);
  await api.restricciones(cred.CLIENTE_DEMO);
  await api.perfilDemo();
  assert.deepEqual(llamadas.map(x => new URL(x.url).pathname), ["/api/demo/profile", "/api/demo/constraints", "/api/demo/profile"]);
  assert.ok(llamadas.every(x => !x.init.headers.Authorization));
  await assert.rejects(async () => api.validar(cred.CLIENTE_DEMO, "asesor-demo"), e => e.status === 401);
  assert.equal(llamadas.length, 3);
});

test("memoria usa ETag exacto y PUT lleva consentimiento explícito", async () => {
  autenticar();
  mock(() => respuesta({ enabled: false, version: 0, data: {} }, 200, { ETag: '"personal-0"' }));
  const m = await api.memoria(alta.session_id);
  assert.equal(m.etag, '"personal-0"');
  await api.guardarMemoria(alta.session_id, m.etag, false, {});
  assert.equal(llamadas[1].init.headers["If-Match"], '"personal-0"');
  assert.equal(JSON.parse(llamadas[1].init.body).consent_given, false);
  await api.borrarMemoria(alta.session_id, m.etag);
  assert.equal(llamadas[2].init.headers["If-Match"], '"personal-0"');
});

test("sin ETag servidor o revisión válida no puede escribirse memoria", async () => {
  autenticar();
  mock(() => respuesta({ enabled: false, version: 0, data: {} }));
  await assert.rejects(api.memoria(alta.session_id), /revisión válida/);
  await assert.rejects(async () => api.guardarMemoria(alta.session_id, "", true, {}), /cargar la memoria/);
  await assert.rejects(async () => api.borrarMemoria(alta.session_id, "*"), /cargar la memoria/);
  assert.equal(llamadas.length, 1);
});

test("412 se devuelve sin refrescar, repetir escritura ni reconsentir", async () => {
  autenticar();
  mock(() => respuesta({ detail: "conflicto" }, 412));
  await assert.rejects(api.guardarMemoria(alta.session_id, '"personal-1"', true, {}), e => e instanceof ErrorAPI && e.status === 412);
  assert.equal(llamadas.length, 1);
  assert.equal(llamadas[0].init.method, "PUT");
});

test("errores remotos no exponen cuerpos con credenciales", async () => {
  autenticar();
  mock(() => respuesta({ detail: alta.access_token }, 401));
  await assert.rejects(api.perfil(alta.client_id), e => e.status === 401 && !e.message.includes(alta.access_token));
});

test("voz usa bootstrap autenticado con variables, usuario y región; nunca signed-url", async () => {
  autenticar();
  mock(() => respuesta({ signed_url: "wss://voz.invalid/prueba", user_id: "usr_sintetico", dynamic_variables: { session_id: alta.session_id }, server_location: "eu-residency" }));
  const opciones = await opcionesVoz(alta.session_id);
  assert.deepEqual(opciones, { signedUrl: "wss://voz.invalid/prueba", userId: "usr_sintetico", dynamicVariables: { session_id: alta.session_id }, serverLocation: "eu-residency" });
  assert.equal(new URL(llamadas[0].url).pathname, "/api/voice/bootstrap");
  assert.equal(auth(), `Bearer ${alta.access_token}`);
});

test("fallback voz conserva contexto autenticado para agente público", async () => {
  autenticar();
  mock(url => url.endsWith("/bootstrap") ? respuesta({}, 503) : respuesta({ user_id: "usr_sintetico", dynamic_variables: { session_id: alta.session_id } }));
  assert.deepEqual(await opcionesVoz(alta.session_id, "agente-prueba"), { agentId: "agente-prueba", userId: "usr_sintetico", dynamicVariables: { session_id: alta.session_id } });
  assert.equal(llamadas.length, 2);
  assert.ok(llamadas.every(x => x.init.headers.Authorization === `Bearer ${alta.access_token}`));
});

test("voz no degrada autorización rechazada a agente público", async () => {
  autenticar();
  mock(() => respuesta({}, 403));
  await assert.rejects(opcionesVoz(alta.session_id, "agente-prueba"), e => e.status === 403);
  assert.equal(llamadas.length, 1);
});

test("validación Next recibe bearer de propietario; jamás token de entidad desde cliente", async () => {
  autenticar();
  mock(() => respuesta({}));
  await api.validar(alta.client_id, "asesor-demo");
  assert.equal(auth(), `Bearer ${alta.access_token}`);
  assert.equal(llamadas[0].init.headers["X-Admin-Token"], undefined);
  assert.equal(llamadas[0].url, "/api/entidad/cliente-A/validar");
});

test("proxy de entidad no convierte la credencial del cliente en permiso de asesor", async () => {
  process.env.ADMIN_TOKEN = "entidad-sintetica";
  const { validacionNoDisponible } = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "servidor/entidad.js")))).default;
  mock(() => respuesta({ ok: true }));
  const r = validacionNoDisponible();
  assert.equal(r.status, 403);
  assert.equal(llamadas.length, 0);
  assert.ok(!(await r.text()).includes("entidad-sintetica"));
  delete process.env.ADMIN_TOKEN;
});

test("proxy no añade permiso de servicio a una petición anónima local", async () => {
  process.env.ADMIN_TOKEN = "entidad-sintetica";
  try {
    const { validacionNoDisponible } = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "servidor/entidad.js")))).default;
    const r = validacionNoDisponible();
    assert.equal(r.status, 403);
    assert.equal(r.headers.get("Cache-Control"), "no-store");
    assert.equal(llamadas.length, 0);
  } finally {
    delete process.env.ADMIN_TOKEN;
  }
});

test("historial de demo declara un ejemplo fijo y no lee versiones privadas", async () => {
  mock(() => respuesta({ version: 7, created_at: "2026-11-10", status: "pending_validation" }));
  const versiones = await api.versiones(cred.CLIENTE_DEMO);
  assert.equal(llamadas.length, 1);
  assert.equal(new URL(llamadas[0].url).pathname, "/api/demo/profile");
  assert.equal(versiones[0].version, 7);
  assert.match(versiones[0].reason, /SIMULADOS.*sin historial persistido/);
});
