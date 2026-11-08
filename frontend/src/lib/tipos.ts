// Espejo en TypeScript de backend/app/perfil/modelos.py (contrato v0, docs/CONTRATOS.md).

export type Fuente = "declared" | "demonstrated" | "calculated" | "advisor";
export type EstadoPerfil = "draft" | "validated" | "active" | "review_pending";

export interface Evidencia {
  session_id: string;
  t_start: number;
  t_end: number;
  quote: string;
}

export interface Campo {
  value: unknown;
  source: Fuente;
  declared?: unknown;
  confidence?: number | null;
  evidence: Evidencia[];
  inputs: string[];
  flags: string[];
  updated_at: string;
  updated_by: string;
}

export interface Alerta {
  id: string;
  type: string;
  field?: string | null;
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
  mifid: Record<string, Campo>;
  personal: Record<string, unknown>;
  alerts: Alerta[];
  review: { validated_by?: string | null; validated_at?: string | null; next_review?: string | null };
}

export interface Restricciones {
  client_id: string;
  profile_version: number;
  eligible: boolean;
  missing_fields: string[];
  max_risk_indicator: number | null;
  horizon_years: number | null;
  loss_capacity_eur: number | null;
  liquidity_need: "high" | "medium" | "low" | null;
  esg_required: boolean;
  exclusions: string[];
  rationale: string[];
}

export interface Turno {
  speaker: "agent" | "client";
  text: string;
  t_start: number;
  t_end: number;
}

export interface Sesion {
  session_id: string;
  client_id: string;
  started_at: string;
}

export interface VersionResumen {
  version: number;
  created_at: string;
  reason: string;
  status: EstadoPerfil;
}
