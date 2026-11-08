"use client";

import { use, useState } from "react";
import { AlertaTarjeta, Boton, Cabecera, Chip, Contenido, Marco, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { ETIQUETAS, FUENTES, mostrarValor } from "@/lib/bloques";
import { usePerfil } from "@/lib/usePerfil";

const ESTADOS: Record<string, string> = {
  draft: "Borrador",
  validated: "Validado",
  active: "Activo · apto para recomendar",
  review_pending: "Pendiente de revisión",
};

// Vista mínima de la entidad: perfil con evidencias y validación humana. No es un panel de banquero completo.
export default function VistaEntidad({ params }: { params: Promise<{ cid: string }> }) {
  const { cid } = use(params);
  const { perfil, restricciones, error, recargar } = usePerfil(cid);
  const [abierto, setAbierto] = useState<string | null>(null);
  const [validando, setValidando] = useState(false);

  const validar = async () => {
    setValidando(true);
    try {
      await api.validar(cid, "asesor-demo");
      await recargar();
    } finally {
      setValidando(false);
    }
  };

  return (
    <Marco ancho>
      <Cabecera titulo={`Perfil de cliente · ${cid}`} />
      <Contenido>
        {error && <p role="alert">{error}</p>}
        {perfil && (
          <>
            <div className="fila entre" style={{ flexWrap: "wrap" }}>
              <div className="fila">
                <Chip tipo={perfil.status === "active" ? "demonstrated" : "aviso"}>{ESTADOS[perfil.status]}</Chip>
                <span className="pequena suave">
                  Versión {perfil.version} · {perfil.reason}
                </span>
              </div>
              {perfil.status !== "active" && (
                <Boton style={{ width: "auto" }} onClick={validar} disabled={validando}>
                  {validando ? "Validando…" : "Validar perfil"}
                </Boton>
              )}
            </div>

            {perfil.alerts.filter((a) => a.status === "open").map((a) => <AlertaTarjeta key={a.id} alerta={a} />)}

            {restricciones && (
              <Tarjeta>
                <h2>Restricciones para cualquier recomendación</h2>
                <p>
                  Riesgo máximo <strong>{restricciones.max_risk_indicator ?? "—"}/7</strong> · apto para recomendar:{" "}
                  <strong>{restricciones.eligible ? "sí" : "no"}</strong>
                </p>
                <ul className="pequena suave" style={{ margin: 0, paddingLeft: 18 }}>
                  {restricciones.rationale.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </Tarjeta>
            )}

            <Tarjeta>
              <h2>Datos y evidencias</h2>
              <div className="pila">
                {Object.entries(perfil.mifid).map(([campo, c]) => (
                  <div key={campo} style={{ borderTop: "1px solid var(--c-borde)", paddingTop: 10 }}>
                    <div className="fila entre" style={{ flexWrap: "wrap" }}>
                      <span>{ETIQUETAS[campo] ?? campo}</span>
                      <div className="fila">
                        <strong>{mostrarValor(c.value)}</strong>
                        <Chip tipo={c.source}>{FUENTES[c.source]}</Chip>
                        {c.confidence != null && <Chip>{Math.round(c.confidence * 100)} %</Chip>}
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
                        style={{ background: "none", border: 0, padding: "4px 0", color: "var(--c-primario)", textDecoration: "underline" }}
                        onClick={() => setAbierto(abierto === campo ? null : campo)}
                        aria-expanded={abierto === campo}
                      >
                        {abierto === campo ? "Ocultar evidencia" : "Ver evidencia"}
                      </button>
                    )}
                    {abierto === campo &&
                      c.evidence.map((ev, i) => (
                        <p key={i} className="pequena suave" style={{ margin: "2px 0 0" }}>
                          «{ev.quote}» · sesión {ev.session_id}, {ev.t_start.toFixed(1)}–{ev.t_end.toFixed(1)} s
                          {/* PENDIENTE: reproducir el clip de audio cuando exista /api/sessions/{sid}/audio */}
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
