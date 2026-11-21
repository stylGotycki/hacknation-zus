import type { Metadata } from "next";

import { HelpView } from "@/components/help/help-view";

export const metadata: Metadata = { title: "Pomoc i wsparcie" };

export default function HelpPage() {
  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Pomoc i wsparcie</h1>
        <p className="max-w-2xl text-muted-foreground">
          Oficjalne źródła informacji, organizacje wspierające rodziców w szczególnych sytuacjach i symulacja wniosku o
          odpis aktu urodzenia.
        </p>
      </div>
      <HelpView />
    </section>
  );
}
