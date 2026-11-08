import type { Perfil } from "./tipos";

// Bloques de la entrevista, en orden. Un bloque está completo cuando todos sus campos tienen valor.
export const BLOQUES = [
  { id: "consentimiento", nombre: "Permisos", campos: ["consent.recording", "consent.ai_notice"] },
  { id: "objetivo", nombre: "Tu objetivo", campos: ["objective.goal", "objective.horizon_years"] },
  {
    id: "situacion",
    nombre: "Tu situación",
    campos: [
      "financial.monthly_income_eur",
      "financial.monthly_fixed_costs_eur",
      "financial.liquid_savings_eur",
      "financial.debts_eur",
    ],
  },
  { id: "conocimientos", nombre: "Lo que conoces", campos: ["knowledge.investment_funds", "knowledge.equity_risk"] },
  { id: "riesgo", nombre: "Ante una caída", campos: ["risk.tolerance"] },
  { id: "sostenibilidad", nombre: "Sostenibilidad", campos: ["sustainability.preference"] },
] as const;

export type EstadoBloque = "pendiente" | "en_curso" | "completo";

export function estadoBloques(perfil: Perfil | null): { id: string; nombre: string; estado: EstadoBloque }[] {
  const tiene = (c: string) => perfil?.mifid[c]?.value !== undefined && perfil?.mifid[c]?.value !== null;
  let enCursoAsignado = false;
  return BLOQUES.map((b) => {
    const hechos = b.campos.filter(tiene).length;
    let estado: EstadoBloque = "pendiente";
    if (hechos === b.campos.length) estado = "completo";
    else if (!enCursoAsignado) {
      estado = "en_curso";
      enCursoAsignado = true;
    }
    return { id: b.id, nombre: b.nombre, estado };
  });
}

// Etiquetas legibles para el panel de la entidad.
export const ETIQUETAS: Record<string, string> = {
  "consent.recording": "Consiente la grabación",
  "consent.ai_notice": "Informado de que habla con una IA",
  "knowledge.investment_funds": "Conocimiento: fondos de inversión",
  "knowledge.equity_risk": "Conocimiento: riesgo de renta variable",
  "experience.past_investments": "Experiencia previa",
  "financial.monthly_income_eur": "Ingresos mensuales (€)",
  "financial.monthly_fixed_costs_eur": "Gastos fijos mensuales (€)",
  "financial.liquid_savings_eur": "Ahorro líquido (€)",
  "financial.debts_eur": "Deudas (€)",
  "financial.emergency_fund_eur": "Colchón de emergencia (€)",
  "financial.loss_capacity_eur": "Capacidad de soportar pérdidas (€)",
  "objective.goal": "Objetivo",
  "objective.amount_eur": "Importe objetivo (€)",
  "objective.horizon_years": "Plazo (años)",
  "risk.reaction_to_drop": "Reacción ante una caída",
  "risk.tolerance": "Tolerancia al riesgo",
  "sustainability.preference": "Preferencia de sostenibilidad",
  "sustainability.explained": "Se le explicó la sostenibilidad",
  "exclusions.sectors": "Sectores excluidos",
};

export const VALORES: Record<string, string> = {
  none: "ninguno",
  basic: "básico",
  medium: "medio",
  high: "alto",
  low: "baja",
  some: "alguna",
  strong: "fuerte",
  true: "sí",
  false: "no",
};

export function mostrarValor(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-ES");
  if (Array.isArray(v)) return v.join(", ") || "—";
  const s = String(v);
  return VALORES[s] ?? s;
}

export const FUENTES: Record<string, string> = {
  declared: "Declarado",
  demonstrated: "Demostrado",
  calculated: "Calculado",
  advisor: "Asesor",
};
