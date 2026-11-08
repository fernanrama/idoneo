import type { Perfil, Restricciones, Sesion, Turno, VersionResumen } from "./tipos";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${ruta}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!r.ok) {
    throw new Error(`${r.status} ${ruta}: ${await r.text()}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  salud: () => pedir<{ status: string }>("/api/health"),

  crearSesion: (client_id?: string) =>
    pedir<Sesion>("/api/sessions", { method: "POST", body: JSON.stringify({ client_id }) }),

  enviarTurno: (session_id: string, turno: Turno) =>
    pedir<{ turn_index: number }>(`/api/sessions/${session_id}/turns`, {
      method: "POST",
      body: JSON.stringify(turno),
    }),

  perfil: (client_id: string) => pedir<Perfil>(`/api/clients/${client_id}/profile`),

  versiones: (client_id: string) =>
    pedir<VersionResumen[]>(`/api/clients/${client_id}/profile/versions`),

  restricciones: (client_id: string) =>
    pedir<Restricciones>(`/api/clients/${client_id}/constraints`),

  validar: (client_id: string, advisor_id: string) =>
    pedir<Perfil>(`/api/clients/${client_id}/profile/validate`, {
      method: "POST",
      body: JSON.stringify({ advisor_id, corrections: [] }),
    }),

  reiniciarDemo: () => pedir<Perfil>("/api/demo/reset", { method: "POST" }),

  /** URL firmada para un agente privado de ElevenLabs; 503 si el backend no tiene clave. */
  urlFirmadaVoz: () => pedir<{ signed_url: string }>("/api/voice/signed-url"),
};
