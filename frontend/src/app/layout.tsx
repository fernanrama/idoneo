import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { OnboardingProvider } from "@/lib/onboarding";
import "./globals.css";

const inter = Inter({ variable: "--font-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Idóneo · Perfil inversor por voz",
  description: "Prototipo de feature: onboarding MiFID por voz con perfil verificado. Datos simulados.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0b2a4a",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={inter.variable}>
      <body>
        <OnboardingProvider>{children}</OnboardingProvider>
      </body>
    </html>
  );
}
