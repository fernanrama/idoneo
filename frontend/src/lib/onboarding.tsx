"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Sesion } from "./tipos";

// Estado compartido del onboarding entre pantallas (persistido en localStorage para sobrevivir recargas).
interface EstadoOnboarding {
  sesion: Sesion | null;
  setSesion: (s: Sesion | null) => void;
  clientId: string; // cliente cuyo perfil se muestra; por defecto, el ejemplo simulado de Carmen
}

const CLAVE = "idoneo.sesion";
export const CLIENTE_DEMO = "carmen-68";

const Ctx = createContext<EstadoOnboarding | null>(null);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [sesion, setSesionState] = useState<Sesion | null>(null);

  useEffect(() => {
    const guardada = localStorage.getItem(CLAVE);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- lectura única de localStorage al montar
    if (guardada) setSesionState(JSON.parse(guardada));
  }, []);

  const setSesion = useCallback((s: Sesion | null) => {
    setSesionState(s);
    if (s) localStorage.setItem(CLAVE, JSON.stringify(s));
    else localStorage.removeItem(CLAVE);
  }, []);

  return (
    <Ctx.Provider value={{ sesion, setSesion, clientId: sesion?.client_id ?? CLIENTE_DEMO }}>
      {children}
    </Ctx.Provider>
  );
}

export function useOnboarding() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useOnboarding fuera de OnboardingProvider");
  return v;
}
