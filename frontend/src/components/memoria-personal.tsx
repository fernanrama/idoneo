"use client";

import { useEffect, useState } from "react";
import { api, ErrorAPI } from "@/lib/api";
import type { MemoriaPersonal as Memoria } from "@/lib/tipos";
import s from "./memoria-personal.module.css";

type Trato = "usted" | "tu";
type Detalle = "low" | "normal" | "high";
type Ritmo = "slow" | "normal" | "fast";

export function MemoriaPersonal({ sessionId }: { sessionId: string }) {
  return <FormularioMemoria key={sessionId} sessionId={sessionId} />;
}

function FormularioMemoria({ sessionId }: { sessionId: string }) {
  const [activa, setActiva] = useState(false);
  const [consiente, setConsiente] = useState(false);
  const [etag, setEtag] = useState<string | null>(null);
  const [trato, setTrato] = useState<Trato>("usted");
  const [detalle, setDetalle] = useState<Detalle>("normal");
  const [ritmo, setRitmo] = useState<Ritmo>("normal");
  const [ocupada, setOcupada] = useState(true);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function cargarValores(memoria: Memoria) {
    const valor = memoria.data.communication;
    const preferencias = valor && typeof valor === "object" ? valor as Record<string, unknown> : {};
    setActiva(memoria.enabled);
    setEtag(memoria.etag);
    setConsiente(false); // Cada escritura exige una decisión explícita, también tras un conflicto.
    setTrato(preferencias.treatment === "tu" ? "tu" : "usted");
    setDetalle(preferencias.detail === "low" || preferencias.detail === "high" ? preferencias.detail : "normal");
    setRitmo(preferencias.pace === "slow" || preferencias.pace === "fast" ? preferencias.pace : "normal");
  }

  useEffect(() => {
    let viva = true;
    api.memoria(sessionId)
      .then((m) => { if (viva) cargarValores(m); })
      .catch((e) => { if (viva) setError(e instanceof Error ? e.message : "No se ha podido cargar la memoria."); })
      .finally(() => { if (viva) setOcupada(false); });
    return () => { viva = false; };
  }, [sessionId]);

  function fallo(e: unknown) {
    if (e instanceof ErrorAPI && e.status === 412) {
      // No actualizar revisión ni repetir PUT/DELETE automáticamente: podría reactivar una memoria borrada.
      setEtag(null);
      setConsiente(false);
    }
    setError(e instanceof Error ? e.message : "No se ha podido actualizar la memoria.");
  }

  async function recargar() {
    setOcupada(true);
    setError(null);
    setMensaje(null);
    try { cargarValores(await api.memoria(sessionId)); }
    catch (e) { fallo(e); }
    finally { setOcupada(false); }
  }

  async function guardar() {
    if (!etag || !consiente || ocupada) return;
    setOcupada(true);
    setError(null);
    setMensaje(null);
    try {
      cargarValores(await api.guardarMemoria(sessionId, etag, consiente, {
        communication: { treatment: trato, detail: detalle, pace: ritmo, language: "es" },
      }));
      setMensaje("Preferencias guardadas. Se aplicarán al empezar tu próxima conversación.");
    } catch (e) { fallo(e); }
    finally { setOcupada(false); }
  }

  async function olvidar() {
    if (!etag || ocupada) return;
    setOcupada(true);
    setError(null);
    setMensaje(null);
    try {
      cargarValores(await api.borrarMemoria(sessionId, etag));
      setMensaje("Hemos borrado tus preferencias personales. Tu expediente MiFID no se ha modificado.");
    } catch (e) { fallo(e); }
    finally { setOcupada(false); }
  }

  return (
    <section className={s.tarjeta} aria-labelledby="memoria-titulo">
      <div className={s.cabecera}>
        <span className={s.icono} aria-hidden="true">↻</span>
        <div>
          <h2 id="memoria-titulo">Recordar cómo prefieres hablar</h2>
          <p>Estas opciones sustituyen tus preferencias de conversación anteriores y se guardan separadas del expediente MiFID.</p>
        </div>
      </div>
      <span className={`${s.estado} ${activa ? s.estadoActiva : ""}`}>
        {activa ? "Memoria personal activa" : "No estamos recordando preferencias"}
      </span>
      <fieldset className={s.campos} disabled={ocupada || !etag}>
        <label className={s.campo}>
          <span>Cómo dirigirse a ti</span>
          <select value={trato} onChange={(e) => setTrato(e.target.value as Trato)}>
            <option value="usted">De usted</option><option value="tu">De tú</option>
          </select>
        </label>
        <label className={s.campo}>
          <span>Nivel de detalle</span>
          <select value={detalle} onChange={(e) => setDetalle(e.target.value as Detalle)}>
            <option value="low">Breve</option><option value="normal">Normal</option><option value="high">Con más contexto</option>
          </select>
        </label>
        <label className={s.campo}>
          <span>Ritmo</span>
          <select value={ritmo} onChange={(e) => setRitmo(e.target.value as Ritmo)}>
            <option value="slow">Pausado</option><option value="normal">Normal</option><option value="fast">Ágil</option>
          </select>
        </label>
      </fieldset>
      <label className={s.consentimiento}>
        <input type="checkbox" checked={consiente} disabled={ocupada || !etag} onChange={(e) => setConsiente(e.target.checked)} />
        <span>Autorizo a guardar estas preferencias para futuras conversaciones. Puedo borrarlas cuando quiera.</span>
      </label>
      <p>Borrar memoria elimina toda tu capa personal, incluidas otras preferencias guardadas. No borra tu expediente MiFID.</p>
      <div className={`${s.acciones} ${activa ? s.accionesConBorrado : ""}`}>
        <button type="button" className={s.boton} onClick={guardar} disabled={ocupada || !consiente || !etag}>
          {ocupada ? "Cargando…" : "Guardar preferencias"}
        </button>
        {activa && <button type="button" className={s.botonBorrar} onClick={olvidar} disabled={ocupada || !etag}>Borrar memoria personal</button>}
        {!etag && !ocupada && <button type="button" className={s.botonBorrar} onClick={recargar}>Volver a cargar la memoria</button>}
      </div>
      {mensaje && <p className={s.mensaje} role="status">{mensaje}</p>}
      {error && <p className={`${s.mensaje} ${s.error}`} role="alert">{error}</p>}
    </section>
  );
}
