import type { Perfil } from "./tipos";

// Bloques de la entrevista, en orden. Un bloque está completo cuando todos sus campos tienen valor.
// Rutas del contrato v1 (docs/diseno/03-contrato-perfil.md).
export const BLOQUES = [
  { id: "avisos", nombre: "Avisos", campos: ["disclosures.ai_notice_ack", "disclosures.purpose_ack"] },
  { id: "objetivo", nombre: "Tu objetivo", campos: ["objectives.o1.goal", "objectives.o1.horizon_years"] },
  {
    id: "situacion",
    nombre: "Tu situación",
    campos: [
      "financial.net_monthly_income_eur",
      "financial.fixed_monthly_costs_eur",
      "financial.liquid_savings_eur",
      "financial.debts_eur",
    ],
  },
  { id: "conocimientos", nombre: "Lo que conoces", campos: ["knowledge.fixed_income_funds", "knowledge.equity_funds"] },
  { id: "riesgo", nombre: "Ante una caída", campos: ["risk_tolerance.scenario_score"] },
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

export const FAMILIAS: Record<string, string> = {
  deposits_money_market: "depósitos y monetarios",
  fixed_income_funds: "fondos de renta fija",
  mixed_funds: "fondos mixtos",
  equity_funds: "fondos de renta variable",
  etfs: "ETF",
  stocks: "acciones",
  complex_products: "productos complejos",
};

// Etiquetas legibles para el panel de la entidad.
export const ETIQUETAS: Record<string, string> = {
  "disclosures.ai_notice_ack": "Informado de que habla con una IA",
  "disclosures.purpose_ack": "Entiende para qué es la evaluación",
  ...Object.fromEntries(Object.entries(FAMILIAS).map(([k, v]) => [`knowledge.${k}`, `Conocimiento: ${v}`])),
  ...Object.fromEntries(Object.entries(FAMILIAS).map(([k, v]) => [`experience.${k}.operations_last_3y`, `Operaciones en 3 años: ${v}`])),
  "experience.education": "Formación",
  "experience.profession": "Profesión",
  "financial.net_monthly_income_eur": "Ingresos netos mensuales (€)",
  "financial.income_stability": "Estabilidad de ingresos",
  "financial.fixed_monthly_costs_eur": "Gastos fijos mensuales (€)",
  "financial.liquid_savings_eur": "Ahorro líquido (€)",
  "financial.other_assets_eur": "Otro patrimonio (€)",
  "financial.debts_eur": "Deudas (€)",
  "financial.emergency_fund_months": "Meses de gastos cubiertos",
  "financial.loss_capacity_eur": "Capacidad de soportar pérdidas (€)",
  "objectives.o1.goal": "Objetivo",
  "objectives.o1.amount_eur": "Importe objetivo (€)",
  "objectives.o1.horizon_years": "Plazo (años)",
  "objectives.o1.liquidity_need": "Necesidad de liquidez",
  "risk_tolerance.scenario_score": "Tolerancia por escenarios (1–5)",
  "risk_tolerance.max_drawdown_accepted_pct": "Caída máxima aceptada (%)",
  "risk_tolerance.past_behaviour": "Comportamiento ante caídas",
  "sustainability.preference": "Preferencia de sostenibilidad",
  "sustainability.min_sfdr_article": "Artículo SFDR mínimo",
  "sustainability.explained": "Se le explicó la sostenibilidad",
};

export const VALORES: Record<string, string> = {
  none: "ninguno",
  basic: "básico",
  medium: "medio",
  high: "alto",
  low: "baja",
  some: "alguna",
  strong: "fuerte",
  stable: "estables",
  variable: "variables",
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

export const ESTADOS: Record<string, string> = {
  draft: "Borrador",
  pending_validation: "Pendiente de validar",
  active: "Activo · apto para recomendar",
  review_due: "Revisión pendiente",
};
