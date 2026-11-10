import type { AltaSesion, Sesion } from "./tipos";

const CLAVE = "idoneo.acceso.v1";
export const CLAVE_SESION = "idoneo.sesion";
export const CLIENTE_DEMO = "carmen-68";

type Accesos = { clientes: Record<string, string>; sesiones: Record<string, string> };

function accesos(): Accesos {
  if (typeof window === "undefined") return { clientes: {}, sesiones: {} };
  try {
    const dato = JSON.parse(window.sessionStorage.getItem(CLAVE) ?? "{}");
    return { clientes: dato.clientes ?? {}, sesiones: dato.sesiones ?? {} };
  } catch {
    return { clientes: {}, sesiones: {} };
  }
}

export function tokenCliente(clientId: string): string | null {
  const valor = accesos().clientes[clientId];
  return typeof valor === "string" && valor ? valor : null;
}

export function tokenSesion(sessionId: string): string | null {
  const datos = accesos();
  const cliente = datos.sesiones[sessionId];
  const valor = cliente ? datos.clientes[cliente] : null;
  return typeof valor === "string" && valor ? valor : null;
}

/** Lista permitida: las credenciales nunca pasan a React ni a localStorage. */
export function metadatosSesion(sesion: Sesion): Sesion {
  return {
    session_id: sesion.session_id,
    client_id: sesion.client_id,
    started_at: sesion.started_at,
    ...(sesion.channel ? { channel: sesion.channel } : {}),
  };
}

export function registrarSesion(sesion: AltaSesion): Sesion {
  if (typeof window === "undefined") throw new Error("La sesión requiere un navegador.");
  const datos = accesos();
  if (sesion.access_token) datos.clientes[sesion.client_id] = sesion.access_token;
  if (!datos.clientes[sesion.client_id]) throw new Error("Falta la credencial de acceso a esta sesión.");
  datos.sesiones[sesion.session_id] = sesion.client_id;
  window.sessionStorage.setItem(CLAVE, JSON.stringify(datos));
  return metadatosSesion(sesion);
}

export function persistirSesion(sesion: AltaSesion | null): Sesion | null {
  if (!sesion) {
    window.localStorage.removeItem(CLAVE_SESION);
    return null;
  }
  const metadata = registrarSesion(sesion);
  window.localStorage.setItem(CLAVE_SESION, JSON.stringify(metadata));
  return metadata;
}

/** Una referencia antigua sin credencial no permite reanudar ni obtener otra credencial. */
export function restaurarSesion(): Sesion | null {
  try {
    const sesion = JSON.parse(window.localStorage.getItem(CLAVE_SESION) ?? "null");
    if (!sesion || typeof sesion.session_id !== "string" || typeof sesion.client_id !== "string" || !tokenCliente(sesion.client_id)) {
      window.localStorage.removeItem(CLAVE_SESION);
      return null;
    }
    // Ignorar y eliminar access_token si quedó en metadatos de una versión anterior.
    return persistirSesion(metadatosSesion(sesion));
  } catch {
    window.localStorage.removeItem(CLAVE_SESION);
    return null;
  }
}
