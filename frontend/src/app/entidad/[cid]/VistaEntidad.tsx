"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { nombrePerfil } from "@/components/PanelVivo";
import { Icono } from "@/components/visual";
import { api } from "@/lib/api";
import {
  ESTADOS,
  ETIQUETAS,
  FAMILIAS,
  FUENTES,
  mostrarValor,
} from "@/lib/bloques";
import type { Fact, Perfil, Restricciones, VersionResumen } from "@/lib/tipos";
import { usePerfil } from "@/lib/usePerfil";
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
  const { perfil, restricciones, error, recargar } = usePerfil(cid, SONDEO_MS);
  const [pestana, setPestana] = useState<Pestana>("Resumen");
  const [abierto, setAbierto] = useState<string | null>(null);
  const [validando, setValidando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);
  const [aviso, setAviso] = useState(0);

  const validar = async () => {
    setValidando(true);
    setFallo(null);
    try {
      await api.validar(cid, "asesor-demo");
      await recargar();
      setAviso(Date.now());
    } catch (e) {
      setFallo(e instanceof Error ? e.message : String(e));
    } finally {
      setValidando(false);
    }
  };

  const alertas = perfil?.alerts.filter((a) => a.status === "open") ?? [];

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
              {perfil ? TITULO[perfil.status] : "cargando…"}
            </h1>
            {perfil && (
              <>
                <p>
                  {perfil.status === "active"
                    ? `Versión ${perfil.version}, validada. El agente de la entidad ya puede usarla por MCP.`
                    : `Versión ${perfil.version}. Revisa las evidencias y los avisos y valídalo: hasta entonces, el agente de la entidad no puede usarlo.`}
                  {esSimulado(perfil) && (
                    <span className={s.simulado}>Datos simulados</span>
                  )}
                </p>
                <Recorrido estado={perfil.status} />
              </>
            )}
            <div className={s.accion}>
              {perfil?.status === "pending_validation" && (
                <button
                  className={s.boton}
                  onClick={validar}
                  disabled={validando}
                >
                  {validando ? "Validando…" : "Validar perfil"}{" "}
                  <span aria-hidden="true">→</span>
                </button>
              )}
              {perfil?.status === "active" && (
                <span className={s.sello}>
                  {Icono.check}
                  Validado · v{perfil.version}
                </span>
              )}
            </div>
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
        {fallo && (
          <p role="alert" className={s.error}>
            {fallo}
          </p>
        )}
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
          <Historial cid={cid} version={perfil.version} />
        )}
        {perfil && pestana === "Agente · MCP" && (
          <Mcp restricciones={restricciones} />
        )}
      </main>

      {aviso > 0 && (
        <div key={aviso} className={s.toast} role="status">
          Perfil validado. El agente de la entidad ya puede usarlo por MCP.
        </div>
      )}
    </div>
  );
}

function Resumen({
  perfil,
  alVerEvidencia,
}: {
  perfil: Perfil;
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

function Historial({ cid, version }: { cid: string; version: number }) {
  const [versiones, setVersiones] = useState<VersionResumen[] | null>(null);
  useEffect(() => {
    let vivo = true;
    api
      .versiones(cid)
      .then((v) => vivo && setVersiones([...v].reverse()))
      .catch(() => vivo && setVersiones([]));
    return () => {
      vivo = false;
    };
  }, [cid, version]);
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
        </div>
        <p className="pequena" style={{ margin: 0, color: "#4b4b6b" }}>
          En la demo esto se hace en Claude, con nuestro MCP y el de MyInvestor
          como conectores.
        </p>
      </div>
    </div>
  );
}

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
