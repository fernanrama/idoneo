import { clienteValido, configAsesorDemo, esPeticionLocal, llamarBackend, respuestaJson, versionEsperada } from "@/lib/servidor/asesorDemo";
import { validacionNoDisponible } from "@/lib/servidor/entidad";

/**
 * No convertir la credencial de un cliente en permiso de revisión de la entidad.
 * Solo con el modo asesor de demo activo (DEMO_ADVISOR_MODE=1) el servidor valida, con su propio
 * token y para los clientes ficticios que permita el backend. La cabecera Authorization se ignora y del
 * cuerpo solo se reenvía `expected_version` (entero): si el perfil cambió mientras el asesor lo revisaba,
 * el backend responde 409 y no valida una versión que el asesor no ha visto.
 */
export async function POST(req: Request, ctx: RouteContext<"/api/entidad/[cid]/validar">) {
  const conf = configAsesorDemo();
  if (!conf) return validacionNoDisponible();
  if (!esPeticionLocal(req)) return respuestaJson({ detail: "El modo asesor de demo solo funciona en local." }, 403);
  const { cid } = await ctx.params;
  if (!clienteValido(cid)) return respuestaJson({ detail: "Recurso no encontrado" }, 404);
  const version = versionEsperada(await req.json().catch(() => null));
  return llamarBackend(conf, `/clientes/${encodeURIComponent(cid)}/validar`, "POST",
    version ? { expected_version: version } : undefined);
}
