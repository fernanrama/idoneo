import type { Metadata, Viewport } from "next";
import { Figtree, IBM_Plex_Mono, JetBrains_Mono, Outfit, Sora } from "next/font/google";
import { OnboardingProvider } from "@/lib/onboarding";
import "./globals.css";

// Figtree se parece a la tipografía geométrica de MyInvestor; Outfit, a la de GPTadvisor.
// JetBrains Mono, para las etiquetas técnicas en versalitas de las pantallas oscuras.
const cliente = Figtree({ variable: "--font-sans", subsets: ["latin"], weight: ["400", "500", "600", "700", "800"] });
const asesor = Outfit({ variable: "--font-asesor", subsets: ["latin"], weight: ["300", "400", "500", "600", "700"] });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500"] });
// Marca idóneo (docs/marca): Sora en la landing y en lo que rodea a la demo; IBM Plex Mono para etiquetas técnicas.
const marca = Sora({ variable: "--font-marca", subsets: ["latin"], weight: ["400", "600"] });
const marcaMono = IBM_Plex_Mono({ variable: "--font-marca-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "idóneo · Perfiles vivos que cumplen la norma",
  description:
    "Del cuestionario a la conversación. Perfiles vivos que cumplen la norma. Prototipo: perfil inversor MiFID II por voz, con la prueba de cada dato y validación humana. Datos simulados.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0C1A1F",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${cliente.variable} ${asesor.variable} ${mono.variable} ${marca.variable} ${marcaMono.variable}`}>
      <body>
        <OnboardingProvider>{children}</OnboardingProvider>
      </body>
    </html>
  );
}
