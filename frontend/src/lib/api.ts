import { CLIENTE_DEMO, registrarSesion, tokenCliente, tokenSesion } from "./credenciales";
import type { AltaSesion, BootstrapVoz, Comparacion, ContextoVoz, ExpedienteAsesor, MemoriaPersonal, ModoAsesor, MotivoRevision, Perfil, Restricciones, Revision, Sesion, Turno, VersionResumen } from "./tipos";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ErrorAPI extends Error {
  constructor(public readonly status: number) {
    super(status === 401 || status === 403
      ? `${status} Necesitas la credencial de esta pestaña para acceder a este cliente.`
      : status === 412
        ? "412 La memoria ha cambiado. Vuelve a cargarla y decide si quieres guardar de nuevo."
        : status === 429
          ? "429 Esta demo pública ha llegado a su límite de entrevistas por hoy. Puedes ver la demo guiada o volver mañana."
          : `${status} No se ha podido completar la petición.`);
    this.name = "ErrorAPI";
  }
}

function autorizacion(token: string | null): Record<string, string> {
  if (!token) throw new ErrorAPI(401);
  return { Authorization: `Bearer ${token}` };
}
const cliente = (cid: string) => autorizacion(tokenCliente(cid));
const sesion = (sid: string) => autorizacion(tokenSesion(sid));
const id = encodeURIComponent;

async function respuesta(ruta: string, init?: RequestInit): Promise<Response> {
  const r = await fetch(`${API_URL}${ruta}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  // No incluir cuerpos remotos, URLs firmadas ni credenciales en errores mostrados o registrados.
  if (!r.ok) throw new ErrorAPI(r.status);
  return r;
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  return (await respuesta(ruta, init)).json() as Promise<T>;
}

async function pedirAlFront<T>(ruta: string, cuerpo: unknown, headers: Record<string, string> = {}): Promise<T> {
  const r = await fetch(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(cuerpo),
    cache: "no-store",
  });
  if (!r.ok) throw new ErrorAPI(r.status);
  return r.json() as Promise<T>;
}

/** Rutas del propio servidor Next sin credenciales del navegador (modo asesor de demo). */
async function leerDelFront<T>(ruta: string): Promise<T> {
  const r = await fetch(ruta, { cache: "no-store" });
  if (!r.ok) throw new ErrorAPI(r.status);
  return r.json() as Promise<T>;
}

async function memoria(ruta: string, init: RequestInit): Promise<MemoriaPersonal> {
  const r = await respuesta(ruta, init);
  const etag = r.headers.get("ETag");
  if (!etag || !/^"personal-\d+"$/.test(etag)) throw new Error("La respuesta de memoria no contiene una revisión válida.");
  return { ...(await r.json()), etag } as MemoriaPersonal;
}

function revision(etag: string): Record<string, string> {
  if (!/^"personal-\d+"$/.test(etag)) throw new Error("Vuelve a cargar la memoria antes de modificarla.");
  return { "If-Match": etag };
}

export const api = {
  salud: () => pedir<{ status: string }>("/api/health"),

  crearSesion: async (client_id?: string, channel: "voice" | "text" = "voice"): Promise<Sesion> => {
    const s = await pedir<AltaSesion>("/api/sessions", {
      method: "POST",
      headers: client_id ? cliente(client_id) : {},
      body: JSON.stringify({ ...(client_id ? { client_id } : {}), channel }),
    });
    return registrarSesion(s);
  },

  chat: (session_id: string, text: string | null) =>
    pedir<{ client_turn: Turno | null; agent_turn: Turno; finished: boolean }>(`/api/sessions/${id(session_id)}/chat`, {
      method: "POST", headers: sesion(session_id), body: JSON.stringify({ text }),
    }),

  enviarTurno: (session_id: string, turno: Turno) =>
    pedir<{ turn_id: string }>(`/api/sessions/${id(session_id)}/turns`, {
      method: "POST", headers: sesion(session_id), body: JSON.stringify(turno),
    }),

  perfilDemo: () => pedir<Perfil>("/api/demo/profile"),
  restriccionesDemo: () => pedir<Restricciones>("/api/demo/constraints"),
  perfil: (client_id: string) => client_id === CLIENTE_DEMO && !tokenCliente(client_id)
    ? pedir<Perfil>("/api/demo/profile")
    : pedir<Perfil>(`/api/clients/${id(client_id)}/profile`, { headers: cliente(client_id) }),
  restricciones: (client_id: string) => client_id === CLIENTE_DEMO && !tokenCliente(client_id)
    ? pedir<Restricciones>("/api/demo/constraints")
    : pedir<Restricciones>(`/api/clients/${id(client_id)}/constraints`, { headers: cliente(client_id) }),
  versiones: async (client_id: string): Promise<VersionResumen[]> => {
    if (client_id === CLIENTE_DEMO && !tokenCliente(client_id)) {
      const p = await pedir<Perfil>("/api/demo/profile");
      return [{ version: p.version, created_at: p.created_at,
        reason: "DATOS SIMULADOS: ejemplo fijo sin historial persistido", author: "fixture", status: p.status }];
    }
    return pedir<VersionResumen[]>(`/api/clients/${id(client_id)}/versions`, { headers: cliente(client_id) });
  },

  /** «Ha cambiado algo»: catálogo de motivos, previsualizar, abrir y seguir la microentrevista. */
  motivosRevision: () => pedir<MotivoRevision[]>("/api/review-reasons"),
  revision: (client_id: string) => client_id === CLIENTE_DEMO && !tokenCliente(client_id)
    ? Promise.resolve<Revision>({ open: false })
    : pedir<Revision>(`/api/clients/${id(client_id)}/review`, { headers: cliente(client_id) }),
  previsualizarRevision: (client_id: string, reasons: string[]) =>
    pedir<Revision>(`/api/clients/${id(client_id)}/review/preview`, {
      method: "POST", headers: cliente(client_id), body: JSON.stringify({ reasons }),
    }),
  abrirRevision: (client_id: string, reasons: string[]) =>
    pedir<Revision>(`/api/clients/${id(client_id)}/review`, {
      method: "POST", headers: cliente(client_id), body: JSON.stringify({ reasons }),
    }),
  cambios: (client_id: string) => client_id === CLIENTE_DEMO && !tokenCliente(client_id)
    ? Promise.resolve<Comparacion | null>(null)
    : pedir<Comparacion | null>(`/api/clients/${id(client_id)}/changes`, { headers: cliente(client_id) }),

  /** El servidor añade el token de entidad; la posesión del cliente viaja solo en cabecera. */
  validar: (client_id: string, advisor_id: string) =>
    pedirAlFront<Perfil>(`/api/entidad/${id(client_id)}/validar`, { advisor_id, changes: [] }, cliente(client_id)),
  reiniciarDemo: () => pedirAlFront<Perfil>("/api/entidad/reset", {}),

  /** Modo asesor de demo: el servidor Next pone su autorización; el navegador no envía ninguna credencial. */
  modoAsesor: () => leerDelFront<ModoAsesor>("/api/entidad/asesor"),
  expedienteAsesor: (client_id: string) => leerDelFront<ExpedienteAsesor>(`/api/entidad/${id(client_id)}/asesor`),
  validarComoAsesor: (client_id: string) => pedirAlFront<Perfil>(`/api/entidad/${id(client_id)}/validar`, {}),
  reiniciarComoAsesor: () => pedirAlFront<Perfil>("/api/entidad/reset", {}),
  /** Entrevista corta del pitch (modo asesor): sesión nueva sobre el cliente ficticio casi completo. */
  entrevistaCorta: async (channel: "voice" | "text"): Promise<Sesion> =>
    registrarSesion(await pedirAlFront<AltaSesion>(`/api/entidad/corta?channel=${channel}`, {})),

  pendientes: (session_id: string) =>
    pedir<{ pending: string[]; text: string }>(`/api/sessions/${id(session_id)}/pending`, { headers: sesion(session_id) }),
  bootstrapVoz: (session_id: string) =>
    pedir<BootstrapVoz>("/api/voice/bootstrap", {
      method: "POST", headers: sesion(session_id), body: JSON.stringify({ session_id }),
    }),
  contextoVoz: (session_id: string) =>
    pedir<ContextoVoz>(`/api/voice/context/${id(session_id)}`, { headers: sesion(session_id) }),

  memoria: (session_id: string) =>
    memoria(`/api/sessions/${id(session_id)}/memory`, { headers: sesion(session_id) }),
  guardarMemoria: (session_id: string, etag: string, consent_given: boolean, updates: Record<string, unknown>, forget: string[] = []) =>
    memoria(`/api/sessions/${id(session_id)}/memory`, {
      method: "PUT",
      headers: { ...sesion(session_id), ...revision(etag) },
      body: JSON.stringify({ consent_given, updates, forget }),
    }),
  borrarMemoria: (session_id: string, etag: string) =>
    memoria(`/api/sessions/${id(session_id)}/memory`, {
      method: "DELETE", headers: { ...sesion(session_id), ...revision(etag) },
    }),
};
