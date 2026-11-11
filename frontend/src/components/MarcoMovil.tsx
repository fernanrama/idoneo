import { SelloPowered } from "./SelloPowered";
import s from "./marco.module.css";

/**
 * Marco de teléfono que simula la app de una entidad: su barra arriba, el módulo de idóneo dentro
 * y el sello «Powered by idóneo» al pie. En pantallas estrechas el marco desaparece y queda el contenido.
 */
export function MarcoMovil({ entidad, children }: { entidad: "A" | "B"; children: React.ReactNode }) {
  return (
    <div className={`${s.marco} ${entidad === "A" ? s.entidadA : s.entidadB}`}>
      <div className={s.pantalla}>
        <div className={s.barra} aria-hidden="true">
          <span className={s.muesca} />
          <span className={s.barraNombre}>
            <i />
            Tu entidad
          </span>
          <span className={s.barraSeccion}>Perfil inversor</span>
        </div>
        <div className={s.contenido}>{children}</div>
        <div className={s.pie}>
          <span>Invertir empieza por escucharte.</span>
          <SelloPowered fondo="oscuro" alto={18} />
        </div>
      </div>
    </div>
  );
}
