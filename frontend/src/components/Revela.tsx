"use client";

import { useEffect, useRef } from "react";

/**
 * Aparece suavemente cuando entra en pantalla al hacer scroll. Solo añade la clase `visto`:
 * el movimiento está en `tema/visual.css` y se apaga con «reducir movimiento».
 */
export function Revela({
  children,
  como = "div",
  retraso = 0,
  variante,
  className = "",
  style,
  id,
}: {
  children: React.ReactNode;
  como?: "div" | "section" | "article" | "li";
  retraso?: number;
  variante?: "izq" | "zoom";
  className?: string;
  style?: React.CSSProperties;
  id?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) {
      el.classList.add("visto");
      return;
    }
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          el.classList.add("visto");
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const Tag = como as "div";
  return (
    <Tag
      ref={ref as React.RefObject<HTMLDivElement>}
      id={id}
      className={`revela ${variante ? `revela-${variante}` : ""} ${className}`}
      style={{ ...style, "--retraso": `${retraso}s` } as React.CSSProperties}
    >
      {children}
    </Tag>
  );
}
