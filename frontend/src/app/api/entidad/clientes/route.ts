import { connection } from "next/server";
import { respuestaJson } from "@/lib/servidor/asesorDemo";
import { llamarEntidad, sesionAdmin } from "@/lib/servidor/admin";

/** Bandeja de la entidad: clientes recientes con el estado de su perfil. Solo con sesión de administración. */
export async function GET(req: Request) {
  await connection();
  const admin = sesionAdmin(req);
  if (!admin) return respuestaJson({ detail: "Inicia sesión como entidad." }, 401);
  return llamarEntidad(admin, "/clientes?limite=50");
}
