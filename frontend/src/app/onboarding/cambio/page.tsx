"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { BarraCliente } from "@/components/BarraCliente";
import { IconoMotivo } from "@/components/IconoMotivo";
import s from "@/components/revision.module.css";
import c from "@/components/cliente.module.css";
import { api } from "@/lib/api";
import { useEsPropio } from "@/lib/useRevision";
import { useOnboarding } from "@/lib/onboarding";
import { minutos, nombreDato, TIPO_PREGUNTA, valorLegible } from "@/lib/revision";
import type { MotivoRevision, Revision } from "@/lib/tipos";
import { usePerfil } from "@/lib/usePerfil";

const ESPERA_MS = 250;

/**
 * «Ha cambiado algo»: el cliente elige qué ha cambiado y ve, antes de empezar, exactamente qué le vamos a
 * preguntar y qué se queda como está. Lo decide el planificador del backend (determinista), no el modelo.
 */
export default function HaCambiadoAlgo() {
  const { clientId } = useOnboarding();
  const { perfil, revision: abierta } = usePerfil(clientId);
  const [motivos, setMotivos] = useState<MotivoRevision[] | null>(null);
  const [elegidos, setElegidos] = useState<string[]>([]);
  const [previa, setPrevia] = useState<Revision | null>(null);
  const [estado, setEstado] = useState<{ enviando: boolean; error: string | null }>({ enviando: false, error: null });
  const router = useRouter();
  const propio = useEsPropio(clientId);
  const completo = perfil?.assessments.suitability.complete ?? false;

  useEffect(() => {
    api.motivosRevision().then(setMotivos).catch(() => setMotivos([]));
  }, []);

  // Si ya hay una revisión abierta, se parte de sus motivos.
  const precargado = useRef(false);
  useEffect(() => {
    if (precargado.current || !abierta?.open) return;
    precargado.current = true;
    setElegidos(abierta.reasons.map((r) => r.code));
  }, [abierta]);

  // Vista previa en vivo: qué preguntaríamos con estos motivos (no escribe nada).
  useEffect(() => {
    if (!propio || !completo || elegidos.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- sin motivos no hay vista previa
      setPrevia(null);
      return;
    }
    const t = setTimeout(() => {
      api.previsualizarRevision(clientId, elegidos).then(setPrevia).catch(() => setPrevia(null));
    }, ESPERA_MS);
    return () => clearTimeout(t);
  }, [clientId, elegidos, propio, completo]);

  const alternar = (code: string) =>
    setElegidos((e) => (e.includes(code) ? e.filter((x) => x !== code) : [...e, code]));

  const empezar = async (modo: "voz" | "texto") => {
    setEstado({ enviando: true, error: null });
    try {
      await api.abrirRevision(clientId, elegidos);
      router.push(`/onboarding/entrevista?revision=1&modo=${modo}`);
    } catch (e) {
      const m = e instanceof Error ? e.message : String(e);
      setEstado({ enviando: false, error: m.startsWith("409") ? "Primero termina tu entrevista: aún faltan datos de tu perfil." : "No hemos podido empezar la revisión. Inténtalo de nuevo." });
    }
  };

  const preguntas = useMemo(() => (previa?.open ? previa.questions : []), [previa]);
  const datosQueSiguen = useMemo(() => {
    if (!perfil) return 0;
    const tocados = new Set(preguntas.map((q) => q.path));
    return Object.entries(perfil.mifid).filter(([r, f]) => f.value != null && f.source !== "calculated" && !tocados.has(r) && !r.startsWith("disclosures.")).length;
  }, [perfil, preguntas]);

  return (
    <div className={c.raiz}>
      <BarraCliente paso={2} />
      <main className={c.caja}>
        <section className={`${c.hero} ${s.hero}`}>
          <div className={c.heroTexto}>
            <span className={`${c.estado} ${c.estadoOk}`}>
              <i aria-hidden="true" />
              Tu perfil sigue vivo
            </span>
            <h1>
              ¿Ha cambiado <span className={c.grad}>algo en tu vida</span>?
            </h1>
            <p>
              Cuéntanos qué ha pasado y te haremos solo las preguntas necesarias. Lo demás se queda como está: no hay que
              repetir la entrevista.
            </p>
          </div>
          <ol className={s.pasosMini} aria-label="Cómo funciona">
            <li className={elegidos.length ? s.pasoHecho : s.pasoActual}><b>1</b>Elige qué ha cambiado</li>
            <li className={elegidos.length ? s.pasoActual : ""}><b>2</b>Mira qué te preguntaremos</li>
            <li><b>3</b>Contesta en un par de minutos</li>
          </ol>
        </section>

        {!propio && (
          <div className={c.aviso}>
            <div>
              <h2>Primero, tu entrevista</h2>
              <p>Para revisar un perfil hace falta tenerlo. Haz la entrevista (unos ocho minutos) y vuelve aquí cuando cambie algo.</p>
              <p style={{ marginTop: 12 }}><Link href="/onboarding/entrevista" className={c.boton}>Empezar mi entrevista</Link></p>
            </div>
          </div>
        )}
        {propio && perfil && !completo && (
          <div className={c.aviso}>
            <div>
              <h2>Tu entrevista está a medias</h2>
              <p>Termínala primero: en cuanto tu perfil esté completo podrás actualizarlo desde aquí.</p>
              <p style={{ marginTop: 12 }}><Link href="/onboarding/entrevista" className={c.boton}>Seguir la entrevista</Link></p>
            </div>
          </div>
        )}

        <div className={s.disposicion}>
          <section aria-labelledby="t-motivos">
            <h2 id="t-motivos" className={s.titulo}>¿Qué ha cambiado?</h2>
            <p className={s.ayuda}>Puedes elegir más de una cosa.</p>
            <div className={s.motivos}>
              {(motivos ?? []).map((m, i) => {
                const activo = elegidos.includes(m.code);
                return (
                  <button
                    key={m.code}
                    type="button"
                    aria-pressed={activo}
                    disabled={!propio || !completo}
                    className={`${s.motivo} ${activo ? s.motivoActivo : ""}`}
                    style={{ animationDelay: `${i * 0.05}s` }}
                    onClick={() => alternar(m.code)}
                  >
                    <span className={s.motivoIcono}><IconoMotivo icono={m.icono} /></span>
                    <span className={s.motivoTexto}>
                      <strong>{m.titulo}</strong>
                      <span>{m.detalle}</span>
                    </span>
                    <span className={s.marca} aria-hidden="true" />
                  </button>
                );
              })}
              {motivos === null && Array.from({ length: 6 }, (_, i) => <span key={i} className={s.motivoCargando} />)}
            </div>
          </section>

          <aside className={s.panel} aria-live="polite" aria-labelledby="t-plan">
            <h2 id="t-plan" className={s.titulo}>Te preguntaremos</h2>
            {preguntas.length === 0 ? (
              <div className={s.vacio}>
                <span className={s.vacioOrbe} aria-hidden="true" />
                <p>Elige qué ha cambiado y aquí verás, una a una, las preguntas que te haremos.</p>
              </div>
            ) : (
              <>
                <div className={s.contadores}>
                  <span><b key={preguntas.length} className={s.numero}>{preguntas.length}</b> {preguntas.length === 1 ? "pregunta" : "preguntas"}</span>
                  <span><b className={s.numero}>~{minutos(preguntas.length)}</b> min</span>
                  <span><b className={s.numero}>{datosQueSiguen}</b> datos siguen igual</span>
                </div>
                <ol className={s.lista}>
                  {preguntas.map((q, i) => (
                    <li key={q.path} className={s.pregunta} style={{ animationDelay: `${i * 0.07}s` }}>
                      <span className={`${s.chip} ${s[`chip_${q.tipo}`]}`} title={TIPO_PREGUNTA[q.tipo].ayuda}>{TIPO_PREGUNTA[q.tipo].nombre}</span>
                      <span className={s.preguntaTexto}>
                        <strong>{nombreDato(q.path)}</strong>
                        {q.tipo === "confirmar" && q.valor_vigente != null && (
                          <span>Tenemos anotado: {valorLegible(q.path, q.valor_vigente)}</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ol>
                {previa?.open && previa.full_reassessment && (
                  <p className={c.nota}>Con estos cambios conviene repasar tu perfil entero. Empezamos por esto y, si hace falta, seguimos.</p>
                )}
                <p className={s.leyenda}>
                  Una persona de la entidad revisará los cambios. Mientras tanto, quien te proponga productos sabrá qué datos
                  están en revisión.
                </p>
                <div className={c.botones}>
                  <button type="button" className={c.boton} disabled={estado.enviando} onClick={() => empezar("voz")}>
                    {estado.enviando ? "Preparando…" : "Empezar hablando"}
                  </button>
                  <button type="button" className={c.botonSec} disabled={estado.enviando} onClick={() => empezar("texto")}>
                    Prefiero escribir
                  </button>
                </div>
                {estado.error && <p role="alert" className={c.error} style={{ marginTop: 12 }}>{estado.error}</p>}
              </>
            )}
          </aside>
        </div>

        <p className={s.volver}><Link href="/onboarding/perfil">← Volver a mi perfil</Link></p>

        {/* Móvil: el plan queda debajo de los motivos; esta barra dice cuánto es y lleva hasta él. */}
        {preguntas.length > 0 && (
          <div className={s.barraMovil}>
            <span>
              <b key={preguntas.length}>{preguntas.length}</b> {preguntas.length === 1 ? "pregunta" : "preguntas"} · ~{minutos(preguntas.length)} min
            </span>
            <button type="button" onClick={() => document.getElementById("t-plan")?.scrollIntoView({ behavior: "smooth", block: "start" })}>
              Ver y empezar ↓
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
