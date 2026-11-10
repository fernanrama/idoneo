import guion from "./guion-carmen.json";
import type { Turno } from "./tipos";

/**
 * GUION DE DEMO — DATOS SIMULADOS.
 * Entrevista corta de Carmen (68 años) para la demo guiada. El texto vive en `guion-carmen.json` para que
 * `backend/scripts/generar_audios_demo.py` pueda grabar con ElevenLabs las voces del entrevistador y de
 * Carmen (`public/demo/carmen/`). Si cambias una frase, vuelve a generar su audio.
 */
export const GUION_CARMEN = guion as Turno[];
