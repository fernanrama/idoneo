"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Perfil, Restricciones, VersionResumen } from "./tipos";

/**
 * Carga perfil y restricciones de un cliente; `recargar` tras validar.
 * Con `sondeoMs` los vuelve a pedir cada cierto tiempo: así la vista de la entidad se rellena en vivo
 * mientras el cliente habla en otra pantalla (el backend aún no emite eventos).
 * Con `asesor` lee el expediente mediante el modo asesor de demo (incluye el historial);
 * con `esperar` no pide nada hasta saber qué fuente usar.
 */
export function usePerfil(clientId: string, sondeoMs?: number, { asesor = false, esperar = false } = {}) {
  const [vista, setVista] = useState<{
    clientId: string | null;
    perfil: Perfil | null;
    restricciones: Restricciones | null;
    versiones: VersionResumen[] | null;
    error: string | null;
  }>({ clientId: null, perfil: null, restricciones: null, versiones: null, error: null });
  const revision = useRef(0);
  const enCurso = useRef<string | null>(null);
  const cancelarPeticiones = useCallback(() => {
    ++revision.current;
    enCurso.current = null;
  }, []);

  const recargar = useCallback(async () => {
    if (!clientId || esperar || enCurso.current === clientId) return;
    const peticion = ++revision.current;
    enCurso.current = clientId;
    try {
      if (asesor) {
        const e = await api.expedienteAsesor(clientId);
        if (peticion !== revision.current) return;
        setVista({ clientId, perfil: e.profile, restricciones: e.constraints, versiones: e.versions, error: null });
        return;
      }
      const [p, r] = await Promise.all([api.perfil(clientId), api.restricciones(clientId)]);
      if (peticion !== revision.current) return;
      setVista({ clientId, perfil: p, restricciones: r, versiones: null, error: null });
    } catch (e) {
      if (peticion !== revision.current) return;
      setVista({ clientId, perfil: null, restricciones: null, versiones: null,
        error: e instanceof Error ? e.message : String(e) });
    } finally {
      if (peticion === revision.current) enCurso.current = null;
    }
  }, [clientId, asesor, esperar]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial de datos remotos
    recargar();
    const id = sondeoMs ? setInterval(recargar, sondeoMs) : undefined;
    return () => {
      cancelarPeticiones(); // invalida también peticiones anteriores al cambio de cliente
      if (id !== undefined) clearInterval(id);
    };
  }, [recargar, sondeoMs, cancelarPeticiones]);

  // No mostrar datos del cliente anterior entre el render y la limpieza del efecto.
  const vigente = vista.clientId === clientId;
  return { perfil: vigente ? vista.perfil : null, restricciones: vigente ? vista.restricciones : null,
    versiones: vigente ? vista.versiones : null, error: vigente ? vista.error : null, recargar };
}
