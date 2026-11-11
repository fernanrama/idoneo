"use client";

import Link from "next/link";
import { ETIQUETAS, FUENTES, mostrarValor } from "@/lib/bloques";
import type { Fact, Perfil } from "@/lib/tipos";
import s from "./panel.module.css";
import { Icono } from "./visual";

const PERFILES: Record<string, string> = {
  CONSERVADOR: "Conservador",
  MODERADO: "Moderado",
  DINAMICO: "Dinámico",
  AGRESIVO: "Agresivo",
  MUY_AGRESIVO: "Muy agresivo",
};
export const nombrePerfil = (p: string | null | undefined) => (p ? (PERFILES[p] ?? p) : "—");

const tieneValor = (f: Fact) => f.value !== null && f.value !== undefined;

/**
 * Lo que recibe la entidad mientras el cliente habla: cada dato entra con su fuente y su cita;
 * la alerta de lo declarado frente a lo demostrado llega con una sacudida; al final, el perfil calculado.
 * El dato más reciente brilla hasta que llega el siguiente.
 */
export function PanelVivo({ perfil, enMarcha }: { perfil: Perfil | null; enMarcha: boolean }) {
  const datos = perfil
    ? Object.entries(perfil.mifid)
        .filter(([ruta, f]) => tieneValor(f) && !ruta.startsWith("disclosures."))
        .sort(([, a], [, b]) => b.updated_at.localeCompare(a.updated_at))
    : [];
  const ultimo = datos[0]?.[1].updated_at;
  const total = perfil ? Object.keys(perfil.mifid).filter((r) => !r.startsWith("disclosures.")).length : 0;
  const alertas = perfil?.alerts.filter((a) => a.status === "open") ?? [];
  const conAlerta = new Set(alertas.map((a) => a.path));
  const su = perfil?.assessments.suitability;
  const estado =
    perfil?.status === "active" ? "validado" : su?.complete ? "listo para validar" : datos.length ? "en construcción" : "esperando datos";

  return (
    <section className={s.panel} aria-label="Lo que recibe la entidad">
      <div className={s.cabecera}>
        <span className="mono">Así se construye el perfil</span>
        {enMarcha && (
          <span className={s.sinc}>
            <span aria-hidden="true" />
            Sincronizado
          </span>
        )}
        {perfil && (
          <span className={s.cuenta}>
            Datos <strong>{datos.length}</strong> de {total}
          </span>
        )}
      </div>
      <h1 className={s.titulo}>
        <span className={s.grad}>Perfil inversor,</span> {estado}
      </h1>

      {!perfil || datos.length === 0 ? (
        <div className={s.vacio}>
          <div className={s.puntos} aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <p style={{ margin: 0 }}>
            {enMarcha ? "Escuchando. Los datos aparecerán aquí con su frase exacta." : "Cuando el cliente empiece a hablar, su perfil se irá construyendo aquí."}
          </p>
        </div>
      ) : (
        <>
          {alertas
            .slice()
            .reverse()
            .map((a) => (
              <div key={a.id} className={s.alerta} role="alert">
                {Icono.aviso}
                <div>
                  <strong>{a.flag === "declared_vs_demonstrated" ? "Lo que dice frente a lo que demuestra" : "Revisar con el cliente"}</strong>
                  <p>{a.message}</p>
                  {a.evidence[0]?.quote && <p className={s.cita}>«{a.evidence[0].quote}»</p>}
                </div>
              </div>
            ))}

          {su?.complete && (
            <div className={s.resumen}>
              <div style={{ flex: "1 1 200px" }}>
                <span className="mono">Los números los calcula código, no la IA</span>
                <strong>
                  {nombrePerfil(su.risk_profile)} · riesgo máximo {su.max_sri ?? "—"} de 7
                </strong>
              </div>
              <div className={s.sri} role="img" aria-label={`Riesgo máximo ${su.max_sri ?? "sin definir"} de 7`}>
                {Array.from({ length: 7 }, (_, i) => (
                  <span key={i} className={su.max_sri != null && i < su.max_sri ? s.lleno : ""} />
                ))}
              </div>
              {!enMarcha && (
                <Link href="/onboarding/perfil" className={s.botonClaro}>
                  Ver el perfil de Carmen →
                </Link>
              )}
            </div>
          )}

          <div className={s.rejilla}>
            {datos.map(([ruta, f]) => (
              <TarjetaDato key={ruta} ruta={ruta} f={f} nuevo={f.updated_at === ultimo} alerta={conAlerta.has(ruta)} />
            ))}
          </div>

          {su && !su.complete && su.missing.length > 0 && (
            <p className={s.pendientes}>Falta por saber: {su.missing.map((m) => ETIQUETAS[m] ?? m).join(", ")}.</p>
          )}
        </>
      )}
    </section>
  );
}

function TarjetaDato({ ruta, f, nuevo, alerta }: { ruta: string; f: Fact; nuevo: boolean; alerta: boolean }) {
  const cita = f.evidence[0]?.quote;
  return (
    <div className={`${s.dato} ${nuevo ? s.nuevo : ""} ${alerta ? s.conAlerta : ""}`}>
      <div className={s.datoCab}>
        <span>{ETIQUETAS[ruta] ?? ruta}</span>
        <span className={`${s.chip} ${s[`chip_${f.source}`] ?? ""}`}>{FUENTES[f.source] ?? f.source}</span>
      </div>
      <div className={s.valor}>{valorConUnidad(ruta, f.value)}</div>
      {f.declared != null && f.declared !== f.value && <span className={s.declaro}>Declaró «{mostrarValor(f.declared)}»</span>}
      {cita ? (
        <p className={s.cita}>«{cita}»</p>
      ) : f.source === "calculated" ? (
        <p className={s.cita}>Cálculo a partir de: {f.inputs.map((i) => ETIQUETAS[i] ?? i).join(", ")}</p>
      ) : null}
    </div>
  );
}

/** Euros con separador de miles y meses con una cifra decimal; el resto, como lo muestra la app. */
export function valorConUnidad(ruta: string, v: unknown) {
  if (typeof v === "number" && ruta.endsWith("_eur")) return `${v.toLocaleString("es-ES", { maximumFractionDigits: 0 })} €`;
  if (typeof v === "number" && ruta.endsWith("_months")) return `${v.toLocaleString("es-ES", { maximumFractionDigits: 1 })} meses`;
  if (typeof v === "number" && ruta.endsWith("horizon_years")) return `${v.toLocaleString("es-ES")} años`;
  return mostrarValor(v);
}
