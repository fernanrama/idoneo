import type { Metadata } from "next";
import VistaOperaciones from "./VistaOperaciones";

export const metadata: Metadata = { title: "Calidad y costes · idóneo para entidades" };

export default function Pagina() {
  return <VistaOperaciones />;
}
