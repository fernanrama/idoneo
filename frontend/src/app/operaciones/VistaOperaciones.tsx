"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import s from "./operaciones.module.css";

type Comprobacion = { metrica: string; etiqueta: string; valor: number | null; limite: { tipo: "min" | "max"; valor: number }; ok: boolean };
type Componente = {
  ejecutada: boolean;
  ok: boolean | null;
  prueba?: string;
  fecha?: string;
  modelo?: string;
  casos?: number;
  detalle?: string;
  metricas?: Record<string, number>;
  comprobaciones: Comprobacion[];
};
type Evals = { ok: boolean; componentes: Record<string, Componente>; aviso: string };
type Agente = {
  llamadas: number; fallos: number; tasa_fallo: number; latencia_p50_s: number; latencia_p95_s: number;
  tokens_entrada: number; tokens_salida: number; tasa_cache: number; coste_usd: number; coste_medio_usd: number;
  modelos: string[]; versiones_prompt: string[];
};
type Tipo = { ejecuciones: number; errores: number; duracion_p50_s: number; duracion_p95_s: number; llamadas_media: number; coste_medio_usd: number };
type Reciente = { id: string; tipo: string; inicio: string; duracion_s: number; estado: string; coste_usd: number; tokens: number; llamadas: { agente: string; resultado: string }[] };
type Metricas = {
  generado: string;
  totales: { ejecuciones: number; llamadas: number; fallos: number; coste_usd: number; tokens: number };
  por_agente: Record<string, Agente>;
  por_tipo: Record<string, Tipo>;
  por_version_prompt: { agente: string; version: string; llamadas: number; fallos: number; latencia_p50_s: number }[];
  recientes: Reciente[];
  aviso: string;
};

const NOMBRES: Record<string, string> = {
  extractor: "Extractor",
  verificador: "Verificador",
  laboratorio: "Entrevista completa (laboratorio)",
  juez: "Calidad de la conversación (juez)",
  calibracion_juez: "Calibración del juez",
  e2e: "Pipeline de punta a punta",
  entrevistador: "Entrevistador",
  cliente_simulado: "Cliente simulado",
  turno: "Turno del cliente",
  chat: "Respuesta del entrevistador",
};
const QUE_MIDE: Record<string, string> = {
  extractor: "Que cada dato del perfil sale de lo que dijo el cliente y nada se inventa.",
  verificador: "Que se detectan las contradicciones y señales de riesgo sin falsas alarmas.",
  laboratorio: "La entrevista entera con clientes simulados: datos, aviso de IA y cero recomendaciones.",
  juez: "Claridad, una pregunta por turno, neutralidad, trato y transparencia, puntuadas de 1 a 5.",
  calibracion_juez: "Si el juez puntúa igual que una persona del equipo antes de fiarnos de él.",
  e2e: "Cliente de ejemplo → entrevista → perfil → validación de la entidad → MCP → catálogo filtrado → trazas.",
};
const COMANDO: Record<string, string> = {
  extractor: "python scripts/evaluar_extractor.py --registrar",
  verificador: "python scripts/evaluar_verificador.py --repeticiones 3 --registrar",
  laboratorio: "python scripts/laboratorio.py --registrar",
  juez: "python scripts/laboratorio.py --juez --registrar",
  calibracion_juez: "python scripts/calibrar_juez.py --registrar",
  e2e: "python scripts/e2e.py --registrar",
};

const num = (v: number, d = 0) => v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v: number) => `${num(v * 100, v === 1 || v === 0 ? 0 : 1)} %`;
const seg = (v: number) => `${num(v, 1)} s`;
const usd = (v: number) => (v < 0.01 && v > 0 ? `${num(v, 4)} $` : `${num(v, 2)} $`);

function valor(c: Comprobacion) {
  if (c.valor === null || c.valor === undefined) return "—";
  if (/latencia|_s$/.test(c.metrica)) return seg(c.valor);
  if (c.limite.valor <= 1 && c.limite.valor > 0 && c.valor <= 1 && !/nota|neutralidad/.test(c.metrica)) return pct(c.valor);
  return num(c.valor, Number.isInteger(c.valor) ? 0 : 2);
}
function limite(c: Comprobacion) {
  const v = { ...c, valor: c.limite.valor };
  return `${c.limite.tipo === "min" ? "≥" : "≤"} ${valor(v)}`;
}

async function leer<T>(ruta: string): Promise<T> {
  const r = await fetch(`${API_URL}${ruta}`, { cache: "no-store" });
  if (!r.ok) throw new Error(String(r.status));
  return r.json() as Promise<T>;
}

export default function VistaOperaciones() {
  const [evals, setEvals] = useState<Evals | null>(null);
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let vivo = true;
    const cargar = () =>
      Promise.all([leer<Evals>("/api/ops/evals"), leer<Metricas>("/api/ops/metrics")])
        .then(([e, m]) => {
          if (!vivo) return;
          setEvals(e);
          setMetricas(m);
          setError(false);
        })
        .catch(() => vivo && setError(true));
    cargar();
    const t = setInterval(cargar, 10_000);
    return () => {
      vivo = false;
      clearInterval(t);
    };
  }, []);

  const comps = evals ? Object.entries(evals.componentes) : [];
  const hechas = comps.filter(([, c]) => c.ejecutada);
  const fallan = hechas.filter(([, c]) => !c.ok);
  const lab = evals?.componentes.laboratorio?.metricas;
  const ext = evals?.componentes.extractor?.metricas;
  const agentes = metricas ? Object.entries(metricas.por_agente) : [];
  const tipos = metricas ? Object.entries(metricas.por_tipo) : [];

  return (
    <div className={`tema-asesor ${s.raiz}`}>
      <header className={s.barra}>
        <div className={s.barraCaja}>
          <Link href="/" className={s.marca}>
            <span className={s.logo} aria-hidden="true" />
            Idóneo <span>para entidades</span>
          </Link>
          <nav className={s.nav} aria-label="Navegación de la entidad">
            <Link href="/">Inicio</Link>
            <Link href="/escenario">Escenario en vivo</Link>
            <Link href="/operaciones" aria-current="page">Calidad y costes</Link>
          </nav>
        </div>
      </header>

      <main className={s.cuerpo}>
        <section className={s.hero}>
          <span className={`${s.pastilla} ${evals ? (fallan.length ? s.mal : s.bien) : ""}`}>
            {!evals ? "Cargando…" : fallan.length ? `${fallan.length} evaluación${fallan.length > 1 ? "es" : ""} por debajo del umbral` : `${hechas.length} de ${comps.length} evaluaciones cumplen sus umbrales`}
          </span>
          <h1>
            Calidad y costes <span className={s.grad}>del agente</span>
          </h1>
          <p>
            Cada versión del agente se mide antes de publicarse con clientes simulados y unos umbrales mínimos. En producción,
            cada llamada a Claude queda trazada con su latencia, sus tokens y su coste estimado, sin guardar lo que dice el
            cliente.
          </p>
          <div className={s.cifras}>
            <Cifra etiqueta="Datos inventados" valor={ext ? num(ext.prohibidos ?? 0) : "—"} nota="en la última evaluación del extractor" />
            <Cifra etiqueta="Recomendaciones" valor={lab ? num(lab.recomendaciones ?? 0) : "—"} nota="el asistente nunca aconseja productos" />
            <Cifra etiqueta="Coste por entrevista" valor={lab?.coste_medio_usd ? `~${usd(lab.coste_medio_usd)}` : "—"} nota="estimado con la tarifa pública" />
            <Cifra
              etiqueta="Llamadas en vivo"
              valor={metricas ? num(metricas.totales.llamadas) : "—"}
              nota={metricas ? `${usd(metricas.totales.coste_usd)} desde que arrancó el servidor` : "desde que arrancó el servidor"}
            />
          </div>
          {error && <p role="alert" className={s.aviso}>No se puede leer el backend en {API_URL}. Comprueba que está arrancado.</p>}
        </section>

        <section className={s.seccion} aria-labelledby="t-evals">
          <div className={s.cabecera}>
            <h2 id="t-evals">Evaluaciones antes de publicar</h2>
            <p>La CI vuelve a pasarlas cuando cambia un prompt o un agente y bloquea la versión si alguna baja del umbral.</p>
          </div>
          <div className={s.rejilla}>
            {comps.map(([nombre, c]) => (
              <article key={nombre} className={s.tarjeta}>
                <div className={s.tarjetaCabeza}>
                  <h3>{NOMBRES[nombre] ?? nombre}</h3>
                  <span className={`${s.estado} ${!c.ejecutada ? s.pendiente : c.ok ? s.bien : s.mal}`}>
                    {!c.ejecutada ? "Sin ejecutar" : c.ok ? "Cumple" : "No cumple"}
                  </span>
                </div>
                <p className={s.queMide}>{QUE_MIDE[nombre]}</p>
                {c.ejecutada ? (
                  <>
                    <ul className={s.comprobaciones}>
                      {c.comprobaciones.map((f) => (
                        <li key={f.metrica} className={f.ok ? "" : s.falla}>
                          <span>{f.etiqueta}</span>
                          <strong>{valor(f)}</strong>
                          <small>{limite(f)}</small>
                        </li>
                      ))}
                    </ul>
                    <p className={s.meta}>
                      {c.prueba} · {c.fecha} · {c.casos} casos · <code>{c.modelo}</code>
                      {c.detalle ? <><br />{c.detalle}</> : null}
                    </p>
                  </>
                ) : (
                  <p className={s.meta}>
                    Necesita la API de Claude. Desde <code>backend/</code>: <code>{COMANDO[nombre]}</code>
                  </p>
                )}
              </article>
            ))}
          </div>
          {evals && <p className={s.meta}>{evals.aviso}</p>}
        </section>

        <section className={s.seccion} aria-labelledby="t-vivo">
          <div className={s.cabecera}>
            <h2 id="t-vivo">En vivo</h2>
            <p>Se actualiza cada 10 segundos. {metricas?.aviso}</p>
          </div>
          {metricas && metricas.totales.llamadas === 0 ? (
            <div className={s.vacio}>
              <strong>Aún no hay llamadas desde que arrancó el servidor.</strong>
              <span>Haz una entrevista por voz o por escrito y aquí aparecerán su latencia, sus tokens y su coste.</span>
            </div>
          ) : (
            <>
              <div className={s.tabla}>
                <table>
                  <thead>
                    <tr><th>Agente</th><th>Llamadas</th><th>Fallos</th><th>Latencia p50</th><th>Latencia p95</th><th>Desde caché</th><th>Coste</th><th>Modelo</th></tr>
                  </thead>
                  <tbody>
                    {agentes.map(([n, a]) => (
                      <tr key={n}>
                        <td>{NOMBRES[n] ?? n}</td>
                        <td>{num(a.llamadas)}</td>
                        <td className={a.fallos ? s.textoMal : ""}>{num(a.fallos)}</td>
                        <td>{seg(a.latencia_p50_s)}</td>
                        <td>{seg(a.latencia_p95_s)}</td>
                        <td>{pct(a.tasa_cache)}</td>
                        <td>{usd(a.coste_usd)}</td>
                        <td><code>{a.modelos.join(", ")}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className={s.dosColumnas}>
                <div className={s.tabla}>
                  <table>
                    <thead><tr><th>Trabajo</th><th>Veces</th><th>Duración p50</th><th>p95</th><th>Coste medio</th></tr></thead>
                    <tbody>
                      {tipos.map(([n, t]) => (
                        <tr key={n}>
                          <td>{NOMBRES[n] ?? n}</td>
                          <td>{num(t.ejecuciones)}</td>
                          <td>{seg(t.duracion_p50_s)}</td>
                          <td>{seg(t.duracion_p95_s)}</td>
                          <td>{usd(t.coste_medio_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className={s.tabla}>
                  <table>
                    <thead><tr><th>Versión del prompt</th><th>Llamadas</th><th>Fallos</th><th>p50</th></tr></thead>
                    <tbody>
                      {metricas?.por_version_prompt.map((v) => (
                        <tr key={`${v.agente}@${v.version}`}>
                          <td>{NOMBRES[v.agente] ?? v.agente} <code>{v.version}</code></td>
                          <td>{num(v.llamadas)}</td>
                          <td>{num(v.fallos)}</td>
                          <td>{seg(v.latencia_p50_s)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <h3 className={s.subtitulo}>Últimas ejecuciones</h3>
              <ol className={s.recientes}>
                {metricas?.recientes.slice(0, 10).map((r) => (
                  <li key={r.id}>
                    <span className={`${s.punto} ${r.estado === "ok" && r.llamadas.every((l) => l.resultado === "ok") ? s.bien : s.mal}`} aria-hidden="true" />
                    <span>{NOMBRES[r.tipo] ?? r.tipo}</span>
                    <span className={s.meta}>{r.llamadas.map((l) => NOMBRES[l.agente] ?? l.agente).join(" → ") || "sin llamadas"}</span>
                    <span>{seg(r.duracion_s)}</span>
                    <span>{num(r.tokens)} tokens</span>
                    <span>{usd(r.coste_usd)}</span>
                  </li>
                ))}
              </ol>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

function Cifra({ etiqueta, valor, nota }: { etiqueta: string; valor: string; nota: string }) {
  return (
    <div className={s.cifra}>
      <span>{etiqueta}</span>
      <strong>{valor}</strong>
      <small>{nota}</small>
    </div>
  );
}
