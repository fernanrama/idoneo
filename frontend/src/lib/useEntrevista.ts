"use client";

import { useConversation } from "@elevenlabs/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { perfilParcial, vocesEspanol } from "./demo";
import { GUION_CARMEN } from "./guion";
import { useOnboarding } from "./onboarding";
import { tokenCliente } from "./credenciales";
import { opcionesVoz } from "./iniciarVoz";
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
 * - modo "guion": demo guiada. Repite la entrevista simulada de Carmen con sus audios grabados (o las voces
 *   del navegador) y reconstruye su perfil dato a dato (ver lib/demo.ts). El backend solo crea, sin IA, una
 *   copia propia de Carmen para esta pestaña, que es la que se ve al final en «Mi perfil».
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
  // Demo guiada
  const [fuenteDemo, setFuenteDemo] = useState<Perfil | null>(null);
  const [paso, setPaso] = useState(0);
  const [vozDemo, setVozDemo] = useState(true);
  const [velocidad, setVelocidad] = useState(1);
  // Entrevista corta del pitch (solo con el modo asesor de demostración)
  const [corta, setCortaEstado] = useState(false);
  const cortaRef = useRef(false);
  const setCorta = useCallback((v: boolean) => {
    cortaRef.current = v;
    setCortaEstado(v);
  }, []);
  const audiosDemo = useRef<Record<string, { archivo: string; texto: string }>>({});

  const inicio = useRef(0);
  const finAgente = useRef(0);
  const sesionRef = useRef(sesion);
  const ultimoTexto = useRef<string | null>(null);
  const alertasVistas = useRef(new Set<string>());
  const temporizadores = useRef<ReturnType<typeof setTimeout>[]>([]);
  const cuentaDatos = useRef(0);
  const idConversacion = useRef<string | null>(null);

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
    onConnect: ({ conversationId }) => {
      idConversacion.current = conversationId;
    },
    onDisconnect: () => {
      setEstado((e) => (e === "activa" ? "terminada" : e));
      // Pruebas de audio: el backend descarga de ElevenLabs el audio de esta llamada y comprueba allí que
      // se creó para esta sesión. Si la voz no está configurada en el backend, no pasa nada.
      const s = sesionRef.current;
      const conversacionId = idConversacion.current;
      idConversacion.current = null;
      if (s && conversacionId) api.registrarAudio(s.session_id, conversacionId).catch(() => {});
    },
  });

  const nuevaSesion = useCallback(
    async (canal: "voice" | "text" = "voice") => {
      const previo = sesionRef.current?.client_id;
      const s = cortaRef.current
        ? await api.entrevistaCorta(canal)
        : await api.crearSesion(previo && tokenCliente(previo) ? previo : undefined, canal);
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
      const s = await nuevaSesion("voice");
      await conversacion.startSession(await opcionesVoz(s.session_id, AGENT_ID));
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
      setError(null);
      try {
        const r = await api.chat(s.session_id, texto);
        anadirLocal(r.agent_turn);
        if (r.finished) setEstado("terminada");
      } catch (e) {
        const m = e instanceof Error ? e.message : String(e);
        if (m.startsWith("503")) {
          setError("El modo texto no está disponible: el backend no tiene clave de Claude.");
          setEstado("error");
        } else if (m.startsWith("429")) {
          setError(m.slice(4));
          setEstado("error");
        } else {
          // La entrevista sigue abierta: lo escrito ya está guardado y basta con pedir otra vez la pregunta.
          setError(m.startsWith("502")
            ? "El asistente no ha podido responder. Pulsa «Reintentar»."
            : `No se ha podido enviar (${m.split(" ")[0]}). Pulsa «Reintentar».`);
        }
      } finally {
        setPensando(false);
      }
    },
    [anadirLocal],
  );

  /** Vuelve a pedir la intervención del asistente tras un fallo, sin perder la sesión ni lo escrito. */
  const reintentar = useCallback(() => {
    void turnoTexto(null);
  }, [turnoTexto]);

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

  const iniciarGuion = useCallback(async (velocidadInicial = 1) => {
    setModo("guion");
    setEstado("conectando");
    setError(null);
    try {
      // Cada demo es una copia propia y ficticia de Carmen, con su credencial (sin IA): al acabar se llega
      // al mismo perfil que tras una entrevista de verdad (memoria, «ha cambiado algo», validación).
      let fuente: Perfil;
      try {
        const s = await api.sesionDemo();
        setSesion(s);
        sesionRef.current = s;
        fuente = await api.perfil(s.client_id);
      } catch {
        setSesion(null); // sin copia (p. ej., tope diario): se repite la Carmen fija, de solo lectura
        fuente = await api.perfilDemo();
      }
      setFuenteDemo(fuente);
      setVelocidad(velocidadInicial);
      setPaso(0);
      setPausa(false);
      cuentaDatos.current = 0;
      setVozDemo(true);
      // Audios grabados con ElevenLabs (scripts/generar_audios_demo.py); si faltan, voz del navegador.
      try {
        const r = await fetch("/demo/carmen/manifest.json", { cache: "no-store" });
        audiosDemo.current = r.ok ? ((await r.json()).turnos ?? {}) : {};
      } catch {
        audiosDemo.current = {};
      }
      setEstado("activa");
    } catch (e) {
      setError(e instanceof Error ? `No se ha podido cargar la demo: ${e.message}` : String(e));
      setEstado("error");
    }
  }, [setSesion]);

  // Reproduce el turno actual de la demo y pasa al siguiente al acabar (con voz o por tiempo de lectura).
  useEffect(() => {
    if (modo !== "guion" || estado !== "activa") return;
    if (paso >= GUION_CARMEN.length) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- fin natural de la demo
      setEstado("terminada");
      return;
    }
    if (pausa) return;
    const turno = GUION_CARMEN[paso];
    let vivo = true;
    let espera: ReturnType<typeof setTimeout> | undefined;
    const siguiente = (ms: number) => {
      clearTimeout(espera);
      espera = setTimeout(() => vivo && setPaso((p) => p + 1), ms);
    };
    const lectura = (900 + turno.text.length * 45) / velocidad;
    const sintesis = typeof window !== "undefined" && "speechSynthesis" in window ? window.speechSynthesis : null;
    const grabado = audiosDemo.current[String(paso)];
    let audio: HTMLAudioElement | null = null;
    if (vozDemo && grabado && grabado.texto === turno.text) {
      audio = new Audio(`/demo/carmen/${grabado.archivo}`);
      audio.playbackRate = velocidad;
      audio.preservesPitch = true;
      audio.onended = () => vivo && siguiente(300);
      audio.onerror = () => vivo && siguiente(lectura);
      audio.play().catch(() => vivo && siguiente(lectura)); // p. ej., el navegador bloquea el sonido
      siguiente(lectura * 3 + 4000); // por si el audio no avisa del final
    } else if (vozDemo && sintesis) {
      const { asistente, cliente } = vocesEspanol();
      const u = new SpeechSynthesisUtterance(turno.text);
      u.lang = "es-ES";
      const v = turno.speaker === "agent" ? asistente : cliente;
      if (v) u.voice = v;
      u.pitch = turno.speaker === "agent" ? 1 : 1.25;
      u.rate = (turno.speaker === "agent" ? 1.08 : 0.98) * velocidad;
      u.onend = () => vivo && siguiente(350);
      sintesis.cancel();
      sintesis.speak(u);
      siguiente(lectura * 2.2 + 1500); // por si el navegador no avisa del final
    } else {
      siguiente(lectura);
    }
    return () => {
      vivo = false;
      clearTimeout(espera);
      audio?.pause();
      sintesis?.cancel();
    };
  }, [modo, estado, pausa, paso, vozDemo, velocidad]);

  const turnosDemo = useMemo(() => GUION_CARMEN.slice(0, Math.min(paso + 1, GUION_CARMEN.length)), [paso]);
  const perfilDemo = useMemo(
    () => (fuenteDemo ? perfilParcial(fuenteDemo, GUION_CARMEN.slice(0, paso), paso >= GUION_CARMEN.length) : null),
    [fuenteDemo, paso],
  );
  useEffect(() => {
    if (modo !== "guion" || !perfilDemo) return;
    const n = datosConValor(perfilDemo);
    if (n > cuentaDatos.current) {
      if (cuentaDatos.current > 0 || paso > 0) setDestello(Date.now());
      cuentaDatos.current = n;
    }
  }, [modo, perfilDemo, paso]);

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
    if (modo === "guion") {
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      setPaso(GUION_CARMEN.length);
    }
    setEstado("terminada");
  }, [conversacion, modo]);

  // Sondeo del perfil mientras hay entrevista
  useEffect(() => {
    // En la demo el perfil se reconstruye en el navegador (lib/demo.ts): no hace falta preguntar.
    if (!sesion || modo === "guion" || (estado !== "activa" && estado !== "terminada")) return;
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
          // Lo que es para el asesor (posible vulnerabilidad, presión de terceros…) no se lee al cliente.
          if (a.flag === "needs_advisor" || !a.path) continue;
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

  const turnosVista = modo === "guion" ? turnosDemo : turnos;
  const ultimoAgente = [...turnosVista].reverse().find((t) => t.speaker === "agent");
  const ultimo = turnosVista.at(-1);

  let asistente: EstadoAsistente = "reposo";
  if (estado === "conectando" || pensando) asistente = "pensando";
  else if (estado === "activa") {
    if (pausa) asistente = "pausa";
    else if (destelloVivo) asistente = "anotado";
    else if (modo === "voz") asistente = conversacion.isSpeaking ? "habla" : "escucha";
    else if (modo === "guion") asistente = ultimo?.speaker === "agent" ? "habla" : "escucha";
    else asistente = "escucha";
  }

  return {
    modo,
    estado,
    error,
    turnos: turnosVista,
    perfil: modo === "guion" ? perfilDemo : perfil,
    pregunta: ultimoAgente?.text ?? null,
    demo: {
      respuesta: modo === "guion" && ultimo?.speaker === "client" ? ultimo.text : null,
      paso: Math.min(paso + 1, GUION_CARMEN.length),
      total: GUION_CARMEN.length,
      voz: vozDemo,
      alternarVoz: () => setVozDemo((v) => !v),
      velocidad,
      cambiarVelocidad: () => setVelocidad((v) => (v === 1 ? 1.5 : v === 1.5 ? 2 : 1)),
      siguiente: () => setPaso((p) => Math.min(p + 1, GUION_CARMEN.length)),
    },
    asistente,
    anotado: destelloVivo,
    pausa,
    hablando: conversacion.isSpeaking,
    iniciarVoz,
    iniciarTexto,
    reintentar,
    corta,
    setCorta,
    iniciarGuion,
    enviarTexto,
    alternarPausa,
    terminar,
  };
}
