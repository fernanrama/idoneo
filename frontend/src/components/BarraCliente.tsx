import Link from "next/link";
import s from "./cliente.module.css";

const PASOS = ["Conversación", "Tu perfil", "Productos"];

/** Barra de las pantallas claras del cliente, con los tres pasos del recorrido. */
export function BarraCliente({ paso }: { paso: 1 | 2 | 3 }) {
  return (
    <header className={s.barra}>
      <div className={s.barraCaja}>
        <Link href="/" className={s.marca}>
          <span className={s.logo} aria-hidden="true" />
          Idóneo
        </Link>
        <ol className={s.pasos} aria-label="Pasos">
          {PASOS.map((p, i) => (
            <li
              key={p}
              data-n={i + 1}
              className={i + 1 < paso ? s.hecho : i + 1 === paso ? s.actual : ""}
              aria-current={i + 1 === paso ? "step" : undefined}
            >
              {p}
            </li>
          ))}
        </ol>
      </div>
    </header>
  );
}
