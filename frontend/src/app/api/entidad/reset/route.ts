/** La demo es fija. No ofrecer un puente anónimo que borre al Carmen persistido. */
export async function POST() {
  return Response.json({ detail: "La demo guiada usa un ejemplo fijo y no necesita reiniciar clientes." },
    { status: 403, headers: { "Cache-Control": "no-store" } });
}
