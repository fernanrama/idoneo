"use client";

import { useConversation } from "@elevenlabs/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { GUION_CARMEN } from "./guion";
import { useOnboarding } from "./onboarding";
import type { Perfil, Turno } from "./tipos";

export type Modo = "voz" | "texto" | "guion";
export type EstadoEntrevista = "inactiva" | "conectando" | "activa" | "terminada" | "error";
export type EstadoAsistente = "reposo" | "habla" | "escucha" | "anotado" | "pausa" | "pensando";

const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;
const SONDEO_MS = 1500;
const DESTELLO_MS = 1600;

/** Cuántos datos MiFID tienen ya valor: cuando sube, el aura destella «Anotado». */
function datosConValor(p: Perfil | null): number {
  if (!p) return 0;
  return Object.values(p.mifid).filter((f) => f.value !== null && f.value !== undefined).length;
}

/**
 * Lógica de la entrevista. Debe usarse dentro de <ConversationProvider> de @elevenlabs/react.
 *
 * - modo "voz": agente conversacional de ElevenLabs. El SDK entrega los mensajes sin tiempos, así que
 *   los marcamos en el cliente: el turno del cliente va desde que el agente deja de hablar
 *   (cambio a "listening") hasta que llega su transcripción. Es una APROXIMACIÓN, por verificar.
 * - modo "texto": el entrevistador de Claude del backend (POST /chat). No gasta minutos de voz.
 * - modo "guion": reproduce GUION_CARMEN (datos simulados) contra el backend real.
 * En todos, el perfil se consulta cada 1,5 s. Las alertas nuevas del verificador se pasan al agente de voz
 * como contexto para que las explique.
 */
export function useEntrevista() {
  const { sesion, setSesion } = useOnboarding();
  const [modo, setModo] = useState<Modo | null>(null);
  const [estado, setEstado] = useState<EstadoEntrevista>("inactiva");
  const [error, setError] = useState<string | null>(null);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [pensando, setPensando] = useState(false);
  const [pausa, setPausa] = useState(false);
  const [destello, setDestello] = useState(0); // marca de tiempo del último dato nuevo

  const inicio = useRef(0);
  const finAgente = useRef(0);
  const sesionRef = useRef(sesion);
  const ultimoTexto = useRef<string | null>(null);
  const alertasVistas = useRef(new Set<string>());
  const temporizadores = useRef<ReturnType<typeof setTimeout>[]>([]);
  const cuentaDatos = useRef(0);

  useEffect(() => {
    sesionRef.current = sesion;
  }, [sesion]);

  const ahora = () => (performance.now() - inicio.current) / 1000;

  const anadirLocal = useCallback((t: Turno) => setTurnos((prev) => [...prev, t]), []);

  const registrar = useCallback(
    (t: Turno) => {
      anadirLocal(t);
      const s = sesionRef.current;
      if (s) api.enviarTurno(s.session_id, t).catch((e) => setError(String(e)));
    },
    [anadirLocal],
  );

  const conversacion = useConversation({
    // Herramienta de cliente del agente (la da de alta scripts/sincronizar_voz.py): el agente pregunta
    // qué falta y el navegador se lo pide al backend, que lo calcula del perfil de forma determinista.
    clientTools: {
      datos_pendientes: async () => {
        const s = sesionRef.current;
        if (!s) return "No hay sesión abierta: sigue el guion.";
        try {
          return (await api.pendientes(s.session_id)).text;
        } catch {
          return "No se ha podido consultar: sigue el guion y no repitas preguntas ya respondidas.";
        }
      },
    },
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

  const nuevaSesion = useCallback(
    async (canal: "voice" | "text" = "voice") => {
      const s = await api.crearSesion(undefined, canal);
      setSesion(s);
      sesionRef.current = s;
      setTurnos([]);
      setPerfil(null);
      setPausa(false);
      alertasVistas.current = new Set();
      cuentaDatos.current = 0;
      inicio.current = performance.now();
      finAgente.current = 0;
      return s;
    },
    [setSesion],
  );

  const iniciarVoz = useCallback(async () => {
    setModo("voz");
    setEstado("conectando");
    setError(null);
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      await nuevaSesion("voice");
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

  /** Pide la siguiente intervención al entrevistador de texto. */
  const turnoTexto = useCallback(
    async (texto: string | null) => {
      const s = sesionRef.current;
      if (!s) return;
      setPensando(true);
      try {
        const r = await api.chat(s.session_id, texto);
        anadirLocal(r.agent_turn);
        if (r.finished) setEstado("terminada");
      } catch (e) {
        const m = e instanceof Error ? e.message : String(e);
        setError(m.startsWith("503") ? "El modo texto no está disponible: el backend no tiene clave de Claude." : m);
      } finally {
        setPensando(false);
      }
    },
    [anadirLocal],
  );

  const iniciarTexto = useCallback(async () => {
    setModo("texto");
    setEstado("conectando");
    setError(null);
    try {
      await nuevaSesion("text");
      setEstado("activa");
      await turnoTexto(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setEstado("error");
    }
  }, [nuevaSesion, turnoTexto]);

  const iniciarGuion = useCallback(
    async (velocidad = 1) => {
      setModo("guion");
      setEstado("conectando");
      setError(null);
      try {
        await nuevaSesion("voice");
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
      if (modo === "texto") {
        anadirLocal({ speaker: "client", text: texto, t_start: t, t_end: t }); // lo guarda POST /chat
        turnoTexto(texto);
        return;
      }
      ultimoTexto.current = texto;
      registrar({ speaker: "client", text: texto, t_start: t, t_end: t });
      if (modo === "voz" && estado === "activa") conversacion.sendUserMessage(texto);
    },
    [anadirLocal, conversacion, estado, modo, registrar, turnoTexto],
  );

  /** En voz silencia el micrófono; el aura se apaga mientras tanto. */
  const alternarPausa = useCallback(() => {
    const nueva = !pausa;
    setPausa(nueva);
    if (modo === "voz") conversacion.setMuted(nueva);
  }, [conversacion, modo, pausa]);

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
        const n = datosConValor(p);
        if (n > cuentaDatos.current) {
          if (cuentaDatos.current > 0 || turnos.length > 0) setDestello(Date.now());
          cuentaDatos.current = n;
        }
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
  }, [sesion, estado, modo, conversacion, turnos.length]);

  // El destello dura un momento y se apaga solo
  const [destelloVivo, setDestelloVivo] = useState(false);
  useEffect(() => {
    if (!destello) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- el destello se enciende al llegar un dato nuevo
    setDestelloVivo(true);
    const id = setTimeout(() => setDestelloVivo(false), DESTELLO_MS);
    return () => clearTimeout(id);
  }, [destello]);

  useEffect(() => () => temporizadores.current.forEach(clearTimeout), []);

  const ultimoAgente = [...turnos].reverse().find((t) => t.speaker === "agent");
  const ultimo = turnos.at(-1);

  let asistente: EstadoAsistente = "reposo";
  if (estado === "conectando" || pensando) asistente = "pensando";
  else if (estado === "activa") {
    if (pausa) asistente = "pausa";
    else if (destelloVivo) asistente = "anotado";
    else if (modo === "voz") asistente = conversacion.isSpeaking ? "habla" : "escucha";
    else asistente = ultimo?.speaker === "agent" ? (modo === "guion" ? "habla" : "escucha") : "escucha";
  }

  return {
    modo,
    estado,
    error,
    turnos,
    perfil,
    pregunta: ultimoAgente?.text ?? null,
    asistente,
    anotado: destelloVivo,
    pausa,
    hablando: conversacion.isSpeaking,
    iniciarVoz,
    iniciarTexto,
    iniciarGuion,
    enviarTexto,
    alternarPausa,
    terminar,
  };
}
