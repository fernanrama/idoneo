import { redirect } from "next/navigation";

// El aviso de IA y el consentimiento de grabación están ahora en la propia pantalla de la entrevista.
export default function Presentacion() {
  redirect("/onboarding/entrevista");
}
