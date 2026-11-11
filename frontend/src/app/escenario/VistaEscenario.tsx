"use client";

import { ConversationProvider } from "@elevenlabs/react";
import Link from "next/link";
import { use, useState } from "react";
import { Entrevista } from "@/components/Entrevista";
import { Logo } from "@/components/Logo";
import { MarcoMovil } from "@/components/MarcoMovil";
import { PanelVivo } from "@/components/PanelVivo";
import { Noche } from "@/components/visual";
import { useEntrevista } from "@/lib/useEntrevista";
import { usePerfil } from "@/lib/usePerfil";
import { AsesorDemo } from "./AsesorDemo";
import s from "./escenario.module.css";

/**
 * Demo guiada: a la izquierda, un móvil con la app de la entidad y el módulo de idóneo dentro (lo que
 * vive el cliente); a la derecha, el perfil que recibe la entidad, construyéndose en directo.
 * `?cliente=<id>` enseña en el panel un perfil ya existente (p. ej. carmen-68) antes de empezar.
 */
export default function VistaEscenario({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const q = use(searchParams);
  const cliente = typeof q.cliente === "string" ? q.cliente : null;
  return (
    <ConversationProvider>
      <Escenario cliente={cliente} />
    </ConversationProvider>
  );
}

function Escenario({ cliente }: { cliente: string | null }) {
  const e = useEntrevista();
  const previo = usePerfil(cliente ?? "", cliente ? 3000 : undefined);
  const enMarcha = e.estado === "activa" || e.estado === "conectando";
  const perfil = e.estado === "inactiva" && cliente ? previo.perfil : e.perfil;
  // En el móvil no caben las dos mitades: se elige cuál ver. En el ordenador se ven a la vez.
  const [vista, setVista] = useState<"cliente" | "entidad">("cliente");
  const [terminada, setTerminada] = useState(false);
  // La misma función, con la apariencia de dos entidades distintas: idóneo se integra en la app de cada una.
  const [entidad, setEntidad] = useState<"A" | "B">("A");
  // Al acabar, la demo enseña también lo que recibe el asesor (sin clave y sin llamar al servidor).
  const [verAsesor, setVerAsesor] = useState(false);
  if ((e.estado === "terminada") !== terminada) {
    setTerminada(e.estado === "terminada");
    if (e.estado === "terminada") setVista("entidad"); // en el móvil: ahí está «Ver el perfil de Carmen»
    else setVerAsesor(false);
  }
  const datos = perfil ? Object.entries(perfil.mifid).filter(([r, f]) => f.value != null && !r.startsWith("disclosures.")).length : 0;

  return (
    <div className={`${s.raiz} ${vista === "entidad" ? s.verEntidad : s.verCliente}`}>
      <header className={s.barra}>
        <Link href="/" aria-label="idóneo, volver al inicio">
          <Logo variante="oscuro" alto={24} />
        </Link>
        <span className={s.barraTitulo}>Demo guiada · Carmen, 68 años · caso simulado</span>
        <div className={s.apariencia} role="group" aria-label="Apariencia de la app de la entidad">
          <span>Apariencia de la app</span>
          {(["A", "B"] as const).map((x) => (
            <button key={x} type="button" aria-pressed={entidad === x} onClick={() => setEntidad(x)}>
              Entidad {x}
            </button>
          ))}
        </div>
      </header>

      <div className={s.conmutador} role="tablist" aria-label="Qué mitad ver">
        <button role="tab" aria-selected={vista === "cliente"} onClick={() => setVista("cliente")}>
          El cliente
        </button>
        <button role="tab" aria-selected={vista === "entidad"} onClick={() => setVista("entidad")}>
          La entidad{datos > 0 && <b key={datos}>{datos}</b>}
        </button>
      </div>

      <div className={s.cuerpo}>
        <div className={s.colCliente}>
          <MarcoMovil entidad={entidad}>
            <Noche className={`${s.cliente} ${entidad === "A" ? s.temaA : s.temaB}`}>
              <Entrevista e={e} compacto />
            </Noche>
          </MarcoMovil>
          <p className={s.rotulo}>
            <strong>Lo que ve el cliente, dentro de la app de su entidad</strong>
          </p>
        </div>
        <div className={s.colEntidad}>
          <p className={s.rotulo}>
            <strong>Lo que recibe la entidad</strong>
            El perfil se construye mientras el cliente habla: cada dato, con su frase exacta.
          </p>
          {terminada && perfil && !verAsesor && (
            <button type="button" className={s.pasoAsesor} onClick={() => setVerAsesor(true)}>
              <span>
                <strong>Siguiente: lo que recibe el asesor</strong>
                El perfil hecho, cada frase con su audio, y la validación de una persona.
              </span>
              <b aria-hidden="true">→</b>
            </button>
          )}
          <div className={s.entidad}>
            {terminada && perfil && verAsesor ? (
              <AsesorDemo perfil={perfil} alVolver={() => setVerAsesor(false)} />
            ) : (
              <PanelVivo perfil={perfil} enMarcha={enMarcha} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
