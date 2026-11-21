import type { Metadata, Viewport } from "next";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Przewodnik rodzica", template: "%s · Przewodnik rodzica" },
  description:
    "Sprawdź, jakie świadczenia przysługują Ci po narodzinach dziecka, i złóż wnioski krok po kroku.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body className="flex min-h-dvh flex-col">
        <SiteHeader />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:py-12">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
