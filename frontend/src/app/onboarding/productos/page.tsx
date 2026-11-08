"use client";

import { Cabecera, Chip, Contenido, Marco, Tarjeta } from "@/components/ui";
import { useOnboarding } from "@/lib/onboarding";
import { usePerfil } from "@/lib/usePerfil";

const LIQUIDEZ: Record<string, string> = { high: "alta", medium: "media", low: "baja" };

/**
 * Productos compatibles con el perfil.
 * PENDIENTE (Alejandro, rol D): listado real del catálogo de MyInvestor filtrado con estas restricciones vía MCP.
 * Hasta entonces se muestran las restricciones que se aplicarán; no se inventan productos.
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
                Aquí aparecerán los fondos del catálogo de MyInvestor que cumplen tus filtros.
              </p>
            </Tarjeta>
          </>
        )}
      </Contenido>
    </Marco>
  );
}
