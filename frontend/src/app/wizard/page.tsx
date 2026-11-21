import type { Metadata } from "next";

import { WizardView } from "@/components/wizard/wizard-view";

export const metadata: Metadata = { title: "Sprawdź uprawnienia" };

export default function WizardPage() {
  return (
    <section className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Sprawdź swoje uprawnienia</h1>
        <p className="text-muted-foreground">
          Kilka pytań o rodzinę i pracę – na końcu lista świadczeń, terminów i ryzyk. Wynik ma charakter
          informacyjny.
        </p>
      </div>
      <WizardView />
    </section>
  );
}
