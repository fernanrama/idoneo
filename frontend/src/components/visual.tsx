"use client";

import Link from "next/link";
import { Logo } from "./Logo";
import { useCallback, useRef } from "react";
import type { EstadoBloque } from "@/lib/bloques";
import { Esfera3D, type AjustesEsfera, type Paleta } from "./Esfera3D";
import s from "./visual.module.css";

/**
 * Ambiente oscuro con brillos que derivan y un foco de luz que sigue al ratón.
 * El ratón solo cambia variables CSS (--mx, --my, --px, --py): no provoca renders de React.
 */
export function Noche({ children, className = "", style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  const ref = useRef<HTMLDivElement>(null);
  const marco = useRef(0);
  const mover = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el || e.pointerType === "touch") return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    cancelAnimationFrame(marco.current);
    marco.current = requestAnimationFrame(() => {
      el.style.setProperty("--mx", `${x}px`);
      el.style.setProperty("--my", `${y}px`);
      el.style.setProperty("--px", ((x / r.width) * 2 - 1).toFixed(3));
      el.style.setProperty("--py", ((y / r.height) * 2 - 1).toFixed(3));
    });
  }, []);
  return (
    <div ref={ref} onPointerMove={mover} className={`tema-noche ${s.noche} ${className}`} style={style}>
      <div className={s.foco} aria-hidden="true" />
      <div className={`${s.brillo} ${s.brillo1}`} aria-hidden="true" />
      <div className={`${s.brillo} ${s.brillo2}`} aria-hidden="true" />
      <div className={`${s.brillo} ${s.brillo3}`} aria-hidden="true" />
      {children}
    </div>
  );
}

export type EstadoAura = "reposo" | "habla" | "escucha" | "anotado" | "pausa" | "pensando";

const AURA: Paleta = ["#1f3bff", "#8a5cff", "#ff7fd1"];
const AJUSTES: Record<EstadoAura, AjustesEsfera> = {
  reposo: { paleta: AURA, velocidad: 0.55, energia: 0.55 },
  habla: { paleta: AURA, velocidad: 1.9, energia: 1.05, pulso: 1 },
  escucha: { paleta: ["#1a2fd0", "#6f6bff", "#8fd6ff"], velocidad: 0.4, energia: 0.35 },
  anotado: { paleta: ["#0c7f8f", "#38d6a4", "#d4ffe9"], velocidad: 1.1, energia: 0.7 },
  pausa: { paleta: AURA, velocidad: 0.06, energia: 0.3, color: 0.12 },
  pensando: { paleta: AURA, velocidad: 1.4, energia: 0.9 },
};

/** El entrevistador: una esfera de plasma en 3D que respira en reposo, se agita al hablar, se calma al escuchar y se vuelve verde al anotar. */
export function Aura({ estado = "reposo", tam = 360 }: { estado?: EstadoAura; tam?: number }) {
  return (
    <div className={`${s.auraCaja} ${s[estado] ?? ""}`} style={{ "--tam": `${tam}px` } as React.CSSProperties} aria-hidden="true">
      <div className={s.anillo2} />
      <div className={s.anillo} />
      <div className={`${s.capa} ${s.c1}`} />
      <div className={`${s.capa} ${s.c2}`} />
      <div className={`${s.capa} ${s.c3}`} />
      <div className={s.voz} />
      <div className={`${s.voz} ${s.voz2}`} />
      <div className={s.nucleo}>
        <div className={s.respaldo} />
        <Esfera3D className={s.esfera} {...AJUSTES[estado]} />
      </div>
    </div>
  );
}

export function Ondas() {
  return (
    <span className={s.ondas} aria-hidden="true">
      {Array.from({ length: 7 }, (_, i) => (
        <span key={i} />
      ))}
    </span>
  );
}

export function Anotado() {
  return (
    <span className={`${s.anotadoChip} mono`} style={{ fontSize: 12 }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20 6 9 17l-5-5" />
      </svg>
      Anotado
    </span>
  );
}

export function MarcaNoche({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className={s.marca} aria-label="idóneo, inicio">
      <Logo variante="oscuro" alto={28} decorativo />
    </Link>
  );
}

export function BloquesNoche({ bloques }: { bloques: { id: string; nombre: string; estado: EstadoBloque }[] }) {
  const hechos = bloques.filter((b) => b.estado === "completo").length;
  return (
    <div
      className={s.bloques}
      role="progressbar"
      aria-label="Progreso de la entrevista"
      aria-valuemin={0}
      aria-valuemax={bloques.length}
      aria-valuenow={hechos}
    >
      {bloques.map((b) => (
        <span key={b.id} className={`${s.bloque} ${s[`bloque_${b.estado}`] ?? ""} mono`}>
          <span className={s.bloquePunto} aria-hidden="true" />
          {b.nombre}
        </span>
      ))}
    </div>
  );
}

type PropsBoton = React.ButtonHTMLAttributes<HTMLButtonElement> & { variante?: "luz" | "vidrio"; redondo?: boolean };
export function BotonNoche({ variante = "luz", redondo = false, className = "", ...props }: PropsBoton) {
  const cls = variante === "luz" ? s.botonLuz : `vidrio ${s.botonVidrio} ${redondo ? s.botonRedondo : ""}`;
  return <button className={`${cls} ${className}`} {...props} />;
}

export const clasesBoton = { luz: s.botonLuz, vidrio: `vidrio ${s.botonVidrio}` };

export const Icono = {
  micro: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </svg>
  ),
  teclado: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10" />
    </svg>
  ),
  cerrar: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  ),
  enviar: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  ),
  aviso: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 3 2 21h20L12 3z" />
      <path d="M12 10v5M12 18h.01" />
    </svg>
  ),
  pausa: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="6" y="5" width="4" height="14" rx="1.2" />
      <rect x="14" y="5" width="4" height="14" rx="1.2" />
    </svg>
  ),
  saltar: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M5 5.5v13l9-6.5-9-6.5z" />
      <rect x="16" y="5" width="3" height="14" rx="1" />
    </svg>
  ),
  sonido: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12" />
    </svg>
  ),
  silencio: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M17 9l5 6M22 9l-5 6" />
    </svg>
  ),
  check: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  ),
  play: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M7 4v16l13-8z" />
    </svg>
  ),
};
