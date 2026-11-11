"use client";

import { useEffect, useState } from "react";
import { API_URL } from "./api";
import { tokenCliente } from "./credenciales";
import { GUION_CARMEN } from "./guion";
import type { Evidencia, Perfil } from "./tipos";

/**
 * Pruebas de audio: cada evidencia suena con el fragmento de la llamada en que el cliente lo dijo.
 *
 * - Entrevistas reales por voz: el backend guarda el audio de la sesión (descargado de ElevenLabs al
 *   colgar) y dice en qué segundos está cada evidencia (`GET /api/clients/{id}/audio`). Se descarga una
 *   vez por sesión, con la credencial del cliente, y se reproduce solo el fragmento.
 * - Carmen (DATOS SIMULADOS, sesión `s-demo`): su frase grabada con ElevenLabs para la demo guiada
 *   (`public/demo/carmen/`), localizada por la cita. Funciona también en el despliegue público.
 */

export interface Fragmento {
  url: string;
  start: number;
  end: number | null; // null: el archivo entero
  exact: boolean;
  privado: boolean; // true: pide la credencial del cliente
}

type Mapa = Record<string, (Fragmento | null)[]>;

const SESION_DEMO = "s-demo";

function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9ñ ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** La frase de Carmen grabada para la demo guiada que contiene la cita de la evidencia. */
export function fragmentoDemo(ev: Evidencia): Fragmento | null {
  if (ev.session_id !== SESION_DEMO) return null;
  const cita = normalizar(ev.quote);
  if (!cita) return null;
  const indice = GUION_CARMEN.findIndex((t) => {
    if (t.speaker !== "client") return false;
    const texto = normalizar(t.text);
    return texto.includes(cita) || cita.includes(texto);
  });
  if (indice < 0) return null;
  const archivo = `${String(indice).padStart(2, "0")}-client.mp3`;
  return { url: `/demo/carmen/${archivo}`, start: 0, end: null, exact: true, privado: false };
}

/** Fragmentos de audio de cada dato del perfil. Se vuelve a pedir cuando cambia la versión. */
export function useFragmentos(cid: string, perfil: Perfil | null): Mapa {
  const [mapa, setMapa] = useState<Mapa>({});
  const version = perfil?.version;
  const conVoz = perfil
    ? Object.values(perfil.mifid).some((f) => f.evidence.some((e) => e.session_id !== SESION_DEMO))
    : false;
  useEffect(() => {
    const token = tokenCliente(cid);
    if (!conVoz || !token || version == null) return;
    let vivo = true;
    fetch(`${API_URL}/api/clients/${encodeURIComponent(cid)}/audio`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { evidence?: Record<string, ({ url: string; start: number; end: number; exact: boolean } | null)[]> } | null) => {
        if (!vivo || !d?.evidence) return;
        const nuevo: Mapa = {};
        for (const [ruta, lista] of Object.entries(d.evidence)) {
          nuevo[ruta] = lista.map((x) => (x ? { url: `${API_URL}${x.url}`, start: x.start, end: x.end, exact: x.exact, privado: true } : null));
        }
        setMapa(nuevo);
      })
      .catch(() => {});
    return () => {
      vivo = false;
    };
  }, [cid, version, conVoz]);
  return mapa;
}

export function fragmentoDe(mapa: Mapa, ruta: string, indice: number, ev: Evidencia): Fragmento | null {
  return mapa[ruta]?.[indice] ?? fragmentoDemo(ev);
}

// Un audio por sesión, descargado una vez con la credencial y guardado como URL local del navegador.
const cache = new Map<string, Promise<string>>();

async function fuente(f: Fragmento, cid: string): Promise<string> {
  if (!f.privado) return f.url;
  let promesa = cache.get(f.url);
  if (!promesa) {
    const token = tokenCliente(cid);
    promesa = fetch(f.url, { headers: token ? { Authorization: `Bearer ${token}` } : {}, cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error(String(r.status));
        return r.blob();
      })
      .then((b) => URL.createObjectURL(b));
    promesa.catch(() => cache.delete(f.url));
    cache.set(f.url, promesa);
  }
  return promesa;
}

export type EstadoClip = "parado" | "cargando" | "sonando" | "error";

// Un único reproductor para toda la página, fuera de React: al pulsar otro fragmento, el anterior se para.
let reproductor: HTMLAudioElement | null = null;
const obtenerReproductor = () => (reproductor ??= new Audio());

async function sonar(f: Fragmento, src: string, alAcabar: () => void): Promise<void> {
  const a = obtenerReproductor();
  a.pause();
  a.ontimeupdate = () => {
    if (f.end != null && a.currentTime >= f.end) {
      a.pause();
      alAcabar();
    }
  };
  a.onended = alAcabar;
  if (a.dataset.fuente !== src) {
    a.dataset.fuente = src;
    a.src = src;
    await new Promise<void>((ok, mal) => {
      a.onloadedmetadata = () => ok();
      a.onerror = () => mal(new Error("audio"));
    });
  }
  a.currentTime = f.start;
  await a.play();
}

function pararReproductor() {
  reproductor?.pause();
}

/** Estado del fragmento que suena en esta vista. */
export function useReproductor(cid: string) {
  const [activo, setActivo] = useState<{ clave: string; estado: EstadoClip } | null>(null);

  useEffect(() => pararReproductor, []);

  const parar = () => {
    pararReproductor();
    setActivo(null);
  };

  const reproducir = async (clave: string, f: Fragmento) => {
    if (activo?.clave === clave && activo.estado === "sonando") return parar();
    pararReproductor();
    setActivo({ clave, estado: "cargando" });
    try {
      const src = await fuente(f, cid);
      await sonar(f, src, () => setActivo((x) => (x?.clave === clave ? null : x)));
      setActivo({ clave, estado: "sonando" });
    } catch {
      setActivo({ clave, estado: "error" });
    }
  };

  return { activo, reproducir, parar };
}
