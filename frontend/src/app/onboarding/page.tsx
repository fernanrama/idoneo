"use client";

import Link from "next/link";
import { useState } from "react";
import { Boton, Cabecera, Contenido, Marco, Pie, Tarjeta } from "@/components/ui";

export default function Presentacion() {
  const [ia, setIa] = useState(false);
  const [grabacion, setGrabacion] = useState(false);
  return (
    <Marco>
      <Cabecera titulo="Tu perfil inversor" />
      <Contenido>
        <h1>Hablemos de ti</h1>
        <p>
          La ley nos pide conocer tu situación, tus objetivos y lo que sabes de inversión antes de ofrecerte productos.
          Así nos aseguramos de que lo que te propongamos encaje contigo.
        </p>
        <Tarjeta>
          <ul style={{ margin: 0, paddingLeft: 20 }} className="pila">
            <li>Unos 7 minutos. Puedes parar y seguir luego.</li>
            <li>Habla o escribe, como prefieras.</li>
            <li>No hay respuestas buenas ni malas: si algo no lo sabes, dilo.</li>
          </ul>
        </Tarjeta>
        <Tarjeta>
          <label className="fila" style={{ alignItems: "flex-start" }}>
            <input type="checkbox" checked={ia} onChange={(e) => setIa(e.target.checked)} style={{ width: 22, height: 22 }} />
            <span>Entiendo que hablaré con un asistente de inteligencia artificial y que una persona del banco revisará el resultado.</span>
          </label>
          <label className="fila" style={{ alignItems: "flex-start", marginTop: 12 }}>
            <input type="checkbox" checked={grabacion} onChange={(e) => setGrabacion(e.target.checked)} style={{ width: 22, height: 22 }} />
            <span>Acepto que se grabe la conversación para justificar mi perfil. No se usará mi voz para identificarme.</span>
          </label>
        </Tarjeta>
      </Contenido>
      <Pie>
        <Link href={ia && grabacion ? "/onboarding/entrevista" : "#"} aria-disabled={!(ia && grabacion)}>
          <Boton disabled={!(ia && grabacion)}>Continuar</Boton>
        </Link>
      </Pie>
    </Marco>
  );
}
