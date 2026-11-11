"use client";

import { useEffect, useState } from "react";
import { Aura, type EstadoAura } from "@/components/visual";
import s from "./portada.module.css";

const PREGUNTAS = [
  "¿Para qué quieres este dinero?",
  "¿Cuándo crees que lo vas a necesitar?",
  "Si tus ahorros bajaran un 20 %, ¿qué harías?",
  "¿Has invertido antes en fondos?",
  "¿Cuántos meses de gastos tienes guardados?",
];
const PASOS = ["Conversa", "Verifica", "Valida", "Entrega"];

/** El entrevistador de la portada: va lanzando preguntas de ejemplo y alterna entre hablar y escuchar. */
export function AuraPreguntas() {
  const [i, setI] = useState(0);
  const [estado, setEstado] = useState<EstadoAura>("habla");
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t1 = setTimeout(() => setEstado("escucha"), 2600);
    const t2 = setTimeout(() => setEstado("anotado"), 4300);
    const t3 = setTimeout(() => {
      setI((n) => (n + 1) % PREGUNTAS.length);
      setEstado("habla");
    }, 5200);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, [i]);

  return (
    <div className={s.escena}>
      <div className={s.auraFlota}>
        <Aura estado={estado} tam={320} />
      </div>
      <p key={i} className={s.preguntaEjemplo} aria-live="off">
        {PREGUNTAS[i]}
      </p>
      <ol className={`${s.pasos} mono`} aria-label="Cómo trabaja idóneo">
        {PASOS.map((p, n) => (
          <li key={p} className={n === 0 ? s.pasoActivo : ""}>
            <span>{String(n + 1).padStart(2, "0")}</span> {p}
          </li>
        ))}
      </ol>
    </div>
  );
}
