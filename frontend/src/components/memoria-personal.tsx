"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Boton } from "./ui";
import s from "./memoria-personal.module.css";

type Trato = "usted" | "tu";
type Detalle = "low" | "normal" | "high";
type Ritmo = "slow" | "normal" | "fast";

function comunicacion(data: Record<string, unknown>) {
  const valor = data.communication;
  return valor && typeof valor === "object" ? (valor as Record<string, unknown>) : {};
}

export function MemoriaPersonal({ sessionId }: { sessionId: string }) {
  const [activa, setActiva] = useState(false);
  const [consiente, setConsiente] = useState(false);
  const [trato, setTrato] = useState<Trato>("usted");
  const [detalle, setDetalle] = useState<Detalle>("normal");
  const [ritmo, setRitmo] = useState<Ritmo>("normal");
  const [ocupada, setOcupada] = useState(true);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let viva = true;
    api
      .memoria(sessionId)
      .then((memoria) => {
        if (!viva) return;
        const preferencias = comunicacion(memoria.data);
        setActiva(memoria.enabled);
        setConsiente(memoria.enabled);
        if (preferencias.treatment === "tu" || preferencias.treatment === "usted") setTrato(preferencias.treatment);
        if (["low", "normal", "high"].includes(String(preferencias.detail))) setDetalle(preferencias.detail as Detalle);
        if (["slow", "normal", "fast"].includes(String(preferencias.pace))) setRitmo(preferencias.pace as Ritmo);
      })
      .catch((e) => viva && setError(String(e)))
      .finally(() => viva && setOcupada(false));
    return () => {
      viva = false;
    };
  }, [sessionId]);

  async function guardar() {
    setOcupada(true);
    setError(null);
    setMensaje(null);
    try {
      const memoria = await api.guardarMemoria(sessionId, {
        communication: { treatment: trato, detail: detalle, pace: ritmo, language: "es" },
      });
      setActiva(memoria.enabled);
      setConsiente(memoria.enabled);
      setMensaje("Preferencias guardadas. Se aplicarán al empezar tu próxima conversación.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setOcupada(false);
    }
  }

  async function olvidar() {
    setOcupada(true);
    setError(null);
    setMensaje(null);
    try {
      await api.borrarMemoria(sessionId);
      setActiva(false);
      setConsiente(false);
      setMensaje("Hemos borrado tus preferencias personales. Tu expediente MiFID no se ha modificado.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setOcupada(false);
    }
  }

  return (
    <section className={s.tarjeta} aria-labelledby="memoria-titulo">
      <div className={s.cabecera}>
        <span className={s.icono} aria-hidden="true">↻</span>
        <div>
          <h2 id="memoria-titulo">Recordar cómo prefieres hablar</h2>
          <p className="pequena suave">Solo guardamos estas preferencias. No se usan para calcular tu perfil inversor.</p>
        </div>
      </div>

      <span className={`${s.estado} ${activa ? s.estadoActiva : ""}`}>
        {activa ? "Memoria personal activa" : "No estamos recordando preferencias"}
      </span>

      <fieldset className={s.campos} disabled={ocupada}>
        <label className={s.campo}>
          <span>Cómo dirigirse a ti</span>
          <select value={trato} onChange={(e) => setTrato(e.target.value as Trato)}>
            <option value="usted">De usted</option>
            <option value="tu">De tú</option>
          </select>
        </label>
        <label className={s.campo}>
          <span>Nivel de detalle</span>
          <select value={detalle} onChange={(e) => setDetalle(e.target.value as Detalle)}>
            <option value="low">Breve</option>
            <option value="normal">Normal</option>
            <option value="high">Con más contexto</option>
          </select>
        </label>
        <label className={s.campo}>
          <span>Ritmo</span>
          <select value={ritmo} onChange={(e) => setRitmo(e.target.value as Ritmo)}>
            <option value="slow">Pausado</option>
            <option value="normal">Normal</option>
            <option value="fast">Ágil</option>
          </select>
        </label>
      </fieldset>

      <label className={s.consentimiento}>
        <input type="checkbox" checked={consiente} onChange={(e) => setConsiente(e.target.checked)} />
        <span>Autorizo a guardar estas preferencias para futuras conversaciones. Puedo borrarlas cuando quiera.</span>
      </label>

      <div className={`${s.acciones} ${activa ? s.accionesConBorrado : ""}`}>
        <Boton onClick={guardar} disabled={ocupada || !consiente}>
          {ocupada ? "Guardando…" : "Guardar preferencias"}
        </Boton>
        {activa && (
          <Boton variante="texto" onClick={olvidar} disabled={ocupada}>
            Borrar memoria personal
          </Boton>
        )}
      </div>

      {mensaje && <p className={s.mensaje} role="status">{mensaje}</p>}
      {error && <p className={`${s.mensaje} ${s.error}`} role="alert">No hemos podido actualizar la memoria: {error}</p>}
    </section>
  );
}
