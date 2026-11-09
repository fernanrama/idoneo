"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { EstadoBloque } from "@/lib/bloques";
import type { Alerta, Turno } from "@/lib/tipos";
import s from "./ui.module.css";

/** `asesor` cambia a la piel de la entidad (estilo GPTadvisor); por defecto, piel del cliente (estilo MyInvestor). */
export function Marco({ children, ancho = false, asesor = false }: { children: React.ReactNode; ancho?: boolean; asesor?: boolean }) {
  return (
    <div className={`${s.marco} ${ancho ? s.marcoAncho : ""} ${asesor ? `tema-asesor ${s.asesor}` : ""}`}>{children}</div>
  );
}

/** Nombre del producto (texto, no logo) y la marca de prototipo. */
export function Marca() {
  return (
    <span className="fila">
      <span className={s.marca}>
        idóneo<span>.</span>
      </span>
      <span className={s.prototipo}>Prototipo</span>
    </span>
  );
}

export function Hero({ children }: { children: React.ReactNode }) {
  return <div className={s.hero}>{children}</div>;
}

export function HeroAsesor({ children }: { children: React.ReactNode }) {
  return <div className={s.heroAsesor}>{children}</div>;
}

type ColorEtiqueta = "rosa" | "violeta" | "azul" | "verde";
export function Etiqueta({ children, color, punto = false }: { children: React.ReactNode; color?: ColorEtiqueta; punto?: boolean }) {
  return (
    <span className={`${s.etiqueta} ${color ? s[`etiqueta_${color}`] : ""} ${punto ? s.etiquetaPunto : ""}`}>{children}</span>
  );
}

const PASOS = ["Tú", "Entrevista", "Tu perfil", "Productos"];
/** Pasos del onboarding, con el mismo patrón de círculos del test de MyInvestor. `actual` empieza en 0. */
export function Pasos({ actual }: { actual: number }) {
  const iconos = ["👤", "🎙", "◎", "▤"];
  return (
    <ol className={s.pasos} aria-label="Pasos">
      {PASOS.map((p, i) => {
        const estado = i < actual ? "hecho" : i === actual ? "actual" : "pendiente";
        return (
          <li key={p} className={`${s.paso} ${s[`paso_${estado}`] ?? ""}`} aria-current={i === actual ? "step" : undefined}>
            <span className={s.pasoCirculo} aria-hidden="true">
              {i < actual ? "✓" : iconos[i]}
            </span>
            {p}
          </li>
        );
      })}
    </ol>
  );
}

function IconoCheck() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M21 11.1V12a9 9 0 1 1-5.3-8.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M21 4.5 12 13.5l-3-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ListaCheck({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className={s.checks}>
      {items.map((it, i) => (
        <li key={i}>
          <IconoCheck />
          <span>{it}</span>
        </li>
      ))}
    </ul>
  );
}

/** Recuadro de riesgo con el formato regulatorio que usa la banca española («3/7 · indicativo del riesgo»). */
export function IndicadorRiesgo({ nivel, maximo = 7 }: { nivel: number | null | undefined; maximo?: number }) {
  return (
    <div className={s.riesgo} role="img" aria-label={`Riesgo máximo ${nivel ?? "sin definir"} sobre ${maximo}`}>
      <strong>
        {nivel ?? "—"}/{maximo}
      </strong>
      <div className={s.riesgoEscala} aria-hidden="true">
        {Array.from({ length: maximo }, (_, i) => (
          <span key={i} className={nivel != null && i < nivel ? s.riesgoLleno : ""} />
        ))}
      </div>
      <p>
        Nivel máximo de riesgo de los productos que te mostraremos, siendo 1/{maximo} el menor riesgo y {maximo}/{maximo} el
        mayor.
      </p>
    </div>
  );
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

/** Con `titulo`, la tarjeta lleva cabecera con línea inferior (patrón de las tarjetas de GPTadvisor). */
export function Tarjeta({
  children,
  destacada = false,
  titulo,
  extra,
}: {
  children: React.ReactNode;
  destacada?: boolean;
  titulo?: React.ReactNode;
  extra?: React.ReactNode;
}) {
  if (titulo == null) return <section className={`${s.tarjeta} ${destacada ? s.tarjetaDestacada : ""}`}>{children}</section>;
  return (
    <section className={`${s.tarjeta} ${s.tarjetaConCabecera}`}>
      <div className={s.tarjetaCabecera}>
        <h2>{titulo}</h2>
        {extra}
      </div>
      <div className={s.tarjetaCuerpo}>{children}</div>
    </section>
  );
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
