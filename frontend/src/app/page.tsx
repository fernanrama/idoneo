import Link from "next/link";
import {
  Boton,
  Hero,
  ListaCheck,
  Marca,
  Marco,
  Pie,
  Tarjeta,
} from "@/components/ui";
import s from "@/components/ui.module.css";

// Inicio de la app del banco, con el aspecto de la web pública de MyInvestor (sin su logo). Datos simulados.
export default function Inicio() {
  return (
    <Marco>
      <header className={s.cabecera}>
        <Marca />
      </header>
      <main>
        <Hero>
          <p
            className="pequena"
            style={{ margin: 0, fontWeight: 700, color: "var(--c-primario)" }}
          >
            Hola, Carmen
          </p>
          <h1 style={{ margin: "6px 0 12px" }}>Tu perfil inversor, hablando</h1>
          <p>
            Antes de invertir necesitamos conocerte. Sin test de casillas:
            cuéntanoslo con tu voz o por escrito.
          </p>
          <ListaCheck
            items={[
              <>
                <strong>Unos 7 minutos.</strong> Puedes parar y seguir luego.
              </>,
              <>
                <strong>Con tus palabras.</strong> Si algo no lo sabes, dilo.
              </>,
              <>
                <strong>Revisado por una persona</strong> del banco antes de
                usarse.
              </>,
            ]}
          />
          <div style={{ marginTop: 22 }}>
            <Link href="/onboarding">
              <Boton style={{ width: "auto", paddingInline: 28 }}>
                Empezar
              </Boton>
            </Link>
          </div>
        </Hero>
        <div className={s.contenido}>
          <Tarjeta>
            <p className="suave pequena" style={{ margin: 0, fontWeight: 600 }}>
              Cuenta y depósitos
            </p>
            <p
              style={{
                fontSize: 30,
                fontWeight: 800,
                margin: "4px 0 0",
                letterSpacing: "-0.02em",
              }}
            >
              80.000,00 €
            </p>
          </Tarjeta>
        </div>
      </main>
      <Pie>
        <Link
          href="/entidad/carmen-68"
          className="pequena"
          style={{
            textAlign: "center",
            color: "var(--c-primario)",
            fontWeight: 700,
          }}
        >
          Vista de la entidad (demo)
        </Link>
        <p className="pequena suave" style={{ textAlign: "center", margin: 0 }}>
          Prototipo de feature · no es un producto oficial · datos simulados
        </p>
      </Pie>
    </Marco>
  );
}
