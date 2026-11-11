// Espejo en TypeScript de backend/app/perfil/modelos.py (contrato v1, docs/diseno/03-contrato-perfil.md).

export type Fuente = "declared" | "demonstrated" | "calculated" | "advisor";
export type EstadoPerfil = "draft" | "pending_validation" | "active" | "review_due";
export type Flag = "declared_vs_demonstrated" | "inconsistent" | "low_confidence" | "needs_advisor";
export type Conveniencia = "appropriate" | "not_appropriate" | "not_assessed";

export interface Evidencia {
  session_id: string;
  turn_id?: string | null;
  t: [number, number];
  quote: string;
  audio_url?: string | null;
}

export interface Fact {
  value: unknown;
  source: Fuente;
  declared?: unknown;
  confidence?: number | null;
  confidence_basis?: string | null;
  evidence: Evidencia[];
  inputs: string[];
  flags: Flag[];
  updated_at: string;
  updated_by: string;
}

export interface Alerta {
  id: string;
  path?: string | null;
  flag: Flag;
  message: string;
  evidence: Evidencia[];
  status: "open" | "resolved";
  created_at: string;
}

export interface Perfil {
  client_id: string;
  version: number;
  status: EstadoPerfil;
  created_at: string;
  reason: string;
  author: string;
  mifid: Record<string, Fact>;
  assessments: {
    suitability: {
      complete: boolean;
      missing: string[];
      risk_profile: string | null;
      max_sri: number | null;
      rationale_ids: string[];
      rationale: string[];
    };
    appropriateness: Record<string, Conveniencia>;
  };
  personal: Record<string, unknown>;
  alerts: Alerta[];
  review: { validated_by?: string | null; validated_at?: string | null; next_review?: string | null; open_flags: number };
}

export interface Restricciones {
  client_id: string;
  profile_version: number;
  status: EstadoPerfil;
  usable: boolean;
  funds_query: Record<string, unknown>;
  portfolios_query: Record<string, unknown>;
  post_filters: { field: string; op: string; value: unknown; why: string }[];
  appropriateness: Record<string, Conveniencia>;
  evidence_refs: string[];
  rationale: string[];
}

export interface Turno {
  turn_id?: string;
  speaker: "agent" | "client";
  text: string;
  t_start: number;
  t_end: number;
}

export interface Sesion {
  session_id: string;
  client_id: string;
  started_at: string;
  channel?: "voice" | "text";
}

/** Solo llega en el alta; se extrae antes de persistir metadatos. */
export interface AltaSesion extends Sesion {
  access_token?: string;
}

export type VariableDinamica = string | number | boolean;

export interface ContextoVoz {
  user_id: string;
  dynamic_variables: Record<string, VariableDinamica>;
  server_location?: string | null;
}

export interface BootstrapVoz extends ContextoVoz {
  signed_url: string;
}

export interface MemoriaPersonal {
  enabled: boolean;
  version: number;
  etag: string;
  data: Record<string, unknown>;
  consent_at?: string | null;
  deleted_versions?: number;
}

export interface VersionResumen {
  version: number;
  created_at: string;
  reason: string;
  author: string;
  status: EstadoPerfil;
}

/** Modo asesor de demostración (DATOS SIMULADOS). Lo decide el servidor; el navegador no tiene credencial. */
export interface ModoAsesor {
  enabled: boolean;
  clients: string[];
  advisor_id?: string;
}

export interface ExpedienteAsesor {
  profile: Perfil;
  constraints: Restricciones;
  versions: VersionResumen[];
}
