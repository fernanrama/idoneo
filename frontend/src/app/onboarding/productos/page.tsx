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
import { Busquedas, EnRevision } from "@/components/PerfilCambios";
import rv from "@/components/revision.module.css";
import type { Restricciones } from "@/lib/tipos";

const euros = (v: number) => `${v.toLocaleString("es-ES", { maximumFractionDigits: 0, useGrouping: "always" })} €`;

/** Los filtros que se aplican sobre cada ficha, en palabras del cliente. */
function filtroLegible(f: Restricciones["post_filters"][number]): string | null {
  if (f.field === "redemption_lag_days") return `Que puedas recuperar tu dinero en ${f.value} días como mucho`;
  if (f.field === "fixed_income_term") return "En renta fija, solo a corto plazo, porque lo necesitarás pronto";
  if (f.field === "min_initial" && typeof f.value === "number") return `Que se pueda empezar con ${euros(f.value)} o menos`;
  if (f.field === "sustainability_article") return "Solo fondos con objetivo sostenible (artículo 9)";
  if (f.field === "top_sectors") return "Sin los sectores que nos pediste evitar";
  return null;
}

/**
 * Productos compatibles con el perfil.
 * IMPORTANTE: los términos del MCP público de MyInvestor prohíben llamarlo por programa, cachear o
 * redistribuir su catálogo (ver docs/diseno/04-mcp-myinvestor.md). Esta app NO debe consultarlo por código.
 * El filtrado real lo hace el agente de la entidad (Claude con el MCP de MyInvestor como conector, rol D).
 * Mostrar aquí productos reales requiere permiso explícito de MyInvestor; no se inventan productos.
 */
export default function Productos() {
  const { clientId } = useOnboarding();
  const { perfil, restricciones: r, revision, error } = usePerfil(clientId);
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

            {r.pending_review && <EnRevision p={r.pending_review} servida={r.profile_version} revision={revision} />}

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
                  {r.post_filters.map(filtroLegible).filter(Boolean).map((t) => (
                    <li key={t} className={s.fila}>
                      <div className={s.filaBoton}>
                        <span className={s.filaTexto}>
                          <span className={s.filaTitulo}>Además</span>
                          <span className={s.filaValor}>{t}</span>
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
                <Hipoteca perfil={perfil} />
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

            <Revela como="section" className={s.tarjeta}>
              <h2>Qué buscaremos y qué no</h2>
              <p className={s.suave} style={{ marginTop: 0 }}>
                El asistente de la entidad solo busca en el catálogo lo que encaja contigo. Lo que no busca, te explicamos por qué.
              </p>
              <Busquedas r={r} perfil={perfil} />
            </Revela>

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

/** La hipoteca se pregunta aparte: no cuenta como deuda que reste, porque su cuota ya va en los gastos fijos. */
function Hipoteca({ perfil }: { perfil: NonNullable<ReturnType<typeof usePerfil>["perfil"]> }) {
  const h = perfil.mifid["financial.mortgage_eur"]?.value;
  if (typeof h !== "number" || h <= 0) return null;
  return (
    <p className={`${s.nota} ${rv.notaHipoteca}`}>
      <strong>¿Y tu hipoteca?</strong> Te quedan {euros(h)}. No reduce lo que puedes invertir: su cuota ya está dentro de
      tus gastos fijos al mes, así que no la contamos dos veces.
    </p>
  );
}
