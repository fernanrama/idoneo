import { Suspense } from "react";
import VistaAdmin from "./VistaAdmin";

export const metadata = { title: "Idóneo · Administración de la entidad" };

export default function Pagina() {
  return (
    <Suspense fallback={null}>
      <VistaAdmin />
    </Suspense>
  );
}
