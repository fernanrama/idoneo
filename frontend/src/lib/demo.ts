import type { Fact, Perfil, Turno } from "./tipos";

/**
 * Demo guiada — DATOS SIMULADOS.
 * Reconstruye, turno a turno, el perfil de ejemplo `carmen-68` (calculado por el backend con sus reglas
 * fijas) a partir de lo que Carmen ha dicho hasta ese momento: un dato aparece cuando ya se ha oído la
 * frase que lo justifica. No llama al modelo ni gasta créditos; es una repetición de una entrevista simulada.
 */
const normal = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9 ]/g, "")
    .replace(/\s+/g, " ")
    .trim();

export function perfilParcial(fuente: Perfil, dichos: Turno[], terminado: boolean): Perfil {
  const oido = normal(dichos.filter((t) => t.speaker === "client").map((t) => t.text).join(" "));
  const justificado = (f: Fact) => f.evidence.some((e) => e.quote && oido.includes(normal(e.quote)));
  const visibles = new Set<string>();
  for (const [ruta, f] of Object.entries(fuente.mifid)) {
    if (f.value == null || f.source === "calculated") continue;
    if (terminado || justificado(f) || (!f.evidence.some((e) => e.quote) && ruta.startsWith("sustainability") && oido.includes("me da igual"))) visibles.add(ruta);
  }
  for (const [ruta, f] of Object.entries(fuente.mifid)) {
    if (f.value != null && f.source === "calculated" && f.inputs.every((i) => visibles.has(i) || fuente.mifid[i]?.value == null)) visibles.add(ruta);
  }
  const mifid: Perfil["mifid"] = {};
  for (const [ruta, f] of Object.entries(fuente.mifid)) mifid[ruta] = visibles.has(ruta) ? f : { ...f, value: null, evidence: [] };

  const pendientes = Object.keys(fuente.mifid).filter((r) => fuente.mifid[r].value != null && !visibles.has(r) && !r.startsWith("disclosures."));
  const completo = pendientes.length === 0;
  const su = fuente.assessments.suitability;
  return {
    ...fuente,
    status: completo ? fuente.status : "draft",
    mifid,
    alerts: fuente.alerts.filter((a) => a.evidence.some((e) => e.quote && oido.includes(normal(e.quote)))),
    assessments: {
      ...fuente.assessments,
      suitability: completo ? su : { ...su, complete: false, missing: pendientes, risk_profile: null, max_sri: null },
    },
  };
}

/** Voces del navegador en español (gratis, sin servidor). Una para el asistente y otra para Carmen. */
export function vocesEspanol(): { asistente: SpeechSynthesisVoice | null; cliente: SpeechSynthesisVoice | null } {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return { asistente: null, cliente: null };
  const todas = window.speechSynthesis.getVoices().filter((v) => v.lang.toLowerCase().startsWith("es"));
  const espana = todas.filter((v) => v.lang.toLowerCase() === "es-es");
  const lista = espana.length ? [...espana, ...todas.filter((v) => !espana.includes(v))] : todas;
  return { asistente: lista[0] ?? null, cliente: lista[1] ?? lista[0] ?? null };
}
