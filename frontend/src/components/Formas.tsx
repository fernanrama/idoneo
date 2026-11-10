"use client";

import s from "./formas.module.css";

/**
 * Cinta de cristal para la vista de la entidad: tres bandas con degradado que ondulan solas
 * (animación SVG nativa, sin imágenes). Puramente decorativa.
 */
export function Cinta({ className = "" }: { className?: string }) {
  const bandas = [
    { a: "M20 230 C 90 80, 190 320, 320 120", b: "M20 200 C 110 120, 170 300, 320 150", w: 46, o: 0.9, g: "c1", d: "7s" },
    { a: "M30 260 C 120 140, 200 330, 330 170", b: "M30 280 C 100 170, 220 300, 330 140", w: 30, o: 0.7, g: "c2", d: "9s" },
    { a: "M10 190 C 100 40, 170 260, 310 70", b: "M10 170 C 80 70, 200 240, 310 100", w: 18, o: 0.55, g: "c3", d: "11s" },
  ];
  return (
    <svg className={`${s.cinta} ${className}`} viewBox="0 0 340 340" aria-hidden="true">
      <defs>
        <linearGradient id="c1" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f4a6dc" />
          <stop offset="0.5" stopColor="#a78bfa" />
          <stop offset="1" stopColor="#7cc4ff" />
        </linearGradient>
        <linearGradient id="c2" x1="1" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c2338f" />
          <stop offset="1" stopColor="#6b4ef0" />
        </linearGradient>
        <linearGradient id="c3" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.9" />
          <stop offset="1" stopColor="#b9a6ff" />
        </linearGradient>
        <filter id="suave">
          <feGaussianBlur stdDeviation="1.2" />
        </filter>
      </defs>
      {bandas.map((b) => (
        <path key={b.g} d={b.a} fill="none" stroke={`url(#${b.g})`} strokeWidth={b.w} strokeLinecap="round" opacity={b.o} filter="url(#suave)">
          <animate attributeName="d" dur={b.d} repeatCount="indefinite" values={`${b.a};${b.b};${b.a}`} calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" />
        </path>
      ))}
      <path d="M40 215 C 110 90, 190 300, 312 128" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" opacity="0.7">
        <animate attributeName="d" dur="7s" repeatCount="indefinite" values="M40 215 C 110 90, 190 300, 312 128;M40 190 C 120 130, 170 285, 312 155;M40 215 C 110 90, 190 300, 312 128" calcMode="spline" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" />
      </path>
    </svg>
  );
}

/**
 * Esfera de cristal con los rasgos del perfil orbitando alrededor: lo que hemos entendido, de un vistazo.
 */
export function OrbePerfil({ rasgos }: { rasgos: string[] }) {
  return (
    <div className={s.orbeCaja} aria-hidden="true">
      <div className={s.orbeSombra} />
      <div className={s.orbe}>
        <div className={s.orbeBrillo} />
        <div className={s.orbeLiquido} />
      </div>
      {rasgos.slice(0, 4).map((r, i) => (
        <span key={r} className={`${s.rasgo} ${s[`r${i}`]}`}>
          <i />
          {r}
        </span>
      ))}
    </div>
  );
}
