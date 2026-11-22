import { Calculator } from "lucide-react";
import type { Metadata } from "next";

import { CalculatorForm } from "@/components/calculator/calculator-form";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Kalkulator" };

export default function CalculatorPage() {
  return (
    <section className="flex flex-col gap-8">
      <PageHeading title="Kalkulator zasiłku i urlopów" icon={Calculator}>
        Podaj kilka danych o rodzinie, a policzymy długość urlopów, wysokość zasiłków, wskażemy, gdzie złożyć wnioski, i ostrzeżemy przed sytuacjami, w których można stracić świadczenia. Wynik ma charakter informacyjny.
      </PageHeading>
      <CalculatorForm />
    </section>
  );
}
