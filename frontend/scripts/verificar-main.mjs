// Comprueba los contratos sobre la interfaz #22/#23 sin fusionar ramas ni tocar la demo.
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repo = resolve(frontend, "..");
const referencia = process.argv[2] ?? "origin/main";
const font = process.env.IDONEO_FONT_FIXTURE;
if (!font) throw new Error("Indica IDONEO_FONT_FIXTURE con un .woff2 local para una compilación sin red.");

function ejecutar(cmd, args, cwd = repo, opciones = {}) {
  const r = spawnSync(cmd, args, { cwd, stdio: "inherit", ...opciones });
  if (r.status !== 0) throw new Error(`${cmd} ${args.join(" ")} terminó con ${r.status}: ${r.error ?? ""}`);
  return r;
}

const sha = ejecutar("git", ["rev-parse", "--verify", `${referencia}^{commit}`], repo,
  { encoding: "utf8", stdio: "pipe" }).stdout.trim();
const temporal = mkdtempSync(join(tmpdir(), "idoneo-main-compat-"));
console.log(`Compatibilidad sobre ${sha}; artefactos conservados en ${temporal}`);
const archivo = ejecutar("git", ["archive", sha, "frontend"], repo,
  { stdio: "pipe", maxBuffer: 64 * 1024 * 1024 }).stdout;
ejecutar("tar", ["-xf", "-", "-C", temporal], repo, { input: archivo, stdio: ["pipe", "inherit", "inherit"] });
const destino = join(temporal, "frontend");
const comunes = [
  "src/lib/api.ts", "src/lib/credenciales.ts", "src/lib/onboarding.tsx", "src/lib/tipos.ts",
  "src/lib/useEntrevista.ts", "src/lib/iniciarVoz.ts", "src/lib/demo.ts", "src/lib/servidor/entidad.ts",
  "src/components/memoria-personal.tsx", "src/components/memoria-personal.module.css",
  "src/app/api/entidad/reset/route.ts", "scripts/test-contrato.mjs", "tests/contrato-cliente.mjs",
];
for (const ruta of comunes) {
  mkdirSync(dirname(join(destino, ruta)), { recursive: true });
  copyFileSync(join(frontend, ruta), join(destino, ruta));
}

// Conserva íntegro el diseño de main. Solo explicita la demo de lectura y oculta una acción no autorizada.
const rutaEntidad = join(destino, "src/app/entidad/[cid]/VistaEntidad.tsx");
const original = readFileSync(rutaEntidad, "utf8");
let entidad = original;
const cambios = [
  ['import { api } from "@/lib/api";', 'import { api } from "@/lib/api";\nimport { CLIENTE_DEMO, tokenCliente } from "@/lib/credenciales";'],
  ['  const alertas = perfil?.alerts.filter', '  const soloEjemplo = cid === CLIENTE_DEMO && !tokenCliente(cid);\n  const alertas = perfil?.alerts.filter'],
  ['            <div className={s.accion}>', '            {soloEjemplo && <p role="note">Ejemplo ficticio fijo de solo lectura; no representa el expediente persistido de un cliente.</p>}\n            <div className={s.accion}>'],
  ['{perfil?.status === "pending_validation" && (', '{perfil?.status === "pending_validation" && tokenCliente(cid) && ('],
];
for (const [antes, despues] of cambios) {
  if (entidad.split(antes).length !== 2) throw new Error(`main cambió; revisar adaptación de entidad: ${antes}`);
  entidad = entidad.replace(antes, despues);
}
writeFileSync(rutaEntidad, entidad);
writeFileSync(join(temporal, "entidad-original.tsx"), original);
const diff = spawnSync("diff", ["-u", "--label", "main/frontend/src/app/entidad/[cid]/VistaEntidad.tsx",
  "--label", "propuesta/frontend/src/app/entidad/[cid]/VistaEntidad.tsx",
  join(temporal, "entidad-original.tsx"), rutaEntidad], { encoding: "utf8" });
if (diff.status !== 1) throw new Error("No se pudo preparar el diff revisable de entidad.");
writeFileSync(join(temporal, "adaptacion-entidad.patch"), diff.stdout);
symlinkSync(realpathSync(join(frontend, "node_modules")), join(destino, "node_modules"), "dir");

// Hook de pruebas del Next instalado: sustituye Google Fonts por un archivo local.
// Verifica compilación/prerender, no tipografía ni apariencia visual.
const mock = join(temporal, "fuentes-locales.cjs");
writeFileSync(mock, `module.exports = new Proxy({}, { get(_target, url) {
  const family = new URL(url).searchParams.get('family').split(':')[0];
  return '/* latin */\\n@font-face { font-family: "' + family + '"; font-style: normal; font-weight: 100 900; src: url(${realpathSync(font)}) format("woff2"); }';
} });\n`);
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: "1", NEXT_FONT_GOOGLE_MOCKED_RESPONSES: mock,
  ANTHROPIC_API_KEY: "", ELEVENLABS_API_KEY: "", ELEVENLABS_AGENT_ID: "",
  NEXT_PUBLIC_ELEVENLABS_AGENT_ID: "" };
ejecutar(process.execPath, ["scripts/test-contrato.mjs"], destino, { env });
ejecutar(process.execPath, ["node_modules/eslint/bin/eslint.js", "."], destino, { env });
ejecutar(process.execPath, ["node_modules/next/dist/bin/next", "build", "--webpack"], destino, { env });
writeFileSync(join(temporal, "resultado.json"), JSON.stringify({ main: sha, archivos: comunes,
  entidad: "adaptacion-entidad.patch", contrato: "pasa", lint: "pasa", build: "pasa", fuentes: "fixture local" }, null, 2));
console.log(`Compatibilidad verificada. ${join(temporal, "resultado.json")}`);
