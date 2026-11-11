/* eslint-disable @next/next/no-img-element -- SVG de marca estático: no necesita el optimizador de imágenes. */

const FICHEROS = {
  claro: "/marca/powered-by-idoneo-claro.svg", // tinta oscura: para fondos claros
  oscuro: "/marca/powered-by-idoneo-oscuro.svg", // tinta clara: para fondos oscuros
  gris: "/marca/powered-by-idoneo-gris.svg",
} as const;

// Proporción del sello (viewBox 6497 × 1187).
const PROPORCION = 6497.2 / 1187;

/** Sello «Powered by idóneo»: la firma de idóneo al pie de un módulo dentro de la app de la entidad. */
export function SelloPowered({ fondo = "claro", alto = 16 }: { fondo?: keyof typeof FICHEROS; alto?: number }) {
  return (
    <img
      src={FICHEROS[fondo]}
      alt="Powered by idóneo"
      width={Math.round(alto * PROPORCION)}
      height={alto}
      style={{ display: "block", height: alto, width: "auto", flexShrink: 0 }}
    />
  );
}
