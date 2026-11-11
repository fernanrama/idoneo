"use client";

import { nombrePerfil } from "@/components/PanelVivo";
import { BUSQUEDAS, motivoBloqueo, nombreDato, porQueNo, valorLegible } from "@/lib/revision";
import type { Comparacion, Perfil, Restricciones, Revision, RevisionPendiente } from "@/lib/tipos";
import s from "./revision.module.css";

type Tono = "cliente" | "entidad";

/** Mini medidor de 7 tramos para el antes y el después. */
function Sri({ n }: { n: number | null }) {
  return (
    <span className={s.sriMini} role="img" aria-label={`Riesgo máximo ${n ?? "sin definir"} de 7`}>
      {Array.from({ length: 7 }, (_, i) => (
        <i key={i} className={n != null && i < n ? s.sriLleno : ""} style={{ animationDelay: `${0.3 + i * 0.05}s` }} />
      ))}
    </span>
  );
}

/**
 * Antes y después: último perfil validado frente al último guardado. Cada dato con lo que constaba, lo que
 * consta ahora y la frase que lo justifica; arriba, si cambian, el perfil de riesgo y el SRI.
 */
export function AntesDespues({ c, tono = "cliente" }: { c: Comparacion; tono?: Tono }) {
  const cambiaPerfil = c.perfil_antes !== c.perfil_ahora || c.sri_antes !== c.sri_ahora;
  const entidad = tono === "entidad";
  return (
    <section className={`${s.ad} ${entidad ? s.tonoEntidad : ""}`} aria-labelledby="t-antes">
      <header className={s.adCabecera}>
        <div>
          <h2 id="t-antes">{entidad ? "Antes y después" : "Lo que ha cambiado"}</h2>
          <p>
            {entidad
              ? `Versión ${c.desde_version} validada frente a la versión ${c.hasta_version}, sin validar.`
              : "Lo que teníamos anotado y lo que nos has contado ahora. Una persona del banco lo revisará."}
          </p>
        </div>
        <span className={s.adVersiones} aria-hidden="true">
          <b>v{c.desde_version}</b>
          <i />
          <b>v{c.hasta_version}</b>
        </span>
      </header>

      <div className={s.adPerfil}>
        <div className={s.adLado}>
          <span>Antes</span>
          <strong>Perfil {nombrePerfil(c.perfil_antes).toLowerCase()}</strong>
          <Sri n={c.sri_antes} />
        </div>
        <span className={`${s.adFlecha} ${cambiaPerfil ? s.adFlechaViva : ""}`} aria-hidden="true" />
        <div className={`${s.adLado} ${s.adAhora}`}>
          <span>Ahora</span>
          <strong>Perfil {nombrePerfil(c.perfil_ahora).toLowerCase()}</strong>
          <Sri n={c.sri_ahora} />
        </div>
        <p className={s.adVeredicto}>
          {cambiaPerfil
            ? `El riesgo máximo pasa de ${c.sri_antes ?? "—"} a ${c.sri_ahora ?? "—"} de 7.`
            : "El perfil de riesgo se mantiene."}
        </p>
      </div>

      {c.cambios.length > 0 && (
        <ol className={s.adFilas}>
          {c.cambios.map((x, i) => {
            const igual = JSON.stringify(x.antes) === JSON.stringify(x.ahora);
            const nuevo = x.antes == null;
            return (
              <li key={x.path} className={s.adFila} style={{ animationDelay: `${0.1 + i * 0.08}s` }}>
                <span className={s.adNombre}>{nombreDato(x.path)}</span>
                <span className={s.adValores}>
                  {!igual && <s className={s.adViejo}>{nuevo ? "Sin dato" : valorLegible(x.path, x.antes)}</s>}
                  {!igual && <span className={s.adMini} aria-label="pasa a" />}
                  <b className={s.adNuevo} style={{ animationDelay: `${0.35 + i * 0.08}s` }}>{valorLegible(x.path, x.ahora)}</b>
                  <em className={igual ? s.adIgual : nuevo ? s.adNuevoChip : s.adCambia}>
                    {igual ? "Confirmado" : nuevo ? "Nuevo" : "Cambia"}
                  </em>
                </span>
                {x.cita && <q className={s.adCita}>{x.cita}</q>}
              </li>
            );
          })}
        </ol>
      )}

      {c.efectos.length > 0 && (
        <div className={s.adEfectos}>
          <span>{entidad ? "Qué cambia para el agente" : "Qué cambia en lo que te podemos ofrecer"}</span>
          <ul>
            {c.efectos.map((e, i) => (
              <li key={e} style={{ animationDelay: `${0.4 + i * 0.08}s` }}>{e}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

/** Qué busca el agente de la entidad en el catálogo y qué no, y por qué. */
export function Busquedas({ r, perfil, tono = "cliente" }: { r: Restricciones; perfil: Perfil; tono?: Tono }) {
  const bloqueadas = new Set(r.blocked_searches ?? []);
  const sri = perfil.assessments.suitability.max_sri;
  const siDetalle: Record<string, string> = {
    funds: `Con un riesgo de ${sri ?? "—"} sobre 7 como máximo.`,
    portfolios: `Las de perfil ${nombrePerfil(perfil.assessments.suitability.risk_profile).toLowerCase()}.`,
    etfs: `El catálogo no da su riesgo: se comprueba en cada ficha que no pase de ${sri ?? "—"}.`,
    stocks: `Solo si su riesgo no pasa de ${sri ?? "—"} sobre 7.`,
  };
  return (
    <div className={`${s.busquedas} ${tono === "entidad" ? s.tonoEntidad : ""}`}>
      {BUSQUEDAS.map((b, i) => {
        const no = bloqueadas.has(b.code);
        return (
          <div key={b.code} className={`${s.busqueda} ${no ? s.busquedaNo : ""}`} style={{ animationDelay: `${i * 0.07}s` }}>
            <strong>
              <span className={no ? s.no : s.si} aria-hidden="true">{no ? "✕" : "✓"}</span>
              {b.nombre}
              <span className="oculto-visual">{no ? ": no se buscan" : ": sí se buscan"}</span>
            </strong>
            <p>{b.detalle}</p>
            <p className={no ? s.busquedaPorQue : s.busquedaSi}>{no ? (tono === "entidad" ? (motivoBloqueo(b.code, r) ?? porQueNo(b.code, r, perfil)) : porQueNo(b.code, r, perfil)) : siDetalle[b.code]}</p>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Hay una versión posterior sin validar: se sigue sirviendo la última validada, y el agente sabe qué datos
 * no debe dar por buenos. Con la revisión del cliente abierta, enseña también cómo va.
 */
export function EnRevision({ p, servida, revision, tono = "cliente" }: { p: RevisionPendiente; servida: number; revision?: Revision | null; tono?: Tono }) {
  const entidad = tono === "entidad";
  const abierta = revision?.open ? revision : null;
  const hechas = abierta ? abierta.questions.length - abierta.remaining : 0;
  return (
    <section className={s.enRevision} role="status">
      <span className={s.enRevisionIcono} aria-hidden="true">!</span>
      <div className={s.enRevisionTexto}>
        <h3>{entidad ? `Datos en revisión · la versión ${p.latest_version} está sin validar` : "Tu perfil se está actualizando"}</h3>
        <p>
          {entidad
            ? `El agente sigue recibiendo la versión ${servida}, la última validada, con estos datos marcados: no debe apoyarse en ellos hasta que valides los cambios.`
            : `Mientras una persona del banco revisa tus cambios, se usa tu perfil anterior y quien te proponga productos sabe que estos datos están en revisión:`}
        </p>
        {p.paths.length > 0 && (
          <div className={s.rutas}>
            {p.paths.map((r, i) => (
              <span key={r} style={{ animationDelay: `${i * 0.05}s` }}>{nombreDato(r)}</span>
            ))}
          </div>
        )}
        {abierta && (
          <div className={s.revEnCurso}>
            <span>
              {entidad ? "Microentrevista pedida por el cliente" : "Tu revisión"}: {abierta.reasons.map((m) => m.titulo.toLowerCase()).join(", ")}
            </span>
            <span className={s.progreso} aria-label={`${hechas} de ${abierta.questions.length} preguntas contestadas`}>
              {abierta.questions.map((q) => <i key={q.path} className={q.respondida ? s.hecha : ""} />)}
            </span>
            <span>{hechas} de {abierta.questions.length}</span>
          </div>
        )}
      </div>
    </section>
  );
}
