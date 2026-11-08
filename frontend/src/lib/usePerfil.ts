"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Perfil, Restricciones } from "./tipos";

/** Carga perfil y restricciones de un cliente; `recargar` tras validar. */
export function usePerfil(clientId: string) {
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
  }, [recargar]);

  return { perfil, restricciones, error, recargar };
}
