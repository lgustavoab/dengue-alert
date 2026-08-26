import type { Metadata } from "next";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Dengue Alert",
    template: "%s | Dengue Alert",
  },
  description:
    "Aplicação de análise histórica, qualidade de dados e avaliação preditiva de risco elevado de dengue em municípios brasileiros.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" data-scroll-behavior="smooth">
      <body>
        <div className="app-shell">
          <SiteHeader />

          <main className="app-main">{children}</main>

          <SiteFooter />
        </div>
      </body>
    </html>
  );
}