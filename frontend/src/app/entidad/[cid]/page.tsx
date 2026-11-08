import { Suspense } from "react";
import VistaEntidad from "./VistaEntidad";

export default function Pagina({ params }: PageProps<"/entidad/[cid]">) {
  return (
    <Suspense fallback={null}>
      <VistaEntidad params={params} />
    </Suspense>
  );
}
