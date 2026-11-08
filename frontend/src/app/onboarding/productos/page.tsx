"use client";

import { Cabecera, Chip, Contenido, Marco, Tarjeta } from "@/components/ui";
import { useOnboarding } from "@/lib/onboarding";
import { usePerfil } from "@/lib/usePerfil";

const LIQUIDEZ: Record<string, string> = { high: "alta", medium: "media", low: "baja" };

/**
 * Productos compatibles con el perfil.
 * IMPORTANTE: los términos del MCP público de MyInvestor prohíben llamarlo por programa, cachear o
 * redistribuir su catálogo (ver docs/proyecto/05_MCP_MYINVESTOR.md). Esta app NO debe consultarlo por código.
 * El filtrado real se hace con Claude usando el MCP de MyInvestor como conector (rol D).
 * Mostrar aquí productos reales requiere permiso explícito de MyInvestor; no se inventan productos.
 */
export default function Productos() {
  const { clientId } = useOnboarding();
  const { restricciones: r, error } = usePerfil(clientId);

  return (
    <Marco>
      <Cabecera titulo="Productos para ti" />
      <Contenido>
        {error && <p role="alert">No se han podido cargar las restricciones.</p>}
        {r && (
          <>
            <Tarjeta>
              <h2>Filtros de tu perfil</h2>
              <div className="pila">
                <div className="fila entre">
                  <span>Riesgo máximo</span>
                  <strong>{r.max_risk_indicator ?? "—"} / 7</strong>
                </div>
                <div className="fila entre">
                  <span>Plazo</span>
                  <strong>{r.horizon_years ?? "—"} años</strong>
                </div>
                <div className="fila entre">
                  <span>Necesidad de liquidez</span>
                  <strong>{r.liquidity_need ? LIQUIDEZ[r.liquidity_need] : "—"}</strong>
                </div>
                <div className="fila entre">
                  <span>Criterios sostenibles</span>
                  <strong>{r.esg_required ? "sí" : "no es necesario"}</strong>
                </div>
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
