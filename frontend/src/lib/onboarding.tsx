"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { CLIENTE_DEMO, persistirSesion, restaurarSesion } from "./credenciales";
import type { AltaSesion, Sesion } from "./tipos";

export { CLIENTE_DEMO } from "./credenciales";

interface EstadoOnboarding {
  sesion: Sesion | null;
  setSesion: (s: AltaSesion | null) => void;
  clientId: string;
  /** Ya se ha leído la sesión guardada en esta pestaña (antes de eso, `sesion` es null siempre). */
  listo: boolean;
}

const Ctx = createContext<EstadoOnboarding | null>(null);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [sesion, setSesionState] = useState<Sesion | null>(null);
  const [listo, setListo] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- recuperar metadatos, con credencial de esta pestaña
    setSesionState(restaurarSesion());
    setListo(true);
  }, []);

  const setSesion = useCallback((s: AltaSesion | null) => {
    setSesionState(persistirSesion(s));
  }, []);

  return (
    <Ctx.Provider value={{ sesion, setSesion, clientId: sesion?.client_id ?? CLIENTE_DEMO, listo }}>
      {children}
    </Ctx.Provider>
  );
}

export function useOnboarding() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useOnboarding fuera de OnboardingProvider");
  return v;
}
