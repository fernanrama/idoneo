"use client";

import { ConversationProvider } from "@elevenlabs/react";
import Link from "next/link";
import { use } from "react";
import { Entrevista } from "@/components/Entrevista";
import { PanelVivo } from "@/components/PanelVivo";
import { Noche, clasesBoton } from "@/components/visual";
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

  return (
    <div className={s.raiz}>
      <Noche className={s.cliente}>
        <Entrevista
          e={e}
          compacto
          alTerminar={
            e.perfil && (
              <Link href={`/entidad/${encodeURIComponent(e.perfil.client_id)}`}>
                <span className={clasesBoton.luz}>Validar en la entidad</span>
              </Link>
            )
          }
        />
      </Noche>
      <div className={s.entidad}>
        <PanelVivo perfil={perfil} enMarcha={enMarcha} />
      </div>
    </div>
  );
}
