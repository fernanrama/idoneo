import Link from "next/link";
import s from "./cliente.module.css";

const PASOS = [
  { nombre: "Conversación", href: "/onboarding/entrevista" },
  { nombre: "Tu perfil", href: "/onboarding/perfil" },
  { nombre: "Productos", href: "/onboarding/productos" },
];

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
              key={p.nombre}
              data-n={i + 1}
              className={i + 1 < paso ? s.hecho : i + 1 === paso ? s.actual : ""}
              aria-current={i + 1 === paso ? "step" : undefined}
            >
              {i + 1 === paso ? p.nombre : <Link href={p.href}>{p.nombre}</Link>}
            </li>
          ))}
        </ol>
      </div>
    </header>
  );
}
