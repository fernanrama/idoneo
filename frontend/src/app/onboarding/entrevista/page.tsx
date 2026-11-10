"use client";

import { ConversationProvider } from "@elevenlabs/react";
import { Entrevista } from "@/components/Entrevista";
import { Noche } from "@/components/visual";
import { useEntrevista } from "@/lib/useEntrevista";

export default function PaginaEntrevista() {
  return (
    <ConversationProvider>
      <Contenido />
    </ConversationProvider>
  );
}

function Contenido() {
  const e = useEntrevista();
  return (
    <Noche>
      <Entrevista e={e} />
    </Noche>
  );
}
