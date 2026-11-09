import { reenviar } from "@/lib/servidor/entidad";

/** Recarga a Carmen (datos simulados) como versión nueva (añade X-Admin-Token en el servidor). */
export async function POST(req: Request) {
  return reenviar(req, "/api/demo/reset", {});
}
