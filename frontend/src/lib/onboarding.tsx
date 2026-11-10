"use client";

import { usePathname } from "next/navigation";
import { MemoriaPersonal } from "@/components/memoria-personal";
import { Suspense, createContext, useCallback, useContext, useEffect, useState } from "react";
import { CLIENTE_DEMO, persistirSesion, restaurarSesion } from "./credenciales";
import type { AltaSesion, Sesion } from "./tipos";

export { CLIENTE_DEMO } from "./credenciales";

interface EstadoOnboarding {
  sesion: Sesion | null;
  setSesion: (s: AltaSesion | null) => void;
  clientId: string;
}

const Ctx = createContext<EstadoOnboarding | null>(null);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [sesion, setSesionState] = useState<Sesion | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- recuperar metadatos, con credencial de esta pestaña
    setSesionState(restaurarSesion());
  }, []);

  const setSesion = useCallback((s: AltaSesion | null) => {
    setSesionState(persistirSesion(s));
  }, []);

  return (
    <Ctx.Provider value={{ sesion, setSesion, clientId: sesion?.client_id ?? CLIENTE_DEMO }}>
      {children}
      <Suspense fallback={null}>
        {sesion && <MemoriaEnPagina sessionId={sesion.session_id} />}
      </Suspense>
    </Ctx.Provider>
  );
}

function MemoriaEnPagina({ sessionId }: { sessionId: string }) {
  const pathname = usePathname();
  if (pathname !== "/onboarding/perfil") return null;
  return (
    <div style={{ width: "min(1040px, calc(100% - 32px))", margin: "24px auto" }}>
      <MemoriaPersonal sessionId={sessionId} />
    </div>
  );
}

export function useOnboarding() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useOnboarding fuera de OnboardingProvider");
  return v;
}
