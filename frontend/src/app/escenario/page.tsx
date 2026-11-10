import { Suspense } from "react";
import VistaEscenario from "./VistaEscenario";

export default function Pagina({ searchParams }: PageProps<"/escenario">) {
  return (
    <Suspense fallback={null}>
      <VistaEscenario searchParams={searchParams} />
    </Suspense>
  );
}
