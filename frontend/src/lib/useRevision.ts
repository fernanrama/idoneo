"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import { tokenCliente } from "./credenciales";
import type { Revision } from "./tipos";

/**
 * Revisión «Ha cambiado algo» del cliente. Con `sondeoMs` se vuelve a pedir cada cierto tiempo: así la
 * entrevista marca cada pregunta como contestada en cuanto el perfil la recoge.
 */
export function useRevision(clientId: string, sondeoMs?: number): Revision | null {
  const [revision, setRevision] = useState<{ cid: string; r: Revision } | null>(null);
  const propio = Boolean(tokenCliente(clientId));
  useEffect(() => {
    if (!propio) return;
    let vivo = true;
    const tick = () =>
      api.revision(clientId).then((r) => vivo && setRevision({ cid: clientId, r })).catch(() => undefined);
    tick();
    const id = sondeoMs ? setInterval(tick, sondeoMs) : undefined;
    return () => {
      vivo = false;
      if (id !== undefined) clearInterval(id);
    };
  }, [clientId, propio, sondeoMs]);
  return propio && revision?.cid === clientId ? revision.r : null;
}

/** Si esta pestaña tiene la credencial del cliente. Se lee tras montar, para no desajustar la hidratación. */
export function useEsPropio(clientId: string): boolean {
  const [propio, setPropio] = useState(false);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- la credencial solo existe en el navegador
    setPropio(Boolean(tokenCliente(clientId)));
  }, [clientId]);
  return propio;
}
