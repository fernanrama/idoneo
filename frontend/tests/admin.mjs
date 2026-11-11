import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const adm = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "servidor/admin.js")))).default;

const ENV = { ADMIN_LOGIN_CLAVE: "clave-del-equipo-de-prueba", ADMIN_TOKEN: "token-servicio-ficticio-0123456789", API_URL_SERVIDOR: "https://backend.example" };
const conf = adm.configAdmin(ENV);
const AHORA = 1_800_000_000_000;
let llamadas;
beforeEach(() => {
  llamadas = [];
  global.fetch = async (url, init) => { llamadas.push({ url: String(url), init }); return new Response("{}", { status: 200 }); };
});
const peticion = (headers = {}, url = "https://web.example/api/x") => new Request(url, { method: "POST", headers });

test("sin clave, con clave corta o igual al token, no hay administración", () => {
  assert.equal(adm.configAdmin({}), null);
  assert.equal(adm.configAdmin({ ...ENV, ADMIN_LOGIN_CLAVE: "corta" }), null);
  assert.equal(adm.configAdmin({ ...ENV, ADMIN_TOKEN: "" }), null);
  assert.equal(adm.configAdmin({ ...ENV, ADMIN_LOGIN_CLAVE: ENV.ADMIN_TOKEN }), null);
  assert.equal(adm.configAdmin({ ...ENV, API_URL_SERVIDOR: "no-es-url" }), null);
  assert.ok(conf);
});

test("la clave se comprueba exactamente", () => {
  assert.equal(adm.claveCorrecta(conf, ENV.ADMIN_LOGIN_CLAVE), true);
  for (const mala of ["", "clave-del-equipo-de-prueb", ENV.ADMIN_LOGIN_CLAVE + " ", null, 123, "x".repeat(300)]) {
    assert.equal(adm.claveCorrecta(conf, mala), false);
  }
});

test("la cookie de sesión es válida hasta que caduca y no se puede falsificar", () => {
  const c = adm.emitirSesion(conf, AHORA);
  assert.equal(adm.sesionValida(conf, c, AHORA), true);
  assert.equal(adm.sesionValida(conf, c, AHORA + (adm.DURACION_SESION_S + 1) * 1000), false);
  const [caduca, firma] = c.split(".");
  assert.equal(adm.sesionValida(conf, `${Number(caduca) + 999999}.${firma}`, AHORA), false);
  assert.equal(adm.sesionValida(conf, `${caduca}.${"A".repeat(43)}`, AHORA), false);
  assert.equal(adm.sesionValida(conf, "", AHORA), false);
  // Cambiar la clave invalida las sesiones emitidas.
  const otra = adm.configAdmin({ ...ENV, ADMIN_LOGIN_CLAVE: "otra-clave-del-equipo" });
  assert.equal(adm.sesionValida(otra, c, AHORA), false);
});

test("sesionAdmin lee la cookie de la petición", () => {
  const c = adm.emitirSesion(conf);
  assert.ok(adm.sesionAdmin(peticion({ cookie: `otra=1; ${adm.COOKIE_ADMIN}=${c}` }), ENV));
  assert.equal(adm.sesionAdmin(peticion({ cookie: `${adm.COOKIE_ADMIN}=falsa` }), ENV), null);
  assert.equal(adm.sesionAdmin(peticion({}), ENV), null);
  assert.equal(adm.sesionAdmin(peticion({ cookie: `${adm.COOKIE_ADMIN}=${c}` }), {}), null);
});

test("las escrituras exigen el mismo origen", () => {
  assert.equal(adm.mismoOrigen(peticion({ origin: "https://web.example", host: "web.example" })), true);
  assert.equal(adm.mismoOrigen(peticion({ origin: "https://atacante.example", host: "web.example" })), false);
  assert.equal(adm.mismoOrigen(peticion({ host: "web.example" })), false);
  assert.equal(adm.mismoOrigen(peticion({ origin: "https://web.example", host: "x", "x-forwarded-host": "web.example" })), true);
});

test("la cookie es HttpOnly, SameSite=Strict y Secure en https", () => {
  const c = adm.cookieSesion("v", true);
  for (const p of ["HttpOnly", "SameSite=Strict", "Secure", "Path=/"]) assert.ok(c.includes(p), p);
  assert.ok(adm.cookieBorrada(false).includes("Max-Age=0"));
});

test("al backend solo va ADMIN_TOKEN y el cuerpo permitido", async () => {
  await adm.llamarEntidad(conf, "/clientes/cliente-a/validar", "POST", { expected_version: 3 });
  assert.equal(llamadas[0].url, "https://backend.example/api/entidad/clientes/cliente-a/validar");
  assert.deepEqual(Object.keys(llamadas[0].init.headers).sort(), ["Content-Type", "X-Admin-Token"]);
  assert.deepEqual(JSON.parse(llamadas[0].init.body), { expected_version: 3 });
});
