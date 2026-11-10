/**
 * Modo asesor de demostración: solo servidor (rutas de /api/entidad). DATOS SIMULADOS.
 *
 * El token DEMO_ADVISOR_TOKEN vive en el entorno del servidor Next (sin prefijo NEXT_PUBLIC_, así que
 * nunca entra en el bundle del navegador) y solo se envía a un backend local. Las peticiones del
 * navegador no llevan ninguna credencial de asesor y la del cliente nunca se reenvía.
 * Apagado por defecto: sin DEMO_ADVISOR_MODE=1 todo sigue como en la PR #21 (403).
 * Ver docs/MODO_ASESOR_DEMO.md.
 */

export const CABECERA_ASESOR = "X-Demo-Advisor-Token";
const HOSTS_LOCALES = new Set(["localhost", "127.0.0.1", "[::1]", "::1"]);
const IPS_LOCALES = new Set(["127.0.0.1", "::1", "::ffff:127.0.0.1"]);
const CLIENTE = /^[a-z0-9][a-z0-9_-]{0,63}$/;
const SIN_CACHE = { "Cache-Control": "no-store" };

export type ConfigAsesorDemo = { token: string; api: string };
type Entorno = Record<string, string | undefined>;

function hostname(valor: string | null | undefined): string | null {
  if (!valor) return null;
  try {
    return new URL(`http://${valor}`).hostname.toLowerCase();
  } catch {
    return null;
  }
}

/** null si el modo está apagado o mal configurado: entonces las rutas se comportan como en la PR #21. */
export function configAsesorDemo(env: Entorno = process.env): ConfigAsesorDemo | null {
  if (env.DEMO_ADVISOR_MODE !== "1") return null;
  const token = (env.DEMO_ADVISOR_TOKEN ?? "").trim();
  if (new TextEncoder().encode(token).length < 32) return null;
  if (env.ADMIN_TOKEN && env.ADMIN_TOKEN.trim() === token) return null;
  const api = (env.API_URL_SERVIDOR ?? env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
  try {
    const url = new URL(api);
    // El token solo viaja a un backend en esta misma máquina.
    if (!["http:", "https:"].includes(url.protocol) || !HOSTS_LOCALES.has(url.hostname)) return null;
  } catch {
    return null;
  }
  return { token, api };
}

/**
 * La petición llega a este servidor Next desde esta máquina, sin proxy delante y, si escribe, desde una
 * página del mismo origen. Next añade sus propias cabeceras X-Forwarded-*: se aceptan solo con valores locales.
 */
export function esPeticionLocal(req: Request): boolean {
  const h = req.headers;
  if (h.has("forwarded") || h.has("x-real-ip")) return false;
  const host = h.get("host");
  if (!HOSTS_LOCALES.has(hostname(host) ?? "")) return false;
  const reenviadoHost = h.get("x-forwarded-host");
  if (reenviadoHost !== null && !HOSTS_LOCALES.has(hostname(reenviadoHost.split(",")[0].trim()) ?? "")) return false;
  const reenviadoPor = h.get("x-forwarded-for");
  if (reenviadoPor !== null && !reenviadoPor.split(",").every((ip) => IPS_LOCALES.has(ip.trim()))) return false;
  if (req.method !== "GET" && req.method !== "HEAD") {
    const origen = h.get("origin");
    if (!origen) return false;
    try {
      if (new URL(origen).host !== host) return false;
    } catch {
      return false;
    }
    const sitio = h.get("sec-fetch-site");
    if (sitio !== null && sitio !== "same-origin") return false;
  }
  return true;
}

export function clienteValido(cid: string): boolean {
  return CLIENTE.test(cid);
}

export function respuestaJson(cuerpo: unknown, status = 200): Response {
  return Response.json(cuerpo, { status, headers: SIN_CACHE });
}

/** Llama al backend con el token del servidor. No reenvía cabeceras ni cuerpo del navegador. */
export async function llamarBackend(conf: ConfigAsesorDemo, ruta: string, method: "GET" | "POST" = "GET"): Promise<Response> {
  try {
    const r = await fetch(`${conf.api}/api/demo/asesor${ruta}`, {
      method,
      headers: { [CABECERA_ASESOR]: conf.token },
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    return new Response(await r.text(), {
      status: r.status,
      headers: { "Content-Type": r.headers.get("Content-Type") ?? "application/json", ...SIN_CACHE },
    });
  } catch {
    return respuestaJson({ detail: "No se pudo contactar con el backend local." }, 502);
  }
}

/** Estado que puede ver el navegador: nunca incluye el token. */
export async function estadoAsesorDemo(req: Request, env: Entorno = process.env): Promise<{ enabled: boolean; clients: string[]; advisor_id?: string }> {
  const conf = configAsesorDemo(env);
  if (!conf || !esPeticionLocal(req)) return { enabled: false, clients: [] };
  const r = await llamarBackend(conf, "/estado");
  if (!r.ok) return { enabled: false, clients: [] };
  const datos = await r.json();
  const clients = Array.isArray(datos.clients) ? datos.clients.filter((c: unknown) => typeof c === "string" && clienteValido(c)) : [];
  return { enabled: datos.enabled === true, clients, ...(typeof datos.advisor_id === "string" ? { advisor_id: datos.advisor_id } : {}) };
}
