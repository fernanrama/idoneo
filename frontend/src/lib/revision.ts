import { ETIQUETAS, mostrarValor } from "./bloques";
import type { Perfil, Restricciones, TipoPregunta } from "./tipos";

/** Búsquedas que el agente de la entidad puede hacer en el catálogo, en palabras del cliente. */
export const BUSQUEDAS: { code: string; nombre: string; detalle: string }[] = [
  { code: "funds", nombre: "Fondos de inversión", detalle: "Renta fija, mixtos, renta variable o monetarios" },
  { code: "portfolios", nombre: "Carteras automatizadas", detalle: "Gestionadas por la entidad según tu perfil" },
  { code: "etfs", nombre: "ETF", detalle: "Fondos que cotizan en bolsa" },
  { code: "stocks", nombre: "Acciones sueltas", detalle: "De una sola empresa" },
];

/** Por qué no se busca algo, explicado al cliente (sale del `rationale` que calcula el backend). */
/** La línea del cálculo (backend) que explica por qué no se busca algo; para la entidad. */
export function motivoBloqueo(code: string, r: Restricciones): string | undefined {
  return r.rationale.find((m) =>
    code === "funds" ? m.includes("fondos") : code === "etfs" ? m.startsWith("ETF") : code === "stocks" ? m.includes("cciones") : m.includes("perfil de riesgo"));
}

export function porQueNo(code: string, r: Restricciones, perfil: Perfil): string {
  const sri = perfil.assessments.suitability.max_sri;
  const motivo = motivoBloqueo(code, r);
  if (!perfil.assessments.suitability.risk_profile) return "Aún nos faltan datos para saber qué riesgo encaja contigo.";
  if (code === "stocks" && motivo?.includes("SRI máximo")) {
    return `Una acción suelta suele tener un riesgo de 6 o 7 sobre 7, y tu perfil llega hasta ${sri}.`;
  }
  if (code === "funds") return "En la conversación no quedó claro que conozcas cómo funcionan estos fondos.";
  return "No has comprobado todavía que conoces cómo funcionan. Si quieres, lo vemos en una revisión.";
}

export const TIPO_PREGUNTA: Record<TipoPregunta, { nombre: string; ayuda: string }> = {
  confirmar: { nombre: "Confirmar", ayuda: "Te leemos lo que tenemos y nos dices si sigue igual" },
  repreguntar: { nombre: "Pregunta nueva", ayuda: "Ha podido cambiar: te lo preguntamos otra vez" },
  comprobar: { nombre: "Comprobar", ayuda: "Una pregunta sencilla para ver cómo funciona" },
};

/** Nombre del dato para el cliente («Tus ingresos al mes»), sin rutas internas. */
export function nombreDato(ruta: string): string {
  return CLIENTE[ruta] ?? ETIQUETAS[ruta] ?? ruta;
}

const CLIENTE: Record<string, string> = {
  "financial.net_monthly_income_eur": "Lo que cobras al mes",
  "financial.income_stability": "Si tus ingresos son estables",
  "financial.fixed_monthly_costs_eur": "Tus gastos fijos al mes",
  "financial.liquid_savings_eur": "Tu ahorro disponible",
  "financial.other_assets_eur": "Otros bienes",
  "financial.debts_eur": "Préstamos y deudas (sin la hipoteca)",
  "financial.mortgage_eur": "Lo que te queda de hipoteca",
  "objectives.o1.goal": "Para qué inviertes",
  "objectives.o1.amount_eur": "Cuánto quieres invertir",
  "objectives.o1.horizon_years": "Durante cuánto tiempo",
  "objectives.o1.liquidity_need": "Si podrías necesitar el dinero antes",
  "risk_tolerance.scenario_score": "Qué harías si tus ahorros bajan",
  "risk_tolerance.max_drawdown_accepted_pct": "Cuánto podrías ver bajar",
  "risk_tolerance.past_behaviour": "Qué hiciste en una caída real",
};

const EUROS = /_eur$/;
/** Valor que consta, legible: «1.400 €», «estables», «10 años». */
export function valorLegible(ruta: string, v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number" && EUROS.test(ruta)) return `${v.toLocaleString("es-ES", { maximumFractionDigits: 0, useGrouping: "always" })} €`;
  if (ruta === "objectives.o1.horizon_years" && typeof v === "number") return `${v.toLocaleString("es-ES")} ${v === 1 ? "año" : "años"}`;
  return mostrarValor(v);
}

/** Minutos aproximados de una microentrevista: unos 25-30 s por pregunta, mínimo uno. */
export function minutos(preguntas: number): number {
  return Math.max(1, Math.round((preguntas * 28) / 60));
}
