/* eslint-disable @next/next/no-img-element -- SVG de marca estático: no necesita el optimizador de imágenes. */

/** Lema oficial de la marca (docs/marca/README.md). */
export const LEMA = "Del cuestionario a la conversación. Perfiles vivos que cumplen la norma.";

const FICHEROS = {
  claro: "/marca/idoneo-logo-sobre-claro.svg",
  oscuro: "/marca/idoneo-logo-sobre-oscuro.svg",
  icono: "/marca/idoneo-icono-degradado.svg",
} as const;

// Proporción del logotipo (viewBox 3740 × 1187). El icono es cuadrado.
const PROPORCION = { claro: 3740 / 1187, oscuro: 3740 / 1187, icono: 1 } as const;

/**
 * Logotipo de idóneo. «claro» para fondos claros, «oscuro» para fondos noche.
 * Por debajo de 80 px de ancho la guía pide el icono: con `alto` < 26 usa `variante="icono"`.
 */
export function Logo({ variante, alto = 28, decorativo = false }: { variante: keyof typeof FICHEROS; alto?: number; decorativo?: boolean }) {
  return (
    <img
      src={FICHEROS[variante]}
      alt={decorativo ? "" : "idóneo"}
      width={Math.round(alto * PROPORCION[variante])}
      height={alto}
      style={{ display: "block", height: alto, width: "auto", flexShrink: 0 }}
    />
  );
}
