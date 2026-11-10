"use client";

import { Esfera3D, type Paleta } from "./Esfera3D";
import s from "./formas.module.css";

export const PALETA_CLIENTE: Paleta = ["#0038c8", "#4f86ff", "#c4e2ff"];
export const PALETA_ENTIDAD: Paleta = ["#7a1fa8", "#6b4ef0", "#ff9bd6"];

/**
 * El perfil como objeto: la misma esfera 3D del entrevistador, con los rasgos del perfil flotando
 * alrededor y dos órbitas. Decorativa: la información está también en el texto de la página.
 */
export function OrbePerfil({ rasgos, paleta = PALETA_CLIENTE, tono = "cliente" }: { rasgos: string[]; paleta?: Paleta; tono?: "cliente" | "entidad" }) {
  return (
    <div className={`${s.orbeCaja} ${tono === "entidad" ? s.entidad : ""}`} aria-hidden="true">
      <div className={s.halo} />
      <div className={`${s.orbita} ${s.orbita1}`}>
        <i />
      </div>
      <div className={`${s.orbita} ${s.orbita2}`}>
        <i />
      </div>
      <div className={s.orbeSombra} />
      <div className={s.orbe}>
        <div className={s.respaldo} />
        <Esfera3D paleta={paleta} velocidad={0.6} energia={0.6} style={{ position: "absolute", inset: 0 }} />
      </div>
      {rasgos.slice(0, 4).map((r, i) => (
        <span key={r} className={`${s.rasgo} ${s[`r${i}`]}`}>
          <i />
          {r}
        </span>
      ))}
    </div>
  );
}
