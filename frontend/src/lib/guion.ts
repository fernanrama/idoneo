import type { Turno } from "./tipos";

/**
 * GUION DE DEMO — DATOS SIMULADOS.
 * Entrevista corta de Carmen (68 años) para el modo "guion": se envía turno a turno al backend real,
 * así que el perfil lo construye el sistema, no esta lista. Sustituir por backend/eval/carmen.json
 * (Pablo) cuando exista. Tiempos en segundos desde el inicio de la sesión.
 */
export const GUION_CARMEN: Turno[] = [
  { speaker: "agent", t_start: 0, t_end: 7, text: "Hola, Carmen. Soy el asistente de perfil inversor. Soy una inteligencia artificial y una persona del banco revisará todo. ¿Le parece bien que grabemos la conversación?" },
  { speaker: "client", t_start: 8, t_end: 10.5, text: "Sí, de acuerdo, puede grabar." },
  { speaker: "agent", t_start: 11, t_end: 15, text: "Gracias. ¿Para qué le gustaría invertir su dinero?" },
  { speaker: "client", t_start: 16, t_end: 20, text: "Quiero tener un dinerito extra cada mes para complementar la pensión." },
  { speaker: "agent", t_start: 21, t_end: 24, text: "¿Durante cuánto tiempo, más o menos?" },
  { speaker: "client", t_start: 25, t_end: 28, text: "Para los próximos diez años, más o menos." },
  { speaker: "agent", t_start: 29, t_end: 33, text: "¿Cuánto cobra al mes y cuánto gasta en cosas fijas como luz, comunidad o la compra?" },
  { speaker: "client", t_start: 34, t_end: 41, text: "Cobro unos mil cuatrocientos cincuenta de pensión. Entre luz, comunidad y la compra, unos novecientos." },
  { speaker: "agent", t_start: 42, t_end: 45, text: "¿Y cuánto tiene ahorrado? ¿Tiene alguna deuda?" },
  { speaker: "client", t_start: 46, t_end: 51, text: "Tengo ochenta mil en depósitos. No debo nada, la casa está pagada." },
  { speaker: "agent", t_start: 52, t_end: 55, text: "¿Qué productos conoce? Por ejemplo, depósitos o fondos de renta fija." },
  { speaker: "client", t_start: 55, t_end: 60, text: "Los depósitos los conozco, me dan un poquito al año. Si suben los tipos, el bono vale menos, eso me lo explicó mi hijo." },
  { speaker: "agent", t_start: 60, t_end: 64, text: "En el test de su banco marcó que conoce bien los fondos de renta variable. ¿Podría perder dinero un fondo así?" },
  { speaker: "client", t_start: 57, t_end: 61, text: "Eso no puede pasar, el fondo es del banco." },
  { speaker: "agent", t_start: 62, t_end: 70, text: "Es una duda muy común. Un fondo de renta variable sí puede bajar, aunque lo venda su banco. Imagine que sus ahorros bajan un veinte por ciento en unos meses. ¿Qué haría?" },
  { speaker: "client", t_start: 71, t_end: 74, text: "Si baja un veinte por ciento, lo saco todo." },
  { speaker: "agent", t_start: 75, t_end: 81, text: "Entendido. Última pregunta: ¿le importa que sus inversiones sigan criterios de sostenibilidad, por ejemplo evitar empresas que contaminan mucho?" },
  { speaker: "client", t_start: 82, t_end: 85, text: "Eso me da igual, mientras no pierda." },
  { speaker: "agent", t_start: 86, t_end: 92, text: "Muchas gracias, Carmen. Ya tenemos su perfil. Una persona del banco lo revisará y le avisaremos." },
];
