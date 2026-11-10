/**
 * Bloqueo provisional: la posesión del cliente no acredita un permiso de asesor.
 * No añadir ADMIN_TOKEN a una petición del navegador. La autorización independiente
 * de entidad debe acordarse antes de habilitar de nuevo esta acción.
 */
export function validacionNoDisponible(): Response {
  return Response.json({ detail: "La validación requiere un permiso independiente de asesor. Esta acción aún no está habilitada en el navegador." },
    { status: 403, headers: { "Cache-Control": "no-store" } });
}
