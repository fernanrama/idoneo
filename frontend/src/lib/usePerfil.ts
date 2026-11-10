"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Perfil, Restricciones } from "./tipos";

/**
 * Carga perfil y restricciones de un cliente; `recargar` tras validar.
 * Con `sondeoMs` los vuelve a pedir cada cierto tiempo: así la vista de la entidad se rellena en vivo
 * mientras el cliente habla en otra pantalla (el backend aún no emite eventos).
 */
export function usePerfil(clientId: string, sondeoMs?: number) {
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [restricciones, setRestricciones] = useState<Restricciones | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    try {
      const [p, r] = await Promise.all([api.perfil(clientId), api.restricciones(clientId)]);
      setPerfil(p);
      setRestricciones(r);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [clientId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial de datos remotos
    recargar();
    if (!sondeoMs) return;
    const id = setInterval(recargar, sondeoMs);
    return () => clearInterval(id);
  }, [recargar, sondeoMs]);

  return { perfil, restricciones, error, recargar };
}
