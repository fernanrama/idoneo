import type { Perfil } from "./tipos";

/**
 * ¿Debe ofrecerse al asesor el botón «Validar perfil»?
 *
 * - `pending_validation`: siempre.
 * - `draft` y `review_due`: solo si la idoneidad está completa. Una alerta «revisar por el asesor» deja el
 *   perfil en borrador, y es el asesor quien la revisa al validar. `review_due` es el estado al que pasa un
 *   perfil activo cuando el cliente cambia un dato en una microentrevista; el asesor lo valida sin otra
 *   entrevista completa (D2). El backend rechaza igualmente un `review_due` incompleto.
 * - `active`: nunca. Si el cliente solo confirma que todo sigue igual, el perfil sigue activo (D3).
 *
 * Esto solo decide si se muestra el botón: validar sigue exigiendo el permiso de asesor y la acción explícita.
 */
export function esValidable(perfil: Pick<Perfil, "status" | "assessments"> | null | undefined): boolean {
  if (!perfil) return false;
  if (perfil.status === "pending_validation") return true;
  if (perfil.status === "draft" || perfil.status === "review_due") {
    return perfil.assessments.suitability.complete;
  }
  return false;
}

/** Un 409 al validar: alguien ha cambiado el perfil mientras el asesor lo revisaba (expected_version). */
export const esConflictoDeVersion = (e: unknown): boolean =>
  typeof e === "object" && e !== null && (e as { status?: unknown }).status === 409;

/** Texto para el asesor. En un conflicto la vista recarga el perfil, así que se le pide revisar la versión nueva. */
export function mensajeErrorValidacion(e: unknown): string {
  if (esConflictoDeVersion(e)) {
    return "El perfil ha cambiado mientras lo revisabas. Hemos cargado la versión nueva: revísala antes de validar.";
  }
  return e instanceof Error ? e.message : String(e);
}
