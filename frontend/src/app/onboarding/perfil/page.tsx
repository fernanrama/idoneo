"use client";

import Link from "next/link";
import { AlertaTarjeta, Boton, Cabecera, Contenido, IndicadorRiesgo, Marco, Pasos, Pie, Tarjeta } from "@/components/ui";
import { FAMILIAS, mostrarValor } from "@/lib/bloques";
import { useOnboarding } from "@/lib/onboarding";
import { usePerfil } from "@/lib/usePerfil";

// Resumen para el cliente, en lenguaje claro. No es un informe para el banquero.
export default function MiPerfil() {
  const { clientId } = useOnboarding();
  const { perfil, error } = usePerfil(clientId);
  const v = (c: string) => perfil?.mifid[c]?.value;
  const noConvenientes = perfil
    ? Object.entries(perfil.assessments.appropriateness)
        .filter(([, x]) => x === "not_appropriate")
        .map(([f]) => FAMILIAS[f] ?? f)
    : [];

  return (
    <Marco>
      <Cabecera titulo="Tu perfil" />
      <Contenido>
        {error && <p role="alert">No hemos podido cargar tu perfil. ¿Está el servidor encendido?</p>}
        {perfil && (
          <>
            <Pasos actual={2} />
            <h1>
              Esto es lo que <span style={{ fontWeight: 400 }}>hemos entendido</span>
            </h1>
            <Tarjeta>
              <div className="pila">
                <Dato
                  titulo="Tu objetivo"
                  valor={`${mostrarValor(v("objectives.o1.goal"))}, a unos ${mostrarValor(v("objectives.o1.horizon_years"))} años`}
                />
                <Dato titulo="Ahorro disponible" valor={`${mostrarValor(v("financial.liquid_savings_eur"))} €`} />
                <Dato
                  titulo="Tus ahorros cubren"
                  valor={`${mostrarValor(v("financial.emergency_fund_months"))} meses de gastos fijos`}
                  nota="Conviene conservar siempre al menos seis meses por si surge un imprevisto."
                />
                <Dato titulo="Si tus ahorros bajan" valor={mostrarValor(v("risk_tolerance.past_behaviour"))} />
              </div>
            </Tarjeta>

            {perfil.alerts
              .filter((a) => a.status === "open")
              .map((a) => (
                <AlertaTarjeta key={a.id} alerta={a} paraCliente />
              ))}

            <Tarjeta>
              <h2>Qué significa para ti</h2>
              <IndicadorRiesgo nivel={perfil.assessments.suitability.max_sri} />
              <p style={{ marginTop: 12 }}>
                Te mostraremos productos con un nivel de riesgo de{" "}
                <strong>{perfil.assessments.suitability.max_sri ?? "—"} sobre 7</strong> como máximo.
              </p>
              {noConvenientes.length > 0 && (
                <p>
                  Si quieres comprar por tu cuenta {noConvenientes.join(", ")}, te avisaremos antes, porque todavía no
                  conoces bien cómo funcionan.
                </p>
              )}
              <p className="suave pequena" style={{ margin: 0 }}>
                El nivel de riesgo (1 = muy bajo, 7 = muy alto) aparece en el documento de datos fundamentales de cada fondo.
              </p>
            </Tarjeta>

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
