import { clienteValido, configAsesorDemo, esPeticionLocal, llamarBackend, respuestaJson } from "@/lib/servidor/asesorDemo";
import { llamarEntidad, sesionAdmin } from "@/lib/servidor/admin";

/** Expediente del cliente ficticio para la vista de la entidad (perfil, restricciones e historial). */
export async function GET(req: Request, ctx: RouteContext<"/api/entidad/[cid]/asesor">) {
  const { cid } = await ctx.params;
  const admin = sesionAdmin(req);
  if (admin) {
    if (!clienteValido(cid)) return respuestaJson({ detail: "Recurso no encontrado" }, 404);
    return llamarEntidad(admin, `/clientes/${encodeURIComponent(cid)}`);
  }
  const conf = configAsesorDemo();
  if (!conf) return respuestaJson({ detail: "Modo asesor de demo desactivado." }, 404);
  if (!esPeticionLocal(req)) return respuestaJson({ detail: "El modo asesor de demo solo funciona en local." }, 403);
  if (!clienteValido(cid)) return respuestaJson({ detail: "Recurso no encontrado" }, 404);
  return llamarBackend(conf, `/clientes/${encodeURIComponent(cid)}`);
}
