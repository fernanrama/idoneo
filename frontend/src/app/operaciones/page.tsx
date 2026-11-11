import type { Metadata } from "next";
import VistaOperaciones from "./VistaOperaciones";

export const metadata: Metadata = { title: "Calidad y costes · Idóneo para entidades" };

export default function Pagina() {
  return <VistaOperaciones />;
}
