"use client";

import { ConversationProvider } from "@elevenlabs/react";
import { use, useState } from "react";
import { Entrevista } from "@/components/Entrevista";
import { PanelVivo } from "@/components/PanelVivo";
import { Noche } from "@/components/visual";
import { useEntrevista } from "@/lib/useEntrevista";
import { usePerfil } from "@/lib/usePerfil";
import s from "./escenario.module.css";

/**
 * Escenario del pitch: a la izquierda lo que vive el cliente (el aura y la pregunta), a la derecha lo
 * que recibe la entidad, en directo y con datos reales del backend.
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
  if ((e.estado === "terminada") !== terminada) {
    setTerminada(e.estado === "terminada");
    if (e.estado === "terminada") setVista("entidad"); // en el móvil: ahí está «Ver el perfil de Carmen»
  }
  const datos = perfil ? Object.entries(perfil.mifid).filter(([r, f]) => f.value != null && !r.startsWith("disclosures.")).length : 0;

  return (
    <div className={`${s.raiz} ${vista === "entidad" ? s.verEntidad : s.verCliente}`}>
      <div className={s.conmutador} role="tablist" aria-label="Qué mitad ver">
        <button role="tab" aria-selected={vista === "cliente"} onClick={() => setVista("cliente")}>
          El cliente
        </button>
        <button role="tab" aria-selected={vista === "entidad"} onClick={() => setVista("entidad")}>
          La entidad{datos > 0 && <b key={datos}>{datos}</b>}
        </button>
      </div>
      <Noche className={s.cliente}>
        <Entrevista e={e} compacto />
      </Noche>
      <div className={s.entidad}>
        <PanelVivo perfil={perfil} enMarcha={enMarcha} />
      </div>
    </div>
  );
}
