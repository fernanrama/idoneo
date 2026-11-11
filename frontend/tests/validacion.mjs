import { test } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const { esValidable } = (await import(pathToFileURL(join(process.env.IDONEO_CLIENT_BUILD, "validacion.js")))).default;

const perfil = (status, complete = true) => ({ status, assessments: { suitability: { complete } } });

test("review_due completo ofrece «Validar perfil» (regresión: microentrevista → validación del asesor)", () => {
  assert.equal(esValidable(perfil("review_due")), true);
});

test("review_due incompleto no se ofrece, igual que rechaza el backend", () => {
  assert.equal(esValidable(perfil("review_due", false)), false);
});

test("se mantienen los estados que ya se validaban", () => {
  assert.equal(esValidable(perfil("pending_validation")), true);
  assert.equal(esValidable(perfil("pending_validation", false)), true);
  assert.equal(esValidable(perfil("draft")), true);
  assert.equal(esValidable(perfil("draft", false)), false);
});

test("un perfil activo no pide otra validación (confirmación pura, D3)", () => {
  assert.equal(esValidable(perfil("active")), false);
});

test("sin perfil cargado no hay botón", () => {
  assert.equal(esValidable(null), false);
  assert.equal(esValidable(undefined), false);
});

test("recorrido active → review_due → active: el botón aparece y desaparece al validar", () => {
  const recorrido = ["active", "review_due", "active"].map((s) => esValidable(perfil(s)));
  assert.deepEqual(recorrido, [false, true, false]);
});
