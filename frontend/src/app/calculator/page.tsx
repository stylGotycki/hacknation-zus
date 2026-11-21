import type { Metadata } from "next";

import { CalculatorForm } from "@/components/calculator/calculator-form";

export const metadata: Metadata = { title: "Kalkulator" };

export default function CalculatorPage() {
  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Kalkulator zasiłku i urlopów</h1>
        <p className="max-w-2xl text-muted-foreground">
          Podaj kilka danych o rodzinie, a policzymy długość urlopów, wysokość zasiłków, wskażemy, gdzie złożyć
          wnioski, i ostrzeżemy przed sytuacjami, w których można stracić świadczenia. Wynik ma charakter
          informacyjny.
        </p>
      </div>
      <CalculatorForm />
    </section>
  );
}
