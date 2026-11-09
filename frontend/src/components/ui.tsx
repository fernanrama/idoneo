"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { EstadoBloque } from "@/lib/bloques";
import type { Alerta, Turno } from "@/lib/tipos";
import s from "./ui.module.css";

export function Marco({ children, ancho = false }: { children: React.ReactNode; ancho?: boolean }) {
  return <div className={`${s.marco} ${ancho ? s.marcoAncho : ""}`}>{children}</div>;
}

export function Cabecera({ titulo, volver = true }: { titulo: string; volver?: boolean }) {
  const router = useRouter();
  return (
    <header className={s.cabecera}>
      {volver && (
        <button className={s.volver} onClick={() => router.back()} aria-label="Volver">
          ‹
        </button>
      )}
      <h1>{titulo}</h1>
    </header>
  );
}

export function Contenido({ children }: { children: React.ReactNode }) {
  return <main className={s.contenido}>{children}</main>;
}

export function Pie({ children }: { children: React.ReactNode }) {
  return <footer className={s.pie}>{children}</footer>;
}

type VarianteBoton = "primario" | "secundario" | "texto";
export function Boton({
  variante = "primario",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variante?: VarianteBoton }) {
  return <button className={`${s.boton} ${s[variante]} ${className}`} {...props} />;
}

export function Tarjeta({ children, destacada = false }: { children: React.ReactNode; destacada?: boolean }) {
  return <section className={`${s.tarjeta} ${destacada ? s.tarjetaDestacada : ""}`}>{children}</section>;
}

export function Chip({ children, tipo }: { children: React.ReactNode; tipo?: string }) {
  return <span className={`${s.chip} ${tipo ? s[`chip_${tipo}`] ?? "" : ""}`}>{children}</span>;
}

export function BarraBloques({ bloques }: { bloques: { id: string; nombre: string; estado: EstadoBloque }[] }) {
  const hechos = bloques.filter((b) => b.estado === "completo").length;
  const actual = bloques.find((b) => b.estado === "en_curso");
  return (
    <div>
      <div className={s.bloques} role="progressbar" aria-label="Progreso de la entrevista" aria-valuemin={0} aria-valuemax={bloques.length} aria-valuenow={hechos}>
        {bloques.map((b) => (
          <div key={b.id} className={`${s.bloque} ${s[`bloque_${b.estado}`] ?? ""}`} title={b.nombre} />
        ))}
      </div>
      <div className={s.bloquesLeyenda}>
        <span>{actual ? actual.nombre : hechos === bloques.length ? "Perfil completo" : ""}</span>
        <span>
          {hechos}/{bloques.length}
        </span>
      </div>
    </div>
  );
}

export function Subtitulos({ turnos }: { turnos: Turno[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [turnos.length]);
  return (
    <div ref={ref} className={s.subtitulos} role="log" aria-live="polite" aria-label="Subtítulos de la conversación">
      {turnos.map((t, i) => (
        <p key={i} className={`${s.burbuja} ${s[`burbuja_${t.speaker}`]}`}>
          <span className="oculto-visual">{t.speaker === "agent" ? "Asistente: " : "Tú: "}</span>
          {t.text}
        </p>
      ))}
    </div>
  );
}

export function BotonMicro({ activo, onClick, etiqueta }: { activo: boolean; onClick: () => void; etiqueta: string }) {
  return (
    <button className={`${s.micro} ${activo ? s.microActivo : ""}`} onClick={onClick} aria-label={etiqueta} aria-pressed={activo}>
      {activo ? "■" : "🎙"}
    </button>
  );
}

const TITULO_FLAG: Record<string, string> = {
  declared_vs_demonstrated: "Declarado ≠ demostrado",
  inconsistent: "Datos incoherentes",
  low_confidence: "Confianza baja: repreguntar",
  needs_advisor: "Requiere revisión humana",
};

export function AlertaTarjeta({ alerta, paraCliente = false }: { alerta: Alerta; paraCliente?: boolean }) {
  const cita = alerta.evidence[0]?.quote;
  return (
    <div className={s.alerta} role="status">
      <strong>{paraCliente ? "Algo que conviene aclarar" : TITULO_FLAG[alerta.flag]}</strong>
      <p style={{ margin: "4px 0 0" }}>{alerta.message}</p>
      {cita && <p className={s.cita}>«{cita}»</p>}
    </div>
  );
}

export function EntradaTexto({ onEnviar, deshabilitado }: { onEnviar: (t: string) => void; deshabilitado?: boolean }) {
  const [texto, setTexto] = useState("");
  return (
    <form
      className={s.entradaTexto}
      onSubmit={(e) => {
        e.preventDefault();
        if (texto.trim()) onEnviar(texto.trim());
        setTexto("");
      }}
    >
      <label className="oculto-visual" htmlFor="respuesta">
        Escribe tu respuesta
      </label>
      <input id="respuesta" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="O escribe tu respuesta…" disabled={deshabilitado} />
      <Boton type="submit" variante="secundario" disabled={deshabilitado || !texto.trim()}>
        Enviar
      </Boton>
    </form>
  );
}
