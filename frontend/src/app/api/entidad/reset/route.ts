import { CLIENTE_DEMO } from "@/lib/credenciales";
import { configAsesorDemo, esPeticionLocal, llamarBackend, respuestaJson } from "@/lib/servidor/asesorDemo";

/**
 * Sin el modo asesor de demo, la demo es fija: no hay puente anónimo que borre al Carmen persistido.
 * Con DEMO_ADVISOR_MODE=1, recarga el cliente ficticio de la demo para repetir el ensayo.
 */
export async function POST(req: Request) {
  const conf = configAsesorDemo();
  if (!conf) {
    return respuestaJson({ detail: "La demo guiada usa un ejemplo fijo y no necesita reiniciar clientes." }, 403);
  }
  if (!esPeticionLocal(req)) return respuestaJson({ detail: "El modo asesor de demo solo funciona en local." }, 403);
  return llamarBackend(conf, `/clientes/${CLIENTE_DEMO}/reiniciar`, "POST");
}
