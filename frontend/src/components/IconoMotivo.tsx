/** Iconos propios (SVG) de los motivos de «Ha cambiado algo». Se dibujan al aparecer y al elegirlos. */
const TRAZOS: Record<string, React.ReactNode> = {
  sueldo: (
    <>
      <rect x="6" y="14" width="36" height="22" rx="5" />
      <circle cx="24" cy="25" r="5" />
      <path d="M24 4v6m-4-3 4-3 4 3" />
    </>
  ),
  gasto: (
    <>
      <path d="M8 22 24 9l16 13" />
      <path d="M12 20v18h24V20" />
      <path d="M20 38V28h8v10" />
      <path d="M34 6l4 4m0-4-4 4" />
    </>
  ),
  extra: (
    <>
      <rect x="8" y="18" width="32" height="20" rx="3" />
      <path d="M8 24h32M24 18v20" />
      <path d="M24 18c-4-8-12-6-10-1s10 1 10 1c0 0 8 4 10-1s-6-7-10 1" />
    </>
  ),
  idea: (
    <>
      <path d="M17 30c-3-2.5-5-6-5-10a12 12 0 0 1 24 0c0 4-2 7.5-5 10v4H17z" />
      <path d="M19 40h10" />
      <path d="M24 14v6l3 3" />
    </>
  ),
  casa: (
    <>
      <path d="M6 22 24 8l18 14" />
      <path d="M11 19v19h26V19" />
      <circle cx="24" cy="28" r="4" />
      <path d="M24 32v6" />
    </>
  ),
  trabajo: (
    <>
      <rect x="6" y="14" width="36" height="24" rx="4" />
      <path d="M18 14v-4h12v4" />
      <path d="M6 24h36" />
      <path d="M30 30l6 6m0-6-6 6" />
    </>
  ),
  familia: (
    <>
      <circle cx="16" cy="13" r="5" />
      <circle cx="32" cy="17" r="4" />
      <path d="M7 38v-6a9 9 0 0 1 18 0v6" />
      <path d="M26 38v-4a6 6 0 0 1 12 0v4" />
    </>
  ),
  jubilacion: (
    <>
      <circle cx="24" cy="24" r="16" />
      <path d="M24 14v10l7 5" />
      <path d="M10 6l-4 4m36-4 4 4" />
    </>
  ),
};

export function IconoMotivo({ icono, className }: { icono: string; className?: string }) {
  return (
    <svg viewBox="0 0 48 48" width="44" height="44" fill="none" stroke="currentColor" strokeWidth="2.4"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {TRAZOS[icono] ?? TRAZOS.idea}
    </svg>
  );
}
