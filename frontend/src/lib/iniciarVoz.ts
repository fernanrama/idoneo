import { api, ErrorAPI } from "./api";
import type { ContextoVoz } from "./tipos";

/** Preparar ambas variantes del SDK sin volver a la ruta obsoleta de URL firmada. */
export async function opcionesVoz(sessionId: string, agentId?: string) {
  let contexto: ContextoVoz;
  let signedUrl: string | null = null;
  try {
    const bootstrap = await api.bootstrapVoz(sessionId);
    contexto = bootstrap;
    signedUrl = bootstrap.signed_url;
  } catch (e) {
    // Un rechazo de autorización no debe convertirse en conexión de agente público.
    if (e instanceof ErrorAPI && (e.status === 401 || e.status === 403)) throw e;
    contexto = await api.contextoVoz(sessionId);
  }
  const comun = {
    userId: contexto.user_id,
    dynamicVariables: contexto.dynamic_variables,
    ...(contexto.server_location ? { serverLocation: contexto.server_location } : {}),
  };
  if (signedUrl) return { signedUrl, ...comun };
  if (!agentId) throw new Error("Falta configurar el agente de voz.");
  return { agentId, ...comun };
}
