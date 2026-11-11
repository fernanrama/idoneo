import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const build = mkdtempSync(join(tmpdir(), "idoneo-cliente-test-"));
try {
  const compilacion = spawnSync(process.execPath, [
    "node_modules/typescript/bin/tsc", "--outDir", build, "--module", "commonjs",
    "--moduleResolution", "node", "--target", "ES2020", "--lib", "ES2020,DOM",
    "--esModuleInterop", "--skipLibCheck", "--strict",
    "src/lib/tipos.ts", "src/lib/credenciales.ts", "src/lib/api.ts", "src/lib/iniciarVoz.ts", "src/lib/servidor/entidad.ts", "src/lib/servidor/asesorDemo.ts", "src/lib/validacion.ts", "src/lib/servidor/admin.ts",
  ], { stdio: "inherit" });
  if (compilacion.status !== 0) process.exitCode = compilacion.status ?? 1;
  else {
    const pruebas = spawnSync(process.execPath, ["--test", "tests/contrato-cliente.mjs", "tests/asesor-demo.mjs", "tests/validacion.mjs", "tests/admin.mjs"], {
      stdio: "inherit", env: { ...process.env, IDONEO_CLIENT_BUILD: build },
    });
    process.exitCode = pruebas.status ?? 1;
  }
} finally {
  rmSync(build, { recursive: true, force: true });
}
