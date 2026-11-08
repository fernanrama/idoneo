import Link from "next/link";
import { Boton, Contenido, Marco, Pie, Tarjeta } from "@/components/ui";

// Inicio de la app del banco (maqueta provisional hasta tener las pantallas de MyInvestor).
export default function Inicio() {
  return (
    <Marco>
      <header style={{ background: "var(--c-primario)", color: "var(--c-primario-texto)", padding: "28px 16px 20px" }}>
        <p className="pequena" style={{ opacity: 0.8, margin: 0 }}>Buenos días</p>
        <h1 style={{ margin: "4px 0 0" }}>Carmen</h1>
      </header>
      <Contenido>
        <Tarjeta>
          <p className="suave pequena" style={{ margin: 0 }}>Depósitos</p>
          <p style={{ fontSize: 30, fontWeight: 700, margin: "4px 0 0" }}>80.000,00 €</p>
        </Tarjeta>

        <Tarjeta destacada>
          <p className="pequena" style={{ opacity: 0.85, margin: 0 }}>Nuevo</p>
          <h2 style={{ marginTop: 4 }}>Tu perfil inversor, hablando</h2>
          <p style={{ opacity: 0.9 }}>
            Antes de invertir necesitamos conocerte. En vez de un test de casillas, cuéntanoslo en unos 7 minutos, con
            tu voz o por escrito.
          </p>
          <Link href="/onboarding">
            <Boton>Empezar</Boton>
          </Link>
        </Tarjeta>
      </Contenido>
      <Pie>
        <Link href="/entidad/carmen-68" className="pequena suave" style={{ textAlign: "center" }}>
          Vista de la entidad (demo)
        </Link>
        <p className="pequena suave" style={{ textAlign: "center", margin: 0 }}>
          Prototipo de feature · no es un producto oficial · datos simulados
        </p>
      </Pie>
    </Marco>
  );
}
