/**
 * Acciones de la entidad (validar el perfil, reiniciar la demo) hechas desde el servidor de Next.
 *
 * El backend exige la cabecera X-Admin-Token cuando tiene ADMIN_TOKEN (obligatorio con URL pública).
 * El token no puede ir al navegador: lo añade aquí el servidor, leyéndolo de frontend/.env.local
 * (ADMIN_TOKEN, sin el prefijo NEXT_PUBLIC_, así que nunca entra en el JavaScript del cliente).
 *
 * Además solo se aceptan peticiones hechas a localhost: si el front se expone por un túnel (p. ej. para
 * probar el micrófono en el móvil), nadie de fuera puede validar perfiles a través de estas rutas.
 */

const BACKEND = process.env.API_URL_SERVIDOR ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const LOCALES = new Set(["localhost", "127.0.0.1", "[::1]"]);

export function esPeticionLocal(req: Request): boolean {
  const host = (req.headers.get("x-forwarded-host") ?? req.headers.get("host") ?? "").split(",")[0].trim();
  const nombre = host.startsWith("[") ? host.slice(0, host.indexOf("]") + 1) : host.split(":")[0];
  return LOCALES.has(nombre);
}

export async function reenviar(req: Request, ruta: string, cuerpo: unknown): Promise<Response> {
  if (!esPeticionLocal(req)) {
    return Response.json(
      { detail: "Las acciones de la entidad solo se pueden hacer desde el ordenador donde corre la demo." },
      { status: 403 },
    );
  }
  const cabeceras: Record<string, string> = { "Content-Type": "application/json" };
  const token = process.env.ADMIN_TOKEN;
  if (token) cabeceras["X-Admin-Token"] = token;
  try {
    const r = await fetch(`${BACKEND}${ruta}`, {
      method: "POST",
      headers: cabeceras,
      body: JSON.stringify(cuerpo),
      cache: "no-store",
    });
    return new Response(await r.text(), {
      status: r.status,
      headers: { "Content-Type": r.headers.get("Content-Type") ?? "application/json" },
    });
  } catch {
    return Response.json({ detail: `No se puede conectar con el backend en ${BACKEND}` }, { status: 502 });
  }
}
