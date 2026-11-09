import { reenviar } from "@/lib/servidor/entidad";

/** Valida el perfil del cliente en nombre de la entidad (añade X-Admin-Token en el servidor). */
export async function POST(req: Request, ctx: RouteContext<"/api/entidad/[cid]/validar">) {
  const { cid } = await ctx.params;
  const { advisor_id = "asesor-demo", changes = [] } = await req.json().catch(() => ({}));
  return reenviar(req, `/api/clients/${encodeURIComponent(cid)}/validate`, { advisor_id, changes });
}
