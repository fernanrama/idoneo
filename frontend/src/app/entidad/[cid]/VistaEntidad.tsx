"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { nombrePerfil } from "@/components/PanelVivo";
import { Icono } from "@/components/visual";
import { api } from "@/lib/api";
import { CLIENTE_DEMO, tokenCliente } from "@/lib/credenciales";
import {
  ESTADOS,
  ETIQUETAS,
  FAMILIAS,
  FUENTES,
  mostrarValor,
} from "@/lib/bloques";
import type { Comparacion, Fact, Perfil, Restricciones, Revision, VersionResumen } from "@/lib/tipos";
import { AntesDespues, Busquedas, EnRevision } from "@/components/PerfilCambios";
import { usePerfil } from "@/lib/usePerfil";
import { esValidable } from "@/lib/validacion";
import { OrbePerfil, PALETA_ENTIDAD } from "@/components/Formas";
import s from "./entidad.module.css";

// Se refresca sola: durante la demo está abierta en una segunda pantalla mientras el cliente habla.
const SONDEO_MS = 2000;
const PESTANAS = [
  "Resumen",
  "Evidencias",
  "Historial",
  "Agente · MCP",
] as const;
type Pestana = (typeof PESTANAS)[number];

const TITULO: Record<string, string> = {
  active: "perfil validado",
  pending_validation: "perfil por validar",
  draft: "perfil en construcción",
  review_due: "perfil en revisión",
};

/** Vista de la entidad: perfil con evidencias, resultados y validación humana. No es un panel de banquero. */
export default function VistaEntidad({
  params,
}: {
  params: Promise<{ cid: string }>;
}) {
  const { cid } = use(params);
  // Modo asesor de demo: lo confirma el servidor; mientras tanto no se carga ninguna fuente.
  const modo = useModoAsesor(cid);
  const asesor = modo === null ? null : modo.permitido;
  const { perfil, restricciones, versiones, revision, cambios, error, recargar } = usePerfil(cid, SONDEO_MS, {
    asesor: asesor === true,
    esperar: asesor === null,
  });
  const [accion, setAccion] = useState<{ enCurso: boolean; error: string | null }>({ enCurso: false, error: null });
  const ejecutar = async (fn: () => Promise<unknown>) => {
    setAccion({ enCurso: true, error: null });
    try {
      await fn();
      await recargar();
      setAccion({ enCurso: false, error: null });
    } catch (e) {
      setAccion({ enCurso: false, error: e instanceof Error ? e.message : String(e) });
    }
  };
  const [pestana, setPestana] = useState<Pestana>("Resumen");
  const [abierto, setAbierto] = useState<string | null>(null);
  const alertas = perfil?.alerts.filter((a) => a.status === "open") ?? [];
  const paraAsesor = alertas.filter((a) => a.flag === "needs_advisor").length;
  // Qué estados se validan (incluido review_due tras una microentrevista): ver esValidable.
  const validable = esValidable(perfil);

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
            <span className={s.sesion}>
              <i aria-hidden="true" /> Asesor · demo
            </span>
          </nav>
        </div>
      </header>

      <section className={s.hero}>
        <div className={s.puntos} aria-hidden="true" />
        <div className={s.heroCaja}>
          <div className={s.heroTexto}>
            {perfil && (
              <span
                className={`${s.insignia} ${s[`ins_${perfil.status}`] ?? ""}`}
              >
                {ESTADOS[perfil.status]}
              </span>
            )}
            <h1>
              <span className={s.grad}>{cid},</span>
              <br />
              {perfil ? (revision?.open || restricciones?.pending_review ? "cambios por validar" : TITULO[perfil.status]) : "cargando…"}
            </h1>
            {perfil && (
              <>
                <p>
                  {perfil.status === "active"
                    ? `Versión ${perfil.version}, validada. El agente de la entidad ya puede usarla por MCP.`
                    : restricciones?.pending_review
                      ? `El cliente ha contado que algo ha cambiado. La versión ${perfil.version} recoge sus respuestas; el agente sigue usando la ${restricciones.profile_version} hasta que valides.`
                      : `Versión ${perfil.version}. Revisa las evidencias y los avisos y valídalo: hasta entonces, el agente de la entidad no puede usarlo.`}
                  {(esSimulado(perfil) || asesor) && (
                    <span className={s.simulado}>Datos simulados</span>
                  )}
                </p>
                <Recorrido estado={restricciones?.pending_review && perfil.status !== "active" ? "pending_validation" : perfil.status} />
              </>
            )}
            {asesor === true && (
              <p role="note">Modo asesor de demostración: cliente ficticio y validación autorizada por el servidor local.</p>
            )}
            {modo?.activo && !modo.permitido && (
              <p role="note">
                Modo asesor de demostración activo, pero este cliente aún no está autorizado. El operador debe ejecutar en el
                ordenador del backend <code>python scripts/demo_operador.py autorizar {cid} --confirmo-ficticio</code> y
                después recargar esta página.
              </p>
            )}
            {asesor === false && cid === CLIENTE_DEMO && !tokenCliente(cid) && (
              <p role="note">Ejemplo ficticio fijo de solo lectura; no representa un expediente persistido.</p>
            )}
            {asesor === false && !modo?.activo && validable && (
              <p role="note">La validación está pendiente de habilitar un permiso independiente de asesor.</p>
            )}
            {validable && paraAsesor > 0 && (
              <p role="note">
                {paraAsesor === 1 ? "Hay 1 alerta" : `Hay ${paraAsesor} alertas`} para revisar antes de validar: al validar,
                quedan revisadas por el asesor.
              </p>
            )}
            <div className={s.accion}>
              {validable && (
                <button
                  type="button"
                  className={s.boton}
                  disabled={asesor !== true || accion.enCurso}
                  title={asesor === true ? undefined : "Requiere un permiso independiente de asesor"}
                  onClick={asesor === true ? () => ejecutar(() => api.validarComoAsesor(cid)) : undefined}
                >
                  {accion.enCurso ? "Validando…" : restricciones?.pending_review ? "Validar los cambios" : "Validar perfil"}{" "}
                  <span aria-hidden="true">→</span>
                </button>
              )}
              {perfil?.status === "active" && (
                <span className={s.sello}>
                  {Icono.check}
                  Validado · v{perfil.version}
                </span>
              )}
              {asesor === true && cid === CLIENTE_DEMO && perfil?.status === "active" && (
                <button
                  type="button"
                  className={s.reiniciar}
                  disabled={accion.enCurso}
                  onClick={() => ejecutar(api.reiniciarComoAsesor)}
                >
                  Reiniciar la demo
                </button>
              )}
            </div>
            {accion.error && (
              <p role="alert" className={s.error}>
                {accion.error}
              </p>
            )}
            {error && (
              <p role="alert" className={s.error}>
                {error}
              </p>
            )}
          </div>
          {perfil && (
            <div className={s.cinta}>
              <OrbePerfil
                tono="entidad"
                paleta={PALETA_ENTIDAD}
                rasgos={[
                  `${Object.values(perfil.mifid).filter((f) => f.evidence.some((e) => e.quote)).length} datos con su frase`,
                  alertas.length
                    ? `${alertas.length} ${alertas.length === 1 ? "aviso abierto" : "avisos abiertos"}`
                    : "Sin avisos",
                  `Riesgo hasta ${perfil.assessments.suitability.max_sri ?? "—"} de 7`,
                  `Versión ${perfil.version}`,
                ]}
              />
            </div>
          )}
        </div>
      </section>

      <main className={s.cuerpo}>
        <div
          className={s.pestanas}
          role="tablist"
          aria-label="Secciones del perfil"
        >
          {PESTANAS.map((p) => (
            <button
              key={p}
              role="tab"
              aria-selected={pestana === p}
              className={`${s.pestana} ${pestana === p ? s.pestanaActiva : ""}`}
              onClick={() => setPestana(p)}
            >
              {p}
              {p === "Resumen" && alertas.length > 0 && (
                <span className={s.cuenta}>{alertas.length}</span>
              )}
            </button>
          ))}
        </div>

        {perfil && pestana === "Resumen" && (
          <Resumen
            perfil={perfil}
            restricciones={restricciones}
            revision={revision}
            cambios={cambios}
            alVerEvidencia={(ruta) => {
              setPestana("Evidencias");
              setAbierto(ruta);
            }}
          />
        )}
        {perfil && pestana === "Evidencias" && (
          <Evidencias
            perfil={perfil}
            abierto={abierto}
            setAbierto={setAbierto}
          />
        )}
        {perfil && pestana === "Historial" && (
          <Historial cid={cid} version={perfil.version} precargadas={asesor === true ? versiones : undefined} />
        )}
        {perfil && pestana === "Agente · MCP" && (
          <Mcp restricciones={restricciones} />
        )}
      </main>

    </div>
  );
}

function Resumen({
  perfil,
  restricciones,
  revision,
  cambios,
  alVerEvidencia,
}: {
  perfil: Perfil;
  restricciones: Restricciones | null;
  revision: Revision | null;
  cambios: Comparacion | null;
  alVerEvidencia: (ruta: string) => void;
}) {
  const su = perfil.assessments.suitability;
  const alertas = perfil.alerts.filter((a) => a.status === "open");
  const hechos = Object.values(perfil.mifid).filter(
    (f) => f.value !== null && f.value !== undefined,
  );
  const conCita = hechos.filter((f) => f.evidence.length > 0).length;
  const baja = hechos.filter(
    (f) => f.confidence != null && f.confidence < 0.65,
  ).length;
  return (
    <div className={s.aparece}>
      {restricciones?.pending_review && <EnRevision p={restricciones.pending_review} servida={restricciones.profile_version} revision={revision} tono="entidad" />}
      {cambios && <AntesDespues c={cambios} tono="entidad" />}
      {alertas.map((a) => (
        <div key={a.id} className={`${s.tarj} ${s.alerta}`} role="alert">
          {Icono.aviso}
          <strong>
            {a.flag === "declared_vs_demonstrated"
              ? "Declarado ≠ demostrado"
              : "Revisar"}
          </strong>
          <span>{a.message}</span>
          {a.path && (
            <button
              className={s.enlace}
              onClick={() => alVerEvidencia(a.path!)}
            >
              Ver la frase
            </button>
          )}
        </div>
      ))}
      {perfil.status === "draft" && su.missing.length > 0 && (
        <p className="pequena suave">
          Faltan datos obligatorios:{" "}
          {su.missing.map((m) => ETIQUETAS[m] ?? m).join(", ")}
        </p>
      )}
      <div className={s.rejilla}>
        <div className={`${s.tarj} ${s.tarjHover} ${s.bloque}`}>
          <h2>Idoneidad · calculada con reglas fijas</h2>
          <div className={s.grande}>{nombrePerfil(su.risk_profile)}</div>
          <div
            className={s.sri}
            role="img"
            aria-label={`SRI máximo ${su.max_sri ?? "sin definir"} de 7`}
          >
            {Array.from({ length: 7 }, (_, i) => (
              <span
                key={i}
                className={su.max_sri != null && i < su.max_sri ? s.lleno : ""}
              />
            ))}
          </div>
          <p className="pequena" style={{ margin: 0, color: "#4b4b6b" }}>
            SRI máximo{" "}
            <strong style={{ color: "#12122a" }}>
              {su.max_sri ?? "—"} de 7
            </strong>
          </p>
          {su.rationale.length > 0 && (
            <ul className={s.lista}>
              {su.rationale.map(legible).map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          )}
        </div>
        <div className={`${s.tarj} ${s.tarjHover} ${s.bloque}`}>
          <h2>Conveniencia por familia</h2>
          {Object.entries(perfil.assessments.appropriateness)
            .filter(([, v]) => v !== "not_assessed")
            .map(([f, v]) => (
              <div key={f} className={s.familia}>
                <span>
                  {(FAMILIAS[f] ?? f).replace(/^./, (c) => c.toUpperCase())}
                </span>
                <span className={v === "appropriate" ? s.si : s.no}>
                  {v === "appropriate" ? "Conveniente" : "No conveniente"}
                </span>
              </div>
            ))}
        </div>
        <div className={`${s.tarj} ${s.tarjHover} ${s.bloque}`}>
          <h2>Calidad del perfil</h2>
          <div>
            <span className={s.grande}>{conCita}</span>{" "}
            <span style={{ color: "#4b4b6b" }}>datos con su frase</span>
          </div>
          <p className="pequena" style={{ margin: 0, color: "#4b4b6b" }}>
            {hechos.length} datos en total · {baja} con confianza baja ·{" "}
            {alertas.length}{" "}
            {alertas.length === 1 ? "alerta abierta" : "alertas abiertas"}
          </p>
        </div>
      </div>
      {restricciones && (
        <div className={`${s.tarj} ${s.bloque}`}>
          <h2>Qué puede buscar el agente en el catálogo · calculado, no lo decide el modelo</h2>
          <Busquedas r={restricciones} perfil={perfil} tono="entidad" />
        </div>
      )}
    </div>
  );
}

function Evidencias({
  perfil,
  abierto,
  setAbierto,
}: {
  perfil: Perfil;
  abierto: string | null;
  setAbierto: (r: string | null) => void;
}) {
  const filas = Object.entries(perfil.mifid).sort(([a], [b]) => {
    const fa = perfil.mifid[a].flags.length > 0 ? 0 : 1;
    const fb = perfil.mifid[b].flags.length > 0 ? 0 : 1;
    return fa - fb;
  });
  return (
    <div
      className={`${s.tarj} ${s.aparece}`}
      style={{ gap: 0, overflow: "hidden" }}
    >
      {filas.map(([ruta, f]) => (
        <FilaEvidencia
          key={ruta}
          ruta={ruta}
          f={f}
          abierta={abierto === ruta}
          alternar={() => setAbierto(abierto === ruta ? null : ruta)}
        />
      ))}
    </div>
  );
}

function FilaEvidencia({
  ruta,
  f,
  abierta,
  alternar,
}: {
  ruta: string;
  f: Fact;
  abierta: boolean;
  alternar: () => void;
}) {
  const tieneDetalle =
    f.evidence.length > 0 ||
    f.source === "calculated" ||
    (f.declared != null && f.declared !== f.value);
  return (
    <div className={s.fila}>
      <button
        className={s.filaBoton}
        onClick={alternar}
        aria-expanded={abierta}
        disabled={!tieneDetalle}
        style={{ cursor: tieneDetalle ? "pointer" : "default" }}
      >
        <span className={s.etq}>{ETIQUETAS[ruta] ?? ruta}</span>
        <strong>{mostrarValor(f.value)}</strong>
        <span className={`${s.chip} ${s[`chip_${f.source}`] ?? ""}`}>
          {FUENTES[f.source] ?? f.source}
        </span>
        {f.flags.length > 0 && (
          <span className={`${s.chip} ${s.chip_aviso}`}>alerta</span>
        )}
        <span className={s.confianza}>
          {f.source === "calculated"
            ? "regla"
            : f.confidence != null
              ? `${Math.round(f.confidence * 100)} %`
              : ""}
        </span>
      </button>
      {abierta && (
        <div className={s.detalle}>
          {f.declared != null && f.declared !== f.value && (
            <p className={s.declaro}>Declaró «{mostrarValor(f.declared)}»</p>
          )}
          {f.evidence.map((ev, i) => (
            <div key={i} className={s.evidencia}>
              {ev.audio_url ? (
                <audio
                  controls
                  src={ev.audio_url}
                  style={{ height: 40 }}
                  aria-label="Escuchar la frase"
                />
              ) : (
                <span
                  className={`${s.play} ${s.playApagado}`}
                  title="El clip de audio aún no está disponible"
                  aria-hidden="true"
                >
                  {Icono.play}
                </span>
              )}
              <p>«{ev.quote}»</p>
              <span className={s.meta}>
                sesión {ev.session_id}
                {ev.turn_id ? `, ${ev.turn_id}` : ""} · {ev.t[0].toFixed(1)}–
                {ev.t[1].toFixed(1)} s
              </span>
            </div>
          ))}
          {f.source === "calculated" && (
            <p className={s.meta}>
              Cálculo determinista a partir de:{" "}
              {f.inputs.map((i) => ETIQUETAS[i] ?? i).join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Historial({ cid, version, precargadas }: { cid: string; version: number; precargadas?: VersionResumen[] | null }) {
  const [cargadas, setVersiones] = useState<VersionResumen[] | null>(null);
  const versiones = precargadas !== undefined ? (precargadas ? [...precargadas].reverse() : null) : cargadas;
  useEffect(() => {
    if (precargadas !== undefined) return; // modo asesor de demo: llegan con el expediente
    let vivo = true;
    api
      .versiones(cid)
      .then((v) => vivo && setVersiones([...v].reverse()))
      .catch(() => vivo && setVersiones([]));
    return () => {
      vivo = false;
    };
  }, [cid, version, precargadas]);
  return (
    <div className={`${s.tarj} ${s.aparece}`} style={{ padding: 24 }}>
      {versiones === null && <p className="pequena suave">Cargando…</p>}
      {versiones?.map((v) => (
        <div key={v.version} className={s.version}>
          <span className={s.versionPunto} aria-hidden="true" />
          <div>
            <strong>v{v.version}</strong> · {v.author} ·{" "}
            {ESTADOS[v.status] ?? v.status}
            <p>
              {v.reason} ·{" "}
              {new Date(v.created_at).toLocaleString("es-ES", {
                dateStyle: "short",
                timeStyle: "short",
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function Mcp({ restricciones: r }: { restricciones: Restricciones | null }) {
  if (!r) return null;
  return (
    <div className={`${s.mcp} ${s.aparece}`} style={{ flexDirection: "row" }}>
      <div className={`${s.tarj} ${s.bloque}`}>
        <div className={s.familia}>
          <strong>Restricciones para el agente</strong>
          <span
            className={`${s.chip} ${r.usable ? s.chip_demonstrated : s.chip_aviso}`}
          >
            {r.usable
              ? `Usable · v${r.profile_version}`
              : "Usable tras validar"}
          </span>
        </div>
        <p className="pequena" style={{ margin: 0, color: "#4b4b6b" }}>
          Lo que el agente pasa tal cual al catálogo de MyInvestor, y los
          filtros que aplica después sobre la ficha.
        </p>
        <pre className={s.codigo}>
          {JSON.stringify(
            {
              funds_query: r.funds_query,
              portfolios_query: r.portfolios_query,
              post_filters: r.post_filters,
              blocked_searches: r.blocked_searches ?? [],
              ...(r.pending_review ? { pending_review: r.pending_review } : {}),
            },
            null,
            2,
          )}
        </pre>
      </div>
      <div className={`${s.tarj} ${s.bloque}`}>
        <strong>El agente de la entidad, usándolo</strong>
        <span className={s.paso}>Ejemplo ilustrativo</span>
        <div className={s.burbujaPregunta}>
          ¿Qué fondos le puedo enseñar a este cliente?
        </div>
        <span className={s.paso}>
          → consulta el perfil por MCP · → busca en el catálogo con esos límites
        </span>
        <div className={s.burbujaRespuesta}>
          Su perfil {r.usable ? "validado" : "aún no validado"} permite
          productos con riesgo hasta {String(r.funds_query.max_risk ?? "—")}.{" "}
          {r.usable
            ? "Le enseño solo lo que encaja con esos límites."
            : "Hasta que un asesor lo valide, no lo uso para recomendar."}
          {r.pending_review &&
            ` Ojo: hay ${r.pending_review.paths.length} ${r.pending_review.paths.length === 1 ? "dato" : "datos"} en revisión; no me apoyo en ellos hasta que se validen.`}
          {(r.blocked_searches ?? []).length > 0 &&
            ` No busco ${(r.blocked_searches ?? []).map((b) => BUSQUEDA_NOMBRE[b] ?? b).join(", ")}.`}
        </div>
        <p className="pequena" style={{ margin: 0, color: "#4b4b6b" }}>
          En la demo esto se hace en Claude, con nuestro MCP y el de MyInvestor
          como conectores.
        </p>
      </div>
    </div>
  );
}

/**
 * null mientras el servidor responde. `activo`: el servidor confirma el modo asesor de demo;
 * `permitido`: además, este cliente es un fixture ficticio o lo ha autorizado el operador.
 */
function useModoAsesor(cid: string): { activo: boolean; permitido: boolean } | null {
  const [modo, setModo] = useState<{ cid: string; activo: boolean; permitido: boolean } | null>(null);
  useEffect(() => {
    let vivo = true;
    api
      .modoAsesor()
      .then((m) => vivo && setModo({ cid, activo: m.enabled, permitido: m.enabled && m.clients.includes(cid) }))
      .catch(() => vivo && setModo({ cid, activo: false, permitido: false }));
    return () => {
      vivo = false;
    };
  }, [cid]);
  return modo && modo.cid === cid ? { activo: modo.activo, permitido: modo.permitido } : null;
}

const BUSQUEDA_NOMBRE: Record<string, string> = { funds: "fondos", portfolios: "carteras", etfs: "ETF", stocks: "acciones" };

const esSimulado = (p: Perfil) =>
  p.author === "fixture" || /simulad/i.test(p.reason ?? "");

/** Dónde está el perfil dentro del recorrido: entrevista, revisión, validado y disponible para el agente. */
function Recorrido({ estado }: { estado: string }) {
  const pasos = [
    "Entrevista",
    "Revisión de la entidad",
    "Validado",
    "Disponible por MCP",
  ];
  const actual =
    estado === "active"
      ? 3
      : estado === "pending_validation"
        ? 1
        : estado === "review_due"
          ? 1
          : 0;
  return (
    <ol className={s.recorrido} aria-label="Estado del perfil">
      {pasos.map((p, i) => (
        <li
          key={p}
          className={i < actual ? s.rHecho : i === actual ? s.rActual : ""}
          aria-current={i === actual ? "step" : undefined}
        >
          <span>
            {i < actual || (estado === "active" && i === actual) ? "✓" : i + 1}
          </span>
          {p}
        </li>
      ))}
    </ol>
  );
}

/** Pasa los motivos del cálculo a lenguaje legible: nombres de perfil, miles con punto y sin «.0». */
function legible(m: string) {
  return m
    .replace(
      /\b(MUY_AGRESIVO|CONSERVADOR|MODERADO|DINAMICO|AGRESIVO)\b/g,
      (x) => nombrePerfil(x),
    )
    .replace(/(\d+)\.0\b/g, "$1")
    .replace(/(\d),(\d{3})/g, "$1.$2");
}
