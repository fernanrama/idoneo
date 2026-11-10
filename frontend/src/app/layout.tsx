import type { Metadata, Viewport } from "next";
import { Figtree, JetBrains_Mono, Outfit } from "next/font/google";
import { OnboardingProvider } from "@/lib/onboarding";
import "./globals.css";

// Figtree se parece a la tipografía geométrica de MyInvestor; Outfit, a la de GPTadvisor.
// JetBrains Mono, para las etiquetas técnicas en versalitas de las pantallas oscuras.
const cliente = Figtree({ variable: "--font-sans", subsets: ["latin"], weight: ["400", "500", "600", "700", "800"] });
const asesor = Outfit({ variable: "--font-asesor", subsets: ["latin"], weight: ["300", "400", "500", "600", "700"] });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "Idóneo · Tu perfil inversor, en una conversación",
  description: "Prototipo: perfil inversor MiFID II por voz, con la prueba de cada dato y validación humana. Datos simulados.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#05070d",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${cliente.variable} ${asesor.variable} ${mono.variable}`}>
      <body>
        <OnboardingProvider>{children}</OnboardingProvider>
      </body>
    </html>
  );
}
