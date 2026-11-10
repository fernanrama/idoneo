import guion from "./guion-carmen.json";
import type { Turno } from "./tipos";

/**
 * GUION DE DEMO — DATOS SIMULADOS.
 * Entrevista corta de Carmen (68 años) para la demo guiada. El texto vive en `guion-carmen.json`; los audios
 * grabados de cada turno, si existen, van en `public/demo/carmen/`. Si cambias una frase, regraba su audio.
 */
export const GUION_CARMEN = guion as Turno[];
