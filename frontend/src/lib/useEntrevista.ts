"use client";

import { useConversation } from "@elevenlabs/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { GUION_CARMEN } from "./guion";
import { useOnboarding } from "./onboarding";
import type { Perfil, Turno } from "./tipos";

export type Modo = "voz" | "guion";
export type EstadoEntrevista = "inactiva" | "conectando" | "activa" | "terminada" | "error";

const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;
const SONDEO_MS = 1500;

/**
 * Lógica de la entrevista. Debe usarse dentro de <ConversationProvider> de @elevenlabs/react.
 *
 * - modo "voz": agente conversacional de ElevenLabs. El SDK entrega los mensajes sin tiempos, así que
 *   los marcamos en el cliente: el turno del cliente va desde que el agente deja de hablar
 *   (cambio a "listening") hasta que llega su transcripción. Es una APROXIMACIÓN, por verificar.
 * - modo "guion": reproduce GUION_CARMEN (datos simulados) contra el backend real.
 * En ambos, cada turno se envía a POST /turns y el perfil se consulta cada 1,5 s.
 * Las alertas nuevas del verificador se pasan al agente de voz como contexto para que las explique.
 */
export function useEntrevista() {
  const { sesion, setSesion } = useOnboarding();
  const [modo, setModo] = useState<Modo | null>(null);
  const [estado, setEstado] = useState<EstadoEntrevista>("inactiva");
  const [error, setError] = useState<string | null>(null);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [perfil, setPerfil] = useState<Perfil | null>(null);

  const inicio = useRef(0);
  const finAgente = useRef(0);
  const sesionRef = useRef(sesion);
  const ultimoTexto = useRef<string | null>(null);
  const alertasVistas = useRef(new Set<string>());
  const temporizadores = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    sesionRef.current = sesion;
  }, [sesion]);

  const ahora = () => (performance.now() - inicio.current) / 1000;

  const registrar = useCallback((t: Turno) => {
    setTurnos((prev) => [...prev, t]);
    const s = sesionRef.current;
    if (s) api.enviarTurno(s.session_id, t).catch((e) => setError(String(e)));
  }, []);

  const conversacion = useConversation({
    onMessage: ({ message, role }) => {
      const t = ahora();
      if (role === "user") {
        if (message === ultimoTexto.current) return; // ya registrado por enviarTexto
        registrar({ speaker: "client", text: message, t_start: Math.min(finAgente.current, t), t_end: t });
      } else {
        registrar({ speaker: "agent", text: message, t_start: t, t_end: t + message.length / 15 });
      }
    },
    onModeChange: ({ mode }) => {
      if (mode === "listening") finAgente.current = ahora();
    },
    onError: (mensaje) => {
      setError(`Voz: ${mensaje}`);
      setEstado("error");
    },
    onDisconnect: () => setEstado((e) => (e === "activa" ? "terminada" : e)),
  });

  const nuevaSesion = useCallback(async () => {
    const s = await api.crearSesion();
    setSesion(s);
    sesionRef.current = s;
    setTurnos([]);
    setPerfil(null);
    alertasVistas.current = new Set();
    inicio.current = performance.now();
    finAgente.current = 0;
    return s;
  }, [setSesion]);

  const iniciarVoz = useCallback(async () => {
    setModo("voz");
    setEstado("conectando");
    setError(null);
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      await nuevaSesion();
      let signedUrl: string | null = null;
      try {
        signedUrl = (await api.urlFirmadaVoz()).signed_url;
      } catch {
        signedUrl = null; // el backend no tiene clave: se intenta con agente público
      }
      if (signedUrl) conversacion.startSession({ signedUrl });
      else if (AGENT_ID) conversacion.startSession({ agentId: AGENT_ID });
      else throw new Error("Falta configurar el agente de voz (NEXT_PUBLIC_ELEVENLABS_AGENT_ID o clave en el backend).");
      setEstado("activa");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setEstado("error");
    }
  }, [conversacion, nuevaSesion]);

  const iniciarGuion = useCallback(
    async (velocidad = 1) => {
      setModo("guion");
      setEstado("conectando");
      setError(null);
      try {
        await nuevaSesion();
        setEstado("activa");
        GUION_CARMEN.forEach((t, i) => {
          const id = setTimeout(() => {
            registrar(t);
            if (i === GUION_CARMEN.length - 1) setEstado("terminada");
          }, (t.t_start * 1000) / velocidad);
          temporizadores.current.push(id);
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setEstado("error");
      }
    },
    [nuevaSesion, registrar],
  );

  const enviarTexto = useCallback(
    (texto: string) => {
      const t = ahora();
      ultimoTexto.current = texto;
      registrar({ speaker: "client", text: texto, t_start: t, t_end: t });
      if (modo === "voz" && estado === "activa") conversacion.sendUserMessage(texto);
    },
    [conversacion, estado, modo, registrar],
  );

  const terminar = useCallback(() => {
    temporizadores.current.forEach(clearTimeout);
    temporizadores.current = [];
    if (modo === "voz") conversacion.endSession();
    setEstado("terminada");
  }, [conversacion, modo]);

  // Sondeo del perfil mientras hay entrevista
  useEffect(() => {
    if (!sesion || (estado !== "activa" && estado !== "terminada")) return;
    let vivo = true;
    const tick = async () => {
      try {
        const p = await api.perfil(sesion.client_id);
        if (!vivo) return;
        setPerfil(p);
        for (const a of p.alerts) {
          if (a.status !== "open" || alertasVistas.current.has(a.id)) continue;
          alertasVistas.current.add(a.id);
          if (modo === "voz" && estado === "activa") {
            conversacion.sendContextualUpdate(
              `El verificador ha detectado esto: ${a.message} Explícaselo al cliente con calma, en lenguaje sencillo y sin juzgarle, y comprueba que lo ha entendido.`,
            );
          }
        }
      } catch {
        /* el backend puede no estar listo; se reintenta en el siguiente ciclo */
      }
    };
    tick();
    const id = setInterval(tick, SONDEO_MS);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, [sesion, estado, modo, conversacion]);

  useEffect(() => () => temporizadores.current.forEach(clearTimeout), []);

  return {
    modo,
    estado,
    error,
    turnos,
    perfil,
    hablando: conversacion.isSpeaking,
    iniciarVoz,
    iniciarGuion,
    enviarTexto,
    terminar,
  };
}
