import type { Metadata } from "next";

import { ApplicationsView } from "@/components/applications/applications-view";

export const metadata: Metadata = { title: "Wnioski" };

export default function ApplicationsPage() {
  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Twoje wnioski</h1>
        <p className="max-w-2xl text-muted-foreground">
          Wypełniaj wnioski o urlopy i zasiłek krok po kroku. Dane z wyliczenia uzupełniamy za Ciebie, wersje
          robocze zapisują się same, a status złożonych wniosków możesz śledzić tutaj. To symulacja – wnioski nie
          trafiają do prawdziwego pracodawcy ani do ZUS.
        </p>
      </div>
      <ApplicationsView />
    </section>
  );
}
