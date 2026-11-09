"use client";

import { use, useState } from "react";
import { AlertaTarjeta, Boton, Chip, Contenido, Etiqueta, HeroAsesor, Marca, Marco, Tarjeta } from "@/components/ui";
import ui from "@/components/ui.module.css";
import { api } from "@/lib/api";
import { ESTADOS, ETIQUETAS, FAMILIAS, FUENTES, mostrarValor } from "@/lib/bloques";
import { usePerfil } from "@/lib/usePerfil";

// Vista mínima de la entidad: perfil con evidencias, resultados y validación humana. No es un panel de banquero.
export default function VistaEntidad({ params }: { params: Promise<{ cid: string }> }) {
  const { cid } = use(params);
  const { perfil, restricciones, error, recargar } = usePerfil(cid);
  const [abierto, setAbierto] = useState<string | null>(null);
  const [validando, setValidando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);

  const validar = async () => {
    setValidando(true);
    setFallo(null);
    try {
      await api.validar(cid, "asesor-demo");
      await recargar();
    } catch (e) {
      setFallo(e instanceof Error ? e.message : String(e));
    } finally {
      setValidando(false);
    }
  };

  const s = perfil?.assessments.suitability;

  return (
    <Marco ancho asesor>
      <header className={ui.cabecera}>
        <Marca />
        <span className="pequena suave" style={{ marginLeft: "auto" }}>
          Vista de la entidad
        </span>
      </header>
      <Contenido>
        {error && <p role="alert">{error}</p>}
        {perfil && s && (
          <>
            <HeroAsesor>
              <Etiqueta color={perfil.status === "active" ? "verde" : "rosa"} punto>
                Perfil de cliente · {ESTADOS[perfil.status]}
              </Etiqueta>
              <h1>
                {cid}, <span className="degradado">{perfil.status === "active" ? "perfil validado" : "perfil por validar"}</span>
              </h1>
              <p>
                Versión {perfil.version} · {perfil.reason} · {perfil.author}. El agente de la entidad lo consulta por MCP; el
                asesor revisa y aprueba.
              </p>
              {perfil.status === "pending_validation" && (
                <Boton style={{ width: "auto" }} onClick={validar} disabled={validando}>
                  {validando ? "Validando…" : "Validar perfil"}
                </Boton>
              )}
            </HeroAsesor>

            {fallo && (
              <p role="alert" style={{ color: "var(--c-error)" }}>
                {fallo}
              </p>
            )}
            {perfil.status === "draft" && s.missing.length > 0 && (
              <p className="pequena suave">Faltan datos obligatorios: {s.missing.map((m) => ETIQUETAS[m] ?? m).join(", ")}</p>
            )}

            {perfil.alerts
              .filter((a) => a.status === "open")
              .map((a) => (
                <AlertaTarjeta key={a.id} alerta={a} />
              ))}

            <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
              <Tarjeta titulo="Idoneidad" extra={<Etiqueta color="violeta">Calculado</Etiqueta>}>
                <p>
                  Perfil <strong>{s.risk_profile ?? "—"}</strong> · SRI máximo <strong>{s.max_sri ?? "—"}/7</strong>
                </p>
                <ul className="pequena suave" style={{ margin: 0, paddingLeft: 18 }}>
                  {s.rationale.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </Tarjeta>
              <Tarjeta titulo="Conveniencia" extra={<Etiqueta color="azul">Por familia</Etiqueta>}>
                <div className="pila">
                  {Object.entries(perfil.assessments.appropriateness)
                    .filter(([, v]) => v !== "not_assessed")
                    .map(([f, v]) => (
                      <div key={f} className="fila entre">
                        <span>{FAMILIAS[f] ?? f}</span>
                        <Chip tipo={v === "appropriate" ? "demonstrated" : "aviso"}>
                          {v === "appropriate" ? "Conveniente" : "No conveniente"}
                        </Chip>
                      </div>
                    ))}
                </div>
              </Tarjeta>
            </div>

            {restricciones && (
              <Tarjeta
                titulo="Restricciones para el agente de la entidad"
                extra={
                  <Chip tipo={restricciones.usable ? "demonstrated" : "aviso"}>
                    {restricciones.usable ? `Usable · v${restricciones.profile_version}` : "No usable todavía"}
                  </Chip>
                }
              >
                <p className="pequena suave">
                  Parámetros que el agente pasa tal cual al MCP de MyInvestor y filtros posteriores sobre la ficha.
                </p>
                <pre
                  className="pequena"
                  style={{ background: "var(--c-fondo)", padding: 12, borderRadius: 12, overflowX: "auto", margin: 0 }}
                >
                  {JSON.stringify(
                    {
                      funds_query: restricciones.funds_query,
                      portfolios_query: restricciones.portfolios_query,
                      post_filters: restricciones.post_filters,
                    },
                    null,
                    2,
                  )}
                </pre>
              </Tarjeta>
            )}

            <Tarjeta titulo="Datos y evidencias" extra={<Etiqueta>Con su cita</Etiqueta>}>
              <div className="pila">
                {Object.entries(perfil.mifid).map(([campo, c], i) => (
                  <div key={campo} style={i ? { borderTop: "1px solid var(--c-borde)", paddingTop: 10 } : undefined}>
                    <div className="fila entre" style={{ flexWrap: "wrap" }}>
                      <span>{ETIQUETAS[campo] ?? campo}</span>
                      <div className="fila">
                        <strong>{mostrarValor(c.value)}</strong>
                        <Chip tipo={c.source}>{FUENTES[c.source]}</Chip>
                        {c.confidence != null && <Chip>{Math.round(c.confidence * 100)} %</Chip>}
                        {c.flags.length > 0 && <Chip tipo="aviso">alerta</Chip>}
                      </div>
                    </div>
                    {c.declared != null && c.declared !== c.value && (
                      <p className="pequena" style={{ color: "var(--c-aviso)", margin: "4px 0 0" }}>
                        Declaró «{mostrarValor(c.declared)}»
                      </p>
                    )}
                    {c.evidence.length > 0 && (
                      <button
                        className="pequena"
                        style={{ background: "none", border: 0, padding: "4px 0", color: "var(--c-acento)", textDecoration: "underline" }}
                        onClick={() => setAbierto(abierto === campo ? null : campo)}
                        aria-expanded={abierto === campo}
                      >
                        {abierto === campo ? "Ocultar evidencia" : "Ver evidencia"}
                      </button>
                    )}
                    {abierto === campo &&
                      c.evidence.map((ev, i) => (
                        <p key={i} className="pequena suave" style={{ margin: "2px 0 0" }}>
                          «{ev.quote}» · sesión {ev.session_id}
                          {ev.turn_id ? `, ${ev.turn_id}` : ""}, {ev.t[0].toFixed(1)}–{ev.t[1].toFixed(1)} s
                          {/* PENDIENTE: reproducir ev.audio_url cuando exista el clip */}
                        </p>
                      ))}
                    {c.source === "calculated" && (
                      <p className="pequena suave" style={{ margin: "2px 0 0" }}>
                        Cálculo determinista a partir de: {c.inputs.map((i) => ETIQUETAS[i] ?? i).join(", ")}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Tarjeta>
          </>
        )}
      </Contenido>
    </Marco>
  );
}
