import { validacionNoDisponible } from "@/lib/servidor/entidad";

/** No convertir la credencial de un cliente en permiso de revisión de la entidad. */
export function POST() {
  return validacionNoDisponible();
}
