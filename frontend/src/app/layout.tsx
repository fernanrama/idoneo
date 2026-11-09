import type { Metadata, Viewport } from "next";
import { Figtree, Outfit } from "next/font/google";
import { OnboardingProvider } from "@/lib/onboarding";
import "./globals.css";

// Figtree se parece a la tipografía geométrica de MyInvestor; Outfit, a la de GPTadvisor.
const cliente = Figtree({ variable: "--font-sans", subsets: ["latin"], weight: ["400", "500", "600", "700", "800"] });
const asesor = Outfit({ variable: "--font-asesor", subsets: ["latin"], weight: ["300", "400", "500", "600"] });

export const metadata: Metadata = {
  title: "Idóneo · Perfil inversor por voz",
  description: "Prototipo de feature: onboarding MiFID por voz con perfil verificado. Datos simulados.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#ffffff",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${cliente.variable} ${asesor.variable}`}>
      <body>
        <OnboardingProvider>{children}</OnboardingProvider>
      </body>
    </html>
  );
}
