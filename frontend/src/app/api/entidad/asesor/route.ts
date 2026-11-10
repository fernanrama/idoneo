import { connection } from "next/server";
import { estadoAsesorDemo, respuestaJson } from "@/lib/servidor/asesorDemo";

/** ¿Está habilitado el modo asesor de demo? Lo comprueba el servidor contra el backend; sin secretos. */
export async function GET(req: Request) {
  // Nunca prerenderizar: el resultado depende del entorno de ejecución y del backend, no del build.
  await connection();
  return respuestaJson(await estadoAsesorDemo(req));
}
