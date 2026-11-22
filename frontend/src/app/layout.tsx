import "@fontsource/lato/400.css";
import "@fontsource/lato/700.css";

import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Przewodnik rodzica – ZUS (wersja demonstracyjna)", template: "%s – Przewodnik rodzica" },
  description:
    "Sprawdź, jakie świadczenia przysługują Ci w ciąży i po narodzinach dziecka, ile urlopu zostało i jakie wnioski złożyć.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body className="flex min-h-dvh flex-col">{children}</body>
    </html>
  );
}
