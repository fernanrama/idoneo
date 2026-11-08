"use client";

import Link from "next/link";
import { AlertaTarjeta, Boton, Cabecera, Contenido, Marco, Pie, Tarjeta } from "@/components/ui";
import { mostrarValor } from "@/lib/bloques";
import { useOnboarding } from "@/lib/onboarding";
import { usePerfil } from "@/lib/usePerfil";

// Resumen para el cliente, en lenguaje claro. No es un informe para el banquero.
export default function MiPerfil() {
  const { clientId } = useOnboarding();
  const { perfil, restricciones, error } = usePerfil(clientId);
  const v = (c: string) => perfil?.mifid[c]?.value;

  return (
    <Marco>
      <Cabecera titulo="Tu perfil" />
      <Contenido>
        {error && <p role="alert">No hemos podido cargar tu perfil. ¿Está el servidor encendido?</p>}
        {perfil && (
          <>
            <h1>Esto es lo que hemos entendido</h1>
            <Tarjeta>
              <div className="pila">
                <Dato titulo="Tu objetivo" valor={`${mostrarValor(v("objective.goal"))}, a unos ${mostrarValor(v("objective.horizon_years"))} años`} />
                <Dato titulo="Ahorro disponible" valor={`${mostrarValor(v("financial.liquid_savings_eur"))} €`} />
                <Dato
                  titulo="Colchón que deberías conservar"
                  valor={`${mostrarValor(v("financial.emergency_fund_eur"))} €`}
                  nota="Seis meses de tus gastos fijos, por si surge un imprevisto."
                />
                <Dato titulo="Si tus ahorros bajan" valor={mostrarValor(v("risk.reaction_to_drop"))} />
              </div>
            </Tarjeta>

            {perfil.alerts
              .filter((a) => a.status === "open")
              .map((a) => (
                <AlertaTarjeta key={a.id} alerta={a} paraCliente />
              ))}

            {restricciones && (
              <Tarjeta>
                <h2>Qué significa para ti</h2>
                <p>
                  Te mostraremos solo productos con un nivel de riesgo de <strong>{restricciones.max_risk_indicator ?? "—"} sobre 7</strong> como
                  máximo.
                </p>
                <p className="suave pequena" style={{ margin: 0 }}>
                  El nivel de riesgo (1 = muy bajo, 7 = muy alto) aparece en el documento de datos fundamentales de cada fondo.
                </p>
              </Tarjeta>
            )}

            <Tarjeta>
              <h2>Siguiente paso</h2>
              <p style={{ margin: 0 }}>
                {perfil.status === "active"
                  ? "Una persona del banco ya ha revisado tu perfil."
                  : "Una persona del banco revisará tu perfil. Te avisaremos cuando esté listo."}
              </p>
            </Tarjeta>
          </>
        )}
      </Contenido>
      <Pie>
        <Link href="/onboarding/productos">
          <Boton disabled={perfil?.status !== "active"}>Ver productos que encajan conmigo</Boton>
        </Link>
        {perfil?.status !== "active" && (
          <p className="pequena suave" style={{ textAlign: "center", margin: 0 }}>
            Disponible cuando tu perfil esté revisado.
          </p>
        )}
      </Pie>
    </Marco>
  );
}

function Dato({ titulo, valor, nota }: { titulo: string; valor: string; nota?: string }) {
  return (
    <div>
      <p className="pequena suave" style={{ margin: 0 }}>
        {titulo}
      </p>
      <p style={{ fontWeight: 600, margin: 0 }}>{valor}</p>
      {nota && (
        <p className="pequena suave" style={{ margin: 0 }}>
          {nota}
        </p>
      )}
    </div>
  );
}
