"use client";

import { ConversationProvider } from "@elevenlabs/react";
import Link from "next/link";
import {
  AlertaTarjeta,
  BarraBloques,
  Boton,
  BotonMicro,
  Cabecera,
  Contenido,
  EntradaTexto,
  Marco,
  Pie,
  Subtitulos,
} from "@/components/ui";
import { estadoBloques } from "@/lib/bloques";
import { useEntrevista } from "@/lib/useEntrevista";

export default function PaginaEntrevista() {
  return (
    <ConversationProvider>
      <Entrevista />
    </ConversationProvider>
  );
}

function Entrevista() {
  const e = useEntrevista();
  const alerta = e.perfil?.alerts.filter((a) => a.status === "open").at(-1);
  const enMarcha = e.estado === "activa" || e.estado === "conectando";

  return (
    <Marco>
      <Cabecera titulo="Tu perfil inversor" />
      <Contenido>
        <BarraBloques bloques={estadoBloques(e.perfil)} />

        {e.estado === "inactiva" && (
          <div className="pila" style={{ textAlign: "center", marginTop: 24 }}>
            <h2>Cuando quieras, empezamos</h2>
            <p className="suave">Pulsa el micrófono y habla con normalidad. Verás lo que decimos escrito en pantalla.</p>
          </div>
        )}

        {e.modo === "guion" && <p className="pequena suave">Demo guiada · datos simulados</p>}

        <Subtitulos turnos={e.turnos} />

        {alerta && <AlertaTarjeta alerta={alerta} paraCliente />}

        {e.error && (
          <p role="alert" style={{ color: "var(--c-error)" }}>
            {e.error}
          </p>
        )}
      </Contenido>

      <Pie>
        {e.estado !== "terminada" && (
          <BotonMicro
            activo={enMarcha && e.modo === "voz"}
            etiqueta={enMarcha ? "Terminar la conversación" : "Empezar a hablar"}
            onClick={enMarcha ? e.terminar : e.iniciarVoz}
          />
        )}
        {e.modo === "voz" && e.estado === "activa" && (
          <p className="pequena suave" style={{ textAlign: "center", margin: 0 }}>
            {e.hablando ? "El asistente está hablando…" : "Te escuchamos"}
          </p>
        )}
        {e.modo === "voz" && e.estado === "activa" && <EntradaTexto onEnviar={e.enviarTexto} />}

        {e.estado === "inactiva" && (
          <Boton variante="texto" onClick={() => e.iniciarGuion(1)}>
            Ver demo guiada (datos simulados)
          </Boton>
        )}

        {e.estado === "terminada" && (
          <Link href="/onboarding/perfil">
            <Boton>Ver mi perfil</Boton>
          </Link>
        )}
      </Pie>
    </Marco>
  );
}
