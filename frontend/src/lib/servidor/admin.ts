/**
 * Administración de la entidad en la web publicada: solo servidor (rutas de /api/admin y /api/entidad).
 *
 * - Se activa con ADMIN_LOGIN_CLAVE (clave compartida del equipo, >= 12 caracteres) y ADMIN_TOKEN (el mismo
 *   que en el backend). Sin ellas, todo sigue como antes: no hay login y la validación está bloqueada.
 * - Login: la clave se compara en tiempo constante y se emite una cookie HttpOnly, SameSite=Strict, firmada
 *   con HMAC y con caducidad (8 h). Cambiar la clave o el token invalida las cookies emitidas.
 * - ADMIN_TOKEN nunca sale de este servidor: el navegador solo tiene la cookie.
 * - Las escrituras exigen además que la petición venga de una página del mismo origen.
 */
import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export const COOKIE_ADMIN = "idoneo_admin";
export const DURACION_SESION_S = 8 * 60 * 60;
const MIN_CLAVE = 12;
const SIN_CACHE = { "Cache-Control": "no-store" };

export type ConfigAdmin = { clave: string; token: string; api: string };
type Entorno = Record<string, string | undefined>;

/** null si la administración no está configurada en este despliegue. */
export function configAdmin(env: Entorno = process.env): ConfigAdmin | null {
  const clave = (env.ADMIN_LOGIN_CLAVE ?? "").trim();
  const token = (env.ADMIN_TOKEN ?? "").trim();
  if (clave.length < MIN_CLAVE || token.length < 16 || clave === token) return null;
  const api = (env.API_URL_SERVIDOR ?? env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");
  try {
    if (!["http:", "https:"].includes(new URL(api).protocol)) return null;
  } catch {
    return null;
  }
  return { clave, token, api };
}

const resumen = (texto: string) => createHash("sha256").update(texto, "utf8").digest();

export function claveCorrecta(conf: ConfigAdmin, intento: unknown): boolean {
  if (typeof intento !== "string" || intento.length > 256) return false;
  return timingSafeEqual(resumen(intento), resumen(conf.clave));
}

function firma(conf: ConfigAdmin, caduca: number): string {
  const llave = resumen(`idoneo-admin|${conf.token}|${conf.clave}`);
  return createHmac("sha256", llave).update(`admin.${caduca}`).digest("base64url");
}

export function emitirSesion(conf: ConfigAdmin, ahoraMs = Date.now()): string {
  const caduca = Math.floor(ahoraMs / 1000) + DURACION_SESION_S;
  return `${caduca}.${firma(conf, caduca)}`;
}

export function sesionValida(conf: ConfigAdmin, valor: string | null | undefined, ahoraMs = Date.now()): boolean {
  const m = /^(\d{1,12})\.([A-Za-z0-9_-]{43})$/.exec(valor ?? "");
  if (!m) return false;
  const caduca = Number(m[1]);
  if (caduca <= Math.floor(ahoraMs / 1000)) return false;
  const esperada = Buffer.from(firma(conf, caduca));
  const recibida = Buffer.from(m[2]);
  return esperada.length === recibida.length && timingSafeEqual(esperada, recibida);
}

function leerCookie(req: Request, nombre: string): string | null {
  for (const parte of (req.headers.get("cookie") ?? "").split(";")) {
    const [k, ...v] = parte.trim().split("=");
    if (k === nombre) return v.join("=");
  }
  return null;
}

/** Configuración si la petición trae una sesión de administración válida; null si no. */
export function sesionAdmin(req: Request, env: Entorno = process.env): ConfigAdmin | null {
  const conf = configAdmin(env);
  return conf && sesionValida(conf, leerCookie(req, COOKIE_ADMIN)) ? conf : null;
}

/** Escrituras: Origin presente y con el mismo host que la petición (defensa adicional a SameSite=Strict). */
export function mismoOrigen(req: Request): boolean {
  const origen = req.headers.get("origin");
  const host = req.headers.get("x-forwarded-host")?.split(",")[0].trim() || req.headers.get("host");
  if (!origen || !host) return false;
  try {
    return new URL(origen).host.toLowerCase() === host.toLowerCase();
  } catch {
    return false;
  }
}

export function cookieSesion(valor: string, segura: boolean): string {
  return `${COOKIE_ADMIN}=${valor}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${DURACION_SESION_S}${segura ? "; Secure" : ""}`;
}

export function cookieBorrada(segura: boolean): string {
  return `${COOKIE_ADMIN}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0${segura ? "; Secure" : ""}`;
}

export const esHttps = (req: Request) =>
  (req.headers.get("x-forwarded-proto") ?? new URL(req.url).protocol.replace(":", "")) === "https";

/** Llama a /api/entidad del backend con ADMIN_TOKEN. Del navegador no se reenvía nada. */
export async function llamarEntidad(
  conf: ConfigAdmin, ruta: string, method: "GET" | "POST" = "GET", cuerpo?: Record<string, unknown>,
): Promise<Response> {
  try {
    const r = await fetch(`${conf.api}/api/entidad${ruta}`, {
      method,
      headers: cuerpo ? { "X-Admin-Token": conf.token, "Content-Type": "application/json" } : { "X-Admin-Token": conf.token },
      ...(cuerpo ? { body: JSON.stringify(cuerpo) } : {}),
      cache: "no-store",
      // Render gratuito puede tardar ~1 min en despertar.
      signal: AbortSignal.timeout(70000),
    });
    return new Response(await r.text(), {
      status: r.status,
      headers: { "Content-Type": r.headers.get("Content-Type") ?? "application/json", ...SIN_CACHE },
    });
  } catch {
    return Response.json({ detail: "No se pudo contactar con el backend." }, { status: 502, headers: SIN_CACHE });
  }
}
