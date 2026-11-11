import { configAsesorDemo, esPeticionLocal, llamarBackend, respuestaJson } from "@/lib/servidor/asesorDemo";

/** Cliente ficticio casi completo para la entrevista corta del pitch (backend/fixtures/carmen-corta.json). */
const CLIENTE_CORTA = "carmen-corta";

/**
 * Entrevista corta del pitch: con DEMO_ADVISOR_MODE=1, recarga `carmen-corta`, abre una sesión y devuelve
 * su credencial de cliente. El token del asesor lo pone este servidor; el navegador no envía ninguno.
 * Sin el modo asesor, no existe (403), igual que el resto de acciones de demo.
 */
export async function POST(req: Request) {
  const conf = configAsesorDemo();
  if (!conf) return respuestaJson({ detail: "La entrevista corta solo existe con el modo asesor de demostración." }, 403);
  if (!esPeticionLocal(req)) return respuestaJson({ detail: "El modo asesor de demo solo funciona en local." }, 403);
  const canal = new URL(req.url).searchParams.get("channel") === "text" ? "text" : "voice";
  return llamarBackend(conf, `/clientes/${CLIENTE_CORTA}/entrevista?channel=${canal}`, "POST");
}
