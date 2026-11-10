"use client";

import Link from "next/link";
import { BarraCliente } from "@/components/BarraCliente";
import { nombrePerfil } from "@/components/PanelVivo";
import { Revela } from "@/components/Revela";
import s from "@/components/cliente.module.css";
import { Icono } from "@/components/visual";
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
  const su = perfil?.assessments.suitability;

  return (
    <div className={s.raiz}>
      <BarraCliente paso={3} />
      <main className={s.caja}>
        {error && (
          <p role="alert" className={s.error}>
            No hemos podido cargar tus filtros. Inténtalo de nuevo en un momento.
          </p>
        )}
        {!perfil && !error && <div className={s.cargando} aria-label="Cargando" />}
        {perfil && su && r && (
          <>
            <section className={s.hero} style={{ minHeight: 0 }}>
              <div className={s.heroTexto}>
                <h1>
                  Productos <span className={s.grad}>para ti</span>
                </h1>
                <p>Estos son los filtros que tu perfil pone a cualquier producto que te ofrezcamos.</p>
              </div>
            </section>

            <div className={s.rejilla}>
              <Revela como="section" className={s.tarjeta}>
                <h2>Filtros de tu perfil</h2>
                <ul className={s.filas}>
                  <li className={s.fila}>
                    <div className={s.filaBoton}>
                      <span className={s.filaTexto}>
                        <span className={s.filaTitulo}>Riesgo máximo</span>
                        <span className={s.filaValor}>{su.max_sri ?? "—"} sobre 7</span>
                      </span>
                    </div>
                  </li>
                  <li className={s.fila}>
                    <div className={s.filaBoton}>
                      <span className={s.filaTexto}>
                        <span className={s.filaTitulo}>Perfil</span>
                        <span className={s.filaValor}>{nombrePerfil(su.risk_profile)}</span>
                      </span>
                    </div>
                  </li>
                  <li className={s.fila}>
                    <div className={s.filaBoton}>
                      <span className={s.filaTexto}>
                        <span className={s.filaTitulo}>Criterios sostenibles</span>
                        <span className={s.filaValor}>{r.funds_query.esg_only ? "Sí" : "No es necesario"}</span>
                      </span>
                    </div>
                  </li>
                </ul>
              </Revela>

              <Revela como="section" className={s.tarjeta} retraso={0.12}>
                <h2>Puedes contratar por tu cuenta</h2>
                <ul className={s.filas}>
                  {Object.entries(perfil.assessments.appropriateness)
                    .filter(([, v]) => v !== "not_assessed")
                    .map(([f, v]) => (
                      <li key={f} className={s.fila}>
                        <div className={s.filaBoton}>
                          <span className={s.filaTexto}>
                            <span className={s.filaValor}>{(FAMILIAS[f] ?? f).replace(/^./, (c) => c.toUpperCase())}</span>
                          </span>
                          <span className={`${s.estado} ${v === "appropriate" ? s.estadoOk : ""}`}>
                            {v === "appropriate" ? "Sí" : "Con aviso previo"}
                          </span>
                        </div>
                      </li>
                    ))}
                </ul>
              </Revela>
            </div>

            <Revela como="section" className={`${s.tarjeta} ${s.siguiente}`}>
              <div className={s.siguienteIcono} aria-hidden="true">
                {Icono.check}
              </div>
              <div style={{ flex: "1 1 280px" }}>
                <h2>Qué pasa ahora</h2>
                <p className={s.suave}>
                  Con estos filtros, el asistente de la entidad busca en su catálogo los productos que encajan contigo. Nosotros
                  no elegimos productos: solo nos aseguramos de que encajen con tu perfil.
                </p>
              </div>
              <div className={s.botones}>
                <Link href="/onboarding/perfil" className={s.botonSec}>
                  Volver a mi perfil
                </Link>
              </div>
            </Revela>
          </>
        )}
      </main>
    </div>
  );
}
