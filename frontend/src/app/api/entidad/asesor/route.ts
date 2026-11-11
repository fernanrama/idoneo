import { connection } from "next/server";
import { estadoAsesorDemo, respuestaJson } from "@/lib/servidor/asesorDemo";
import { sesionAdmin } from "@/lib/servidor/admin";

/** ¿Está habilitado el modo asesor de demo? Lo comprueba el servidor contra el backend; sin secretos. */
export async function GET(req: Request) {
  // Nunca prerenderizar: el resultado depende del entorno de ejecución y del backend, no del build.
  await connection();
  // Sesión de administración (web publicada): puede ver y validar cualquier cliente.
  if (sesionAdmin(req)) return respuestaJson({ enabled: true, clients: [], all: true, admin: true, advisor_id: "asesor-web" });
  return respuestaJson(await estadoAsesorDemo(req));
}
