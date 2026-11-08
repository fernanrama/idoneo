"use client";

import { Cabecera, Chip, Contenido, Marco, Tarjeta } from "@/components/ui";
import { FAMILIAS } from "@/lib/bloques";
import { useOnboarding } from "@/lib/onboarding";
import { usePerfil } from "@/lib/usePerfil";

/**
 * Productos compatibles con el perfil.
 * IMPORTANTE: los términos del MCP público de MyInvestor prohíben llamarlo por programa, cachear o
 * redistribuir su catálogo (ver docs/proyecto/05_MCP_MYINVESTOR.md). Esta app NO debe consultarlo por código.
 * El filtrado real lo hace el agente de la entidad (Claude con el MCP de MyInvestor como conector, rol D).
 * Mostrar aquí productos reales requiere permiso explícito de MyInvestor; no se inventan productos.
 */
export default function Productos() {
  const { clientId } = useOnboarding();
  const { perfil, restricciones: r, error } = usePerfil(clientId);
  const s = perfil?.assessments.suitability;

  return (
    <Marco>
      <Cabecera titulo="Productos para ti" />
      <Contenido>
        {error && <p role="alert">No se han podido cargar las restricciones.</p>}
        {perfil && s && r && (
          <>
            <Tarjeta>
              <h2>Filtros de tu perfil</h2>
              <div className="pila">
                <div className="fila entre">
                  <span>Riesgo máximo</span>
                  <strong>{s.max_sri ?? "—"} / 7</strong>
                </div>
                <div className="fila entre">
                  <span>Perfil</span>
                  <strong>{s.risk_profile?.toLowerCase().replace("_", " ") ?? "—"}</strong>
                </div>
                <div className="fila entre">
                  <span>Criterios sostenibles</span>
                  <strong>{r.funds_query.esg_only ? "sí" : "no es necesario"}</strong>
                </div>
              </div>
            </Tarjeta>
            <Tarjeta>
              <h2>Puedes comprar por tu cuenta</h2>
              <div className="pila">
                {Object.entries(perfil.assessments.appropriateness)
                  .filter(([, v]) => v !== "not_assessed")
                  .map(([f, v]) => (
                    <div key={f} className="fila entre">
                      <span>{FAMILIAS[f] ?? f}</span>
                      <Chip tipo={v === "appropriate" ? "demonstrated" : "aviso"}>
                        {v === "appropriate" ? "Sí" : "Con aviso previo"}
                      </Chip>
                    </div>
                  ))}
              </div>
            </Tarjeta>
            <Tarjeta>
              <div className="fila entre">
                <h2 style={{ margin: 0 }}>Catálogo</h2>
                <Chip tipo="aviso">Pendiente</Chip>
              </div>
              <p className="suave" style={{ marginTop: 8 }}>
                Con estos filtros, el asistente de la entidad busca en el catálogo los fondos que encajan contigo.
              </p>
            </Tarjeta>
          </>
        )}
      </Contenido>
    </Marco>
  );
}
