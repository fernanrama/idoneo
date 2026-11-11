"use client";

import { useEffect, useRef, useState } from "react";
import { Aura, Icono } from "@/components/visual";
import s from "./historia.module.css";

const PASOS = [
  {
    kicker: "01 · Conversa",
    titulo: "Una pregunta cada vez, con sus palabras.",
    texto:
      "El cliente habla o escribe. El asistente pregunta por su objetivo, su situación, lo que conoce y cómo reaccionaría ante una caída, y repregunta cuando algo no queda claro.",
  },
  {
    kicker: "02 · Anota",
    titulo: "Cada dato, con la frase que lo justifica.",
    texto:
      "Lo que dice se convierte en datos del perfil MiFID. Cada uno guarda la cita exacta, el momento de la conversación y si es declarado, demostrado, calculado o del asesor.",
  },
  {
    kicker: "03 · Contrasta",
    titulo: "Lo declarado frente a lo demostrado.",
    texto:
      "Si el cliente dice conocer un producto pero su respuesta demuestra lo contrario, salta un aviso. Manda lo demostrado y el aviso queda abierto para la entidad.",
  },
  {
    kicker: "04 · Calcula",
    titulo: "Los números salen de reglas fijas, no del modelo.",
    texto:
      "Tolerancia, capacidad de pérdida y plazo dan cada uno un perfil; manda el más prudente. El resultado es siempre el mismo para las mismas respuestas y se puede auditar.",
  },
  {
    kicker: "05 · Valida y entrega",
    titulo: "Una persona firma. El agente de la entidad lo usa.",
    texto:
      "El perfil queda versionado. Hasta que alguien de la entidad lo valida, su agente no puede usarlo; después lo consulta por MCP para buscar productos dentro de esos límites. Si algo cambia, se pregunta solo eso.",
  },
];

/**
 * «Cómo funciona» contado con el scroll: en escritorio el escenario de la izquierda se queda fijo y
 * cambia de escena según el paso que se lee; en móvil cada paso lleva su escena debajo.
 */
export function Historia() {
  const [activo, setActivo] = useState(0);
  const refs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const io = new IntersectionObserver(
      (entradas) => {
        for (const e of entradas) if (e.isIntersecting) setActivo(Number((e.target as HTMLElement).dataset.i));
      },
      { rootMargin: "-45% 0px -45% 0px" },
    );
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className={s.historia}>
      <div className={s.escenario} aria-hidden="true">
        <div className={`${s.marco} vidrio`}>
          <div className={s.progreso}>
            {PASOS.map((p, i) => (
              <span key={p.kicker} className={i <= activo ? s.lleno : ""} />
            ))}
          </div>
          {PASOS.map((p, i) => (
            <div key={p.kicker} className={`${s.escena} ${i === activo ? s.escenaActiva : ""}`}>
              <Escena i={i} activa={i === activo} />
            </div>
          ))}
        </div>
      </div>
      <ol className={s.pasos}>
        {PASOS.map((p, i) => (
          <li
            key={p.kicker}
            data-i={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className={`${s.paso} ${i === activo ? s.pasoActivo : ""}`}
          >
            <span className={`${s.kicker} mono`}>{p.kicker}</span>
            <h3>{p.titulo}</h3>
            <p>{p.texto}</p>
            <div className={`${s.escenaMovil} vidrio`} aria-hidden="true">
              <Escena i={i} activa />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Escena({ i, activa }: { i: number; activa: boolean }) {
  if (i === 0)
    return (
      <div className={s.e0}>
        <Aura estado={activa ? "habla" : "reposo"} tam={170} />
        <p className={s.preguntaMini}>Si sus ahorros bajaran un 20 % en unos meses, ¿qué haría?</p>
        <p className={s.respuestaMini}>
          <span className="mono">Cliente</span>«Si baja un veinte por ciento, lo saco todo.»
        </p>
      </div>
    );
  if (i === 1)
    return (
      <div className={s.e1}>
        {[
          { e: "Ante una caída del 20 %", v: "Vendería todo", c: "Si baja un veinte por ciento, lo saco todo.", f: "Demostrado", k: s.chipVerde, n: 90 },
          { e: "Plazo", v: "10 años", c: "Para los próximos diez años, más o menos.", f: "Declarado", k: s.chipAzul, n: 70 },
          { e: "Ahorro líquido", v: "80.000 €", c: "Tengo ochenta mil en depósitos.", f: "Declarado", k: s.chipAzul, n: 90 },
        ].map((d, j) => (
          <div key={d.e} className={s.dato} style={{ animationDelay: `${0.15 + j * 0.18}s` }}>
            <div className={s.datoCab}>
              <span>{d.e}</span>
              <span className={`${s.chip} ${d.k}`}>{d.f}</span>
            </div>
            <strong>{d.v}</strong>
            <em>«{d.c}»</em>
            <div className={s.barra}>
              <span style={{ width: `${d.n}%` }} />
            </div>
          </div>
        ))}
      </div>
    );
  if (i === 2)
    return (
      <div className={s.e2}>
        <div className={s.test}>
          <span className="mono">Test del banco</span>
          <label>
            <span className={s.casilla}>{Icono.check}</span>Conozco bien los fondos de renta variable
          </label>
        </div>
        <div className={s.frente}>frente a</div>
        <div className={s.dicho}>
          <span className="mono">En la conversación</span>
          «Eso no puede pasar, el fondo es del banco.»
        </div>
        <div className={s.aviso}>
          {Icono.aviso}
          <div>
            <strong>Declarado ≠ demostrado</strong>
            Cree que un fondo de su banco no puede perder valor.
          </div>
        </div>
      </div>
    );
  if (i === 3)
    return (
      <div className={s.e3}>
        {[
          ["Tolerancia por escenarios (1 de 5)", "Conservador"],
          ["Capacidad de pérdida: 74.600 € de 80.000 €", "Muy agresivo"],
          ["Plazo de 10 años", "Agresivo"],
        ].map(([a, b], j) => (
          <div key={a} className={s.regla} style={{ animationDelay: `${0.1 + j * 0.2}s` }}>
            <span>{a}</span>
            <span className="mono">→ {b}</span>
          </div>
        ))}
        <div className={s.resultado} style={{ animationDelay: "0.8s" }}>
          <span className="mono">Manda el más prudente</span>
          <strong>Conservador · riesgo hasta 3 de 7</strong>
          <div className={s.sri}>
            {Array.from({ length: 7 }, (_, k) => (
              <span key={k} className={k < 3 ? s.sriLleno : ""} style={{ animationDelay: `${1 + k * 0.08}s` }} />
            ))}
          </div>
        </div>
      </div>
    );
  return (
    <div className={s.e4}>
      <div className={s.sello}>
        {Icono.check} Validado por la entidad · v1
      </div>
      <pre className={s.codigo}>
        <em>{"// el agente de la entidad pregunta por MCP"}</em>
        {"\nget_investment_constraints(\"carmen-68\")\n\n{\n  "}
        <b>&quot;usable&quot;</b>
        {": true,\n  "}
        <b>&quot;funds_query&quot;</b>
        {': { "max_risk": 3, "currency": "EUR" },\n  '}
        <b>&quot;appropriateness&quot;</b>
        {': {\n    "equity_funds": "not_appropriate"\n  }\n}'}
      </pre>
    </div>
  );
}
