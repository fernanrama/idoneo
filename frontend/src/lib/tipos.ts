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

/** Datos cambiados en una versión posterior aún sin validar (se sigue sirviendo el último validado). */
export interface RevisionPendiente {
  since_version: number;
  latest_version: number;
  latest_status: EstadoPerfil;
  paths: string[];
  opened_at: string;
  /** Efectos de `alcance.es_material` (perfil de riesgo, conveniencia, filtros…); vacío si no cambian las restricciones. */
  material: string[];
}

export interface MotivoRevision {
  code: string;
  titulo: string;
  detalle: string;
  icono: string;
}

export type TipoPregunta = "confirmar" | "repreguntar" | "comprobar";

export interface PreguntaRevision {
  path: string;
  tipo: TipoPregunta;
  valor_vigente: unknown;
  respondida: boolean;
}

/** Microentrevista «Ha cambiado algo»: motivos, preguntas y cuáles ya se han contestado. */
export type Revision =
  | { open: false }
  | {
      open: true;
      reasons: MotivoRevision[];
      opened_at: string;
      since_version: number;
      questions: PreguntaRevision[];
      remaining: number;
      deferred: string[];
      full_reassessment: boolean;
      full_reassessment_reasons: string[];
      /** Se puede finalizar: no quedan preguntas del alcance ni datos obligatorios (las aplazadas no bloquean). */
      can_finish: boolean;
      /** Lo que impide finalizar (rutas de datos). */
      blocking: string[];
    };

/** Respuesta de `POST /review/close`. Finalizar NO valida: si cambió algo, el perfil espera a la entidad. */
export interface CierreRevision {
  closed: true;
  already_closed: boolean;
  result?: "sin_cambios" | "pendiente_de_validacion";
  status: EstadoPerfil;
  pending_validation: boolean;
  version: number;
  full_reassessment?: boolean;
}

/** Último perfil validado frente al último guardado. */
export interface Comparacion {
  desde_version: number;
  hasta_version: number;
  cambios: { path: string; antes: unknown; ahora: unknown; fuente: string | null; cita: string | null }[];
  efectos: string[];
  perfil_antes: string | null;
  perfil_ahora: string | null;
  sri_antes: number | null;
  sri_ahora: number | null;
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
  blocked_searches?: string[];
  pending_review?: RevisionPendiente | null;
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

/** Fila de la bandeja de la entidad: la última versión de cada cliente, sin datos del perfil. */
export interface ClienteBandeja {
  client_id: string;
  version: number;
  status: EstadoPerfil;
  updated_at: string;
  reason: string;
}

/** Modo asesor de demostración (DATOS SIMULADOS). Lo decide el servidor; el navegador no tiene credencial. */
export interface ModoAsesor {
  enabled: boolean;
  clients: string[];
  advisor_id?: string;
  /** Sesión de administración (web publicada): todos los clientes. */
  all?: boolean;
  admin?: boolean;
}

export interface ExpedienteAsesor {
  profile: Perfil;
  constraints: Restricciones;
  versions: VersionResumen[];
  review?: Revision;
  changes?: Comparacion | null;
}
