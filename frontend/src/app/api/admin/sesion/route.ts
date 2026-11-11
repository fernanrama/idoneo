import { connection } from "next/server";
import { claveCorrecta, configAdmin, cookieBorrada, cookieSesion, emitirSesion, esHttps, mismoOrigen, sesionAdmin } from "@/lib/servidor/admin";

const SIN_CACHE = { "Cache-Control": "no-store" };

/** ¿Hay administración en este despliegue y está iniciada la sesión? Sin secretos. */
export async function GET(req: Request) {
  await connection();
  return Response.json({ enabled: configAdmin() !== null, logged: sesionAdmin(req) !== null }, { headers: SIN_CACHE });
}

/** Iniciar sesión con la clave de administración del equipo. */
export async function POST(req: Request) {
  const conf = configAdmin();
  if (!conf) return Response.json({ detail: "La administración no está activada en este despliegue." }, { status: 404, headers: SIN_CACHE });
  if (!mismoOrigen(req)) return Response.json({ detail: "Origen no permitido." }, { status: 403, headers: SIN_CACHE });
  const cuerpo = await req.json().catch(() => null);
  if (!claveCorrecta(conf, (cuerpo as { clave?: unknown } | null)?.clave)) {
    // Pequeña espera para frenar intentos repetidos.
    await new Promise((r) => setTimeout(r, 800));
    return Response.json({ detail: "Clave incorrecta." }, { status: 401, headers: SIN_CACHE });
  }
  return Response.json({ logged: true }, { headers: { ...SIN_CACHE, "Set-Cookie": cookieSesion(emitirSesion(conf), esHttps(req)) } });
}

/** Cerrar sesión. */
export async function DELETE(req: Request) {
  if (!mismoOrigen(req)) return Response.json({ detail: "Origen no permitido." }, { status: 403, headers: SIN_CACHE });
  return Response.json({ logged: false }, { headers: { ...SIN_CACHE, "Set-Cookie": cookieBorrada(esHttps(req)) } });
}
