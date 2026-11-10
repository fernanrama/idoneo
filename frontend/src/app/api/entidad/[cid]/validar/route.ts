import { clienteValido, configAsesorDemo, esPeticionLocal, llamarBackend, respuestaJson } from "@/lib/servidor/asesorDemo";
import { validacionNoDisponible } from "@/lib/servidor/entidad";

/**
 * No convertir la credencial de un cliente en permiso de revisión de la entidad.
 * Solo con el modo asesor de demo activo (DEMO_ADVISOR_MODE=1) el servidor valida, con su propio
 * token y para los clientes ficticios que permita el backend. La cabecera Authorization y el cuerpo
 * del navegador se ignoran.
 */
export async function POST(req: Request, ctx: RouteContext<"/api/entidad/[cid]/validar">) {
  const conf = configAsesorDemo();
  if (!conf) return validacionNoDisponible();
  if (!esPeticionLocal(req)) return respuestaJson({ detail: "El modo asesor de demo solo funciona en local." }, 403);
  const { cid } = await ctx.params;
  if (!clienteValido(cid)) return respuestaJson({ detail: "Recurso no encontrado" }, 404);
  return llamarBackend(conf, `/clientes/${encodeURIComponent(cid)}/validar`, "POST");
}
