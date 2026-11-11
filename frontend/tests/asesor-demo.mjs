// Modo asesor de demo: reglas del servidor Next y del cliente. Sin red: fetch simulado.
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const cargar = async (m) => (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, m)))).default;
const demo = await cargar("servidor/asesorDemo.js");
const { api } = await cargar("api.js");
const cred = await cargar("credenciales.js");

const TOKEN = "asesor-demo-sintetico-del-front-0123456789abcdef";
const ENV = { DEMO_ADVISOR_MODE: "1", DEMO_ADVISOR_TOKEN: TOKEN, API_URL_SERVIDOR: "http://127.0.0.1:8123" };
let llamadas;
function respuesta(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}
function mock(fn) {
  global.fetch = async (url, init) => { llamadas.push({ url: String(url), init }); return fn(String(url), init); };
}
function peticion(method = "GET", headers = {}) {
  return new Request("http://localhost:3000/api/entidad/carmen-68/validar", { method, headers: { host: "localhost:3000", ...headers } });
}
const mismoOrigen = { origin: "http://localhost:3000", "sec-fetch-site": "same-origin" };
function almacen() {
  const datos = new Map();
  return { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k), clear: () => datos.clear() };
}

beforeEach(() => {
  llamadas = [];
  global.window = { sessionStorage: almacen(), localStorage: almacen() };
  mock(() => { throw new Error("Petición de red inesperada"); });
});

test("apagado por defecto y con cualquier valor distinto de 1", () => {
  assert.equal(demo.configAsesorDemo({}), null);
  for (const v of ["0", "true", "yes", " 1", ""]) assert.equal(demo.configAsesorDemo({ ...ENV, DEMO_ADVISOR_MODE: v }), null);
  assert.deepEqual(demo.configAsesorDemo(ENV), { token: TOKEN, api: "http://127.0.0.1:8123" });
});

test("configuración insegura deja el modo apagado", () => {
  assert.equal(demo.configAsesorDemo({ ...ENV, DEMO_ADVISOR_TOKEN: "corto" }), null);
  assert.equal(demo.configAsesorDemo({ ...ENV, ADMIN_TOKEN: TOKEN }), null);
  for (const api of ["https://idoneo.example.com", "http://192.168.1.10:8000", "ftp://localhost", "no es url"]) {
    assert.equal(demo.configAsesorDemo({ ...ENV, API_URL_SERVIDOR: api }), null, api);
  }
});

test("solo peticiones locales, sin proxy, y escrituras del mismo origen", () => {
  assert.equal(demo.esPeticionLocal(peticion("GET")), true);
  assert.equal(demo.esPeticionLocal(peticion("GET", { "x-forwarded-for": "127.0.0.1", "x-forwarded-host": "localhost:3000" })), true);
  assert.equal(demo.esPeticionLocal(peticion("POST", mismoOrigen)), true);
  const rechazadas = [
    peticion("GET", { host: "idoneo.example.com" }),
    peticion("GET", { "x-forwarded-for": "203.0.113.9" }),
    peticion("GET", { "x-forwarded-for": "127.0.0.1, 203.0.113.9" }),
    peticion("GET", { "x-forwarded-host": "idoneo.example.com" }),
    peticion("GET", { forwarded: "for=203.0.113.9" }),
    peticion("GET", { "x-real-ip": "127.0.0.1" }),
    peticion("POST"),                                                     // sin Origin
    peticion("POST", { origin: "https://atacante.example" }),             // otro sitio
    peticion("POST", { origin: "http://localhost:3000", "sec-fetch-site": "cross-site" }),
    peticion("POST", { origin: "http://localhost:4000" }),
  ];
  rechazadas.forEach((r, i) => assert.equal(demo.esPeticionLocal(r), false, `caso ${i}`));
});

test("el puente al backend solo lleva el token de asesor y no reenvía nada del navegador", async () => {
  mock(() => respuesta({ status: "active" }));
  const r = await demo.llamarBackend(demo.configAsesorDemo(ENV), "/clientes/carmen-68/validar", "POST");
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("Cache-Control"), "no-store");
  assert.equal(llamadas.length, 1);
  assert.equal(llamadas[0].url, "http://127.0.0.1:8123/api/demo/asesor/clientes/carmen-68/validar");
  assert.deepEqual(Object.keys(llamadas[0].init.headers), ["X-Demo-Advisor-Token"]);
  assert.equal(llamadas[0].init.body, undefined);
});

test("validar reenvía solo expected_version entero y nada más del navegador", async () => {
  assert.equal(demo.versionEsperada({ expected_version: 7 }), 7);
  for (const malo of [null, undefined, {}, { expected_version: 0 }, { expected_version: -1 }, { expected_version: 1.5 },
    { expected_version: "7" }, { expected_version: Number.MAX_SAFE_INTEGER + 1 }]) {
    assert.equal(demo.versionEsperada(malo), undefined);
  }
  mock(() => respuesta({ status: "active" }));
  const r = await demo.llamarBackend(demo.configAsesorDemo(ENV), "/clientes/carmen-68/validar", "POST", { expected_version: 7 });
  assert.equal(r.status, 200);
  assert.deepEqual(JSON.parse(llamadas[0].init.body), { expected_version: 7 });
  assert.deepEqual(Object.keys(llamadas[0].init.headers).sort(), ["Content-Type", "X-Demo-Advisor-Token"]);
});

test("el navegador envía la versión que ve el asesor al validar", async () => {
  mock(() => respuesta({ status: "active" }));
  await api.validarComoAsesor("carmen-68", 4);
  assert.deepEqual(JSON.parse(llamadas[0].init.body), { expected_version: 4 });
});

test("un 409 al validar llega como ErrorAPI con su estado, para recargar el perfil", async () => {
  mock(() => respuesta({ detail: "conflicto" }, 409));
  await assert.rejects(api.validarComoAsesor("carmen-68", 4), (e) => e.status === 409);
});

test("el estado visible para el navegador nunca contiene el token y depende del backend", async () => {
  mock(() => respuesta({ enabled: true, simulated: true, clients: ["carmen-68", "../x"], advisor_id: "asesor-demo" }));
  const ok = await demo.estadoAsesorDemo(peticion("GET"), ENV);
  assert.deepEqual(ok, { enabled: true, clients: ["carmen-68"], advisor_id: "asesor-demo" });
  assert.ok(!JSON.stringify(ok).includes(TOKEN));
  mock(() => respuesta({ detail: "no" }, 401));                         // el backend no acepta el token
  assert.deepEqual(await demo.estadoAsesorDemo(peticion("GET"), ENV), { enabled: false, clients: [] });
  llamadas = [];
  assert.deepEqual(await demo.estadoAsesorDemo(peticion("GET"), {}), { enabled: false, clients: [] });
  assert.deepEqual(await demo.estadoAsesorDemo(peticion("GET", { host: "idoneo.example.com" }), ENV), { enabled: false, clients: [] });
  assert.equal(llamadas.length, 0);                                     // apagado o remoto: ni siquiera pregunta
});

test("backend caído: 502 sin detalles internos", async () => {
  mock(() => { throw new Error(`conexión rechazada ${TOKEN}`); });
  const r = await demo.llamarBackend(demo.configAsesorDemo(ENV), "/estado");
  assert.equal(r.status, 502);
  assert.ok(!(await r.text()).includes(TOKEN));
});

test("el cliente del navegador no envía credenciales en el modo asesor, aunque tenga las del cliente", async () => {
  cred.registrarSesion({ client_id: "carmen-68", session_id: "s-1", started_at: "2026-11-10", access_token: "posesion-del-cliente" });
  mock(() => respuesta({ enabled: true, clients: ["carmen-68"], profile: {}, constraints: {}, versions: [] }));
  await api.modoAsesor();
  await api.expedienteAsesor("carmen-68");
  await api.validarComoAsesor("carmen-68");
  await api.reiniciarComoAsesor();
  assert.deepEqual(llamadas.map((l) => [l.init?.method ?? "GET", l.url]), [
    ["GET", "/api/entidad/asesor"], ["GET", "/api/entidad/carmen-68/asesor"],
    ["POST", "/api/entidad/carmen-68/validar"], ["POST", "/api/entidad/reset"],
  ]);
  for (const l of llamadas) {
    const h = l.init?.headers ?? {};
    assert.equal(h.Authorization, undefined);
    assert.equal(h["X-Admin-Token"], undefined);
    assert.equal(h["X-Demo-Advisor-Token"], undefined);
    assert.ok(!String(l.init?.body ?? "").includes("posesion-del-cliente"));
  }
});
