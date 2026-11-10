"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { OrbePerfil } from "@/components/Formas";
import { nombrePerfil } from "@/components/PanelVivo";
import { Revela } from "@/components/Revela";
import { Icono } from "@/components/visual";
import { FAMILIAS, mostrarValor } from "@/lib/bloques";
import { useOnboarding } from "@/lib/onboarding";
import type { Alerta, Fact, Perfil } from "@/lib/tipos";
import { usePerfil } from "@/lib/usePerfil";
import { BarraCliente } from "@/components/BarraCliente";
import s from "@/components/cliente.module.css";

const QUE_SIGNIFICA: Record<string, string> = {
  CONSERVADOR: "Prefieres no ver caer tus ahorros, aunque eso suponga ganar menos.",
  MODERADO: "Aceptas algún altibajo a cambio de una rentabilidad algo mayor.",
  DINAMICO: "Toleras caídas temporales si a largo plazo esperas ganar más.",
  AGRESIVO: "Buscas crecer y asumes caídas fuertes por el camino.",
  MUY_AGRESIVO: "Priorizas el crecimiento y aceptas mucha volatilidad.",
};

const euros = (v: unknown) =>
  typeof v === "number" ? `${v.toLocaleString("es-ES", { maximumFractionDigits: 0 })} €` : mostrarValor(v);
const colchon = (v: unknown) => {
  if (typeof v !== "number") return mostrarValor(v);
  if (v >= 24) return `Más de ${Math.floor(v / 12)} años de gastos fijos`;
  return `${Math.round(v)} meses de gastos fijos`;
};

type Fila = { ruta: string; titulo: string; valor: (f: Fact) => string; nota?: string };
const FILAS: Fila[] = [
  { ruta: "objectives.o1.goal", titulo: "Tu objetivo", valor: (f) => mayus(mostrarValor(f.value)) },
  { ruta: "objectives.o1.horizon_years", titulo: "Cuándo lo necesitarás", valor: (f) => `En unos ${mostrarValor(f.value)} años` },
  { ruta: "financial.liquid_savings_eur", titulo: "Ahorro disponible", valor: (f) => euros(f.value) },
  {
    ruta: "financial.emergency_fund_months",
    titulo: "Tus ahorros cubren",
    valor: (f) => colchon(f.value),
    nota: "Conviene conservar siempre al menos seis meses por si surge un imprevisto.",
  },
  { ruta: "risk_tolerance.past_behaviour", titulo: "Si tus ahorros bajan", valor: (f) => mayus(mostrarValor(f.value)) },
  { ruta: "sustainability.preference", titulo: "Inversión sostenible", valor: (f) => (f.value === "none" ? "No es una prioridad para ti" : mayus(mostrarValor(f.value))) },
];
function mayus(t: string) {
  return t ? t[0].toUpperCase() + t.slice(1) : t;
}

// Resumen para el cliente, en lenguaje claro: qué hemos entendido, qué significa y qué pasa ahora.
export default function MiPerfil() {
  const { clientId } = useOnboarding();
  const { perfil, error } = usePerfil(clientId);
  const ref = useRef<HTMLDivElement>(null);

  const mover = (e: React.PointerEvent) => {
    const el = ref.current;
    if (!el || e.pointerType === "touch") return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--px", (((e.clientX - r.left) / r.width) * 2 - 1).toFixed(3));
    el.style.setProperty("--py", (((e.clientY - r.top) / r.height) * 2 - 1).toFixed(3));
  };

  return (
    <div ref={ref} className={s.raiz} onPointerMove={mover}>
      <BarraCliente paso={2} />

      <main className={s.caja}>
        {error && (
          <p role="alert" className={s.error}>
            No hemos podido cargar tu perfil. Inténtalo de nuevo en un momento.
          </p>
        )}
        {!perfil && !error && <div className={s.cargando} aria-label="Cargando tu perfil" />}
        {perfil && <Contenido perfil={perfil} />}
      </main>
    </div>
  );
}

function Contenido({ perfil }: { perfil: Perfil }) {
  const su = perfil.assessments.suitability;
  const revisado = perfil.status === "active";
  const alertas = perfil.alerts.filter((a) => a.status === "open");
  const noConvenientes = Object.entries(perfil.assessments.appropriateness)
    .filter(([, x]) => x === "not_appropriate")
    .map(([f]) => FAMILIAS[f] ?? f);
  const filas = FILAS.filter((f) => perfil.mifid[f.ruta]?.value != null);
  const horizonte = perfil.mifid["objectives.o1.horizon_years"]?.value as number | null | undefined;

  return (
    <>
      <section className={s.hero}>
        <div className={s.heroTexto}>
          <span className={`${s.estado} ${revisado ? s.estadoOk : ""}`}>
            <i aria-hidden="true" />
            {revisado ? "Revisado por el banco" : "Pendiente de revisión"}
          </span>
          <h1>
            Esto es lo que <span className={s.grad}>hemos entendido</span>
          </h1>
          <p>Lo hemos resumido a partir de lo que nos has contado. Toca cada punto para ver la frase exacta en la que nos basamos. Si algo no encaja, díselo a tu asesor en la revisión.</p>
        </div>
        <div className={s.capsula}>
          <OrbePerfil
            rasgos={[
              `Perfil ${nombrePerfil(su.risk_profile).toLowerCase()}`,
              `Riesgo hasta ${su.max_sri ?? "—"} de 7`,
              horizonte ? `Plazo de ${horizonte} años` : "Plazo por definir",
              revisado ? "Revisado por el banco" : "En revisión",
            ]}
          />
        </div>
      </section>

      <div className={s.rejilla}>
        <Revela como="section" className={`${s.tarjeta} ${s.medidor}`}>
          <h2 id="t-riesgo">Qué significa para ti</h2>
          <Medidor nivel={su.max_sri} />
          <p className={s.perfilNombre}>
            Perfil <strong>{nombrePerfil(su.risk_profile)}</strong>
          </p>
          <p className={s.suave}>{su.risk_profile ? QUE_SIGNIFICA[su.risk_profile] : "Aún nos faltan algunos datos."}</p>
          <p>
            Te mostraremos productos con un nivel de riesgo de <strong>{su.max_sri ?? "—"} sobre 7</strong> como máximo.
          </p>
          {noConvenientes.length > 0 && (
            <p className={s.nota}>
              Si quieres contratar por tu cuenta {noConvenientes.join(", ")}, te avisaremos antes, porque todavía no conoces
              bien cómo funcionan.
            </p>
          )}
          <p className={s.pequena}>
            El nivel de riesgo (1 muy bajo, 7 muy alto) aparece en el documento de datos fundamentales de cada fondo.
          </p>
        </Revela>

        <Revela como="section" className={s.tarjeta} retraso={0.12}>
          <h2 id="t-entendido">Lo que nos has contado</h2>
          <ul className={s.filas}>
            {filas.map((f) => (
              <FilaDato key={f.ruta} fila={f} fact={perfil.mifid[f.ruta]} />
            ))}
          </ul>
        </Revela>
      </div>

      {alertas.map((a) => (
        <AvisoCliente key={a.id} alerta={a} />
      ))}

      <Revela como="section" className={`${s.tarjeta} ${s.siguiente}`}>
        <div className={s.siguienteIcono} aria-hidden="true">
          {revisado ? Icono.check : <span className={s.reloj} />}
        </div>
        <div style={{ flex: "1 1 280px" }}>
          <h2>Siguiente paso</h2>
          <p className={s.suave}>
            {revisado
              ? "Una persona del banco ya ha revisado tu perfil. Ya puedes ver los productos que encajan contigo."
              : "Una persona del banco revisará tu perfil. Te avisaremos cuando esté listo; no tienes que hacer nada más."}
          </p>
        </div>
        <div className={s.botones}>
          {revisado ? (
            <Link href="/onboarding/productos" className={s.boton}>
              Ver productos que encajan conmigo
            </Link>
          ) : (
            <span className={`${s.boton} ${s.botonApagado}`} aria-disabled="true">
              Productos, cuando esté revisado
            </span>
          )}
        </div>
      </Revela>
    </>
  );
}

/** Semicírculo del 1 al 7 con una aguja que se coloca en el riesgo máximo. */
function Medidor({ nivel }: { nivel: number | null }) {
  const n = nivel ?? 0;
  const angulo = nivel ? -90 + ((n - 0.5) / 7) * 180 : -90;
  const segmentos = Array.from({ length: 7 }, (_, i) => {
    const a0 = Math.PI * (1 - i / 7) - 0.03;
    const a1 = Math.PI * (1 - (i + 1) / 7) + 0.03;
    const p = (a: number, r: number) => `${100 + r * Math.cos(a)} ${100 - r * Math.sin(a)}`;
    return { d: `M ${p(a0, 88)} A 88 88 0 0 1 ${p(a1, 88)}`, activo: i < n, i };
  });
  return (
    <div className={s.medidorCaja} role="img" aria-label={`Riesgo máximo ${nivel ?? "sin definir"} de 7`}>
      <svg viewBox="0 0 200 112" width="100%">
        <defs>
          <linearGradient id="g-riesgo" gradientUnits="userSpaceOnUse" x1="12" y1="0" x2="188" y2="0">
            <stop offset="0" stopColor="#3ec6a8" />
            <stop offset="0.5" stopColor="#0046de" />
            <stop offset="1" stopColor="#8b45d6" />
          </linearGradient>
        </defs>
        {segmentos.map((g) => (
          <path
            key={g.i}
            d={g.d}
            fill="none"
            strokeWidth="16"
            strokeLinecap="round"
            stroke={g.activo ? "url(#g-riesgo)" : "#e6ebf5"}
            className={g.activo ? s.segActivo : ""}
            style={{ animationDelay: `${0.15 + g.i * 0.08}s` }}
          />
        ))}
        <g className={s.aguja} style={{ "--ang": `${angulo}deg` } as React.CSSProperties}>
          <path d="M 100 100 L 97 46 L 100 40 L 103 46 Z" fill="#0e1020" />
        </g>
        <circle cx="100" cy="100" r="8" fill="#0e1020" />
        <circle cx="100" cy="100" r="3" fill="#ffffff" />
      </svg>
      <div className={s.medidorNum}>
        <strong>{nivel ?? "—"}</strong>
        <span>de 7</span>
      </div>
    </div>
  );
}

function FilaDato({ fila, fact }: { fila: Fila; fact: Fact }) {
  const [abierta, setAbierta] = useState(false);
  const cita = fact.evidence[0]?.quote;
  const id = `cita-${fila.ruta.replace(/\./g, "-")}`;
  const expandible = Boolean(cita || fila.nota || fact.source === "calculated");
  return (
    <li className={s.fila}>
      <button
        type="button"
        className={s.filaBoton}
        aria-expanded={expandible ? abierta : undefined}
        aria-controls={expandible ? id : undefined}
        onClick={() => expandible && setAbierta((a) => !a)}
      >
        <span className={s.filaTexto}>
          <span className={s.filaTitulo}>{fila.titulo}</span>
          <span className={s.filaValor}>{fila.valor(fact)}</span>
        </span>
        {expandible && <span className={`${s.mas} ${abierta ? s.masAbierto : ""}`} aria-hidden="true" />}
      </button>
      {abierta && (
        <div id={id} className={s.filaDetalle}>
          {cita ? (
            <p className={s.cita}>
              <span>Nos dijiste</span>«{cita}»
            </p>
          ) : fact.source === "calculated" ? (
            <p className={s.cita}>
              <span>Lo hemos calculado</span>Con tu ahorro y tus gastos fijos al mes.
            </p>
          ) : null}
          {fila.nota && <p className={s.pequena}>{fila.nota}</p>}
        </div>
      )}
    </li>
  );
}

function AvisoCliente({ alerta }: { alerta: Alerta }) {
  const familia = FAMILIAS[(alerta.path ?? "").split(".").pop() ?? ""];
  const texto =
    alerta.flag === "declared_vs_demonstrated" && familia
      ? `Nos dijiste que conoces bien los ${familia}, pero una de tus respuestas nos hace pensar que conviene repasar cómo funcionan. Lo hablaremos contigo antes de ofrecerte nada de ese tipo.`
      : "Hay un punto que queremos confirmar contigo antes de cerrar tu perfil. Te lo preguntaremos en la revisión.";
  const cita = alerta.evidence[0]?.quote;
  return (
    <Revela como="section" className={s.aviso}>
      <span className={s.avisoIcono} aria-hidden="true">
        {Icono.aviso}
      </span>
      <div>
        <h2>Algo que conviene aclarar</h2>
        <p>{texto}</p>
        {cita && <p className={s.avisoCita}>«{cita}»</p>}
      </div>
    </Revela>
  );
}
