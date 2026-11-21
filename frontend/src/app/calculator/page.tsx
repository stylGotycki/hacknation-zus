import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Kalkulator" };

export default function CalculatorPage() {
  return (
    <PagePlaceholder
      epic="E2"
      title="Kalkulator zasiłku i urlopów"
      description="Policz, ile wyniesie zasiłek macierzyński i jak długo potrwają urlopy."
      planned={[
        "Podstawa wymiaru: pracownik / JDG / zlecenie",
        "Porównanie wariantu 100% + 70% z wariantem 81,5%",
        "Długość urlopów wg liczby dzieci i zaświadczenia „Za życiem”",
      ]}
    />
  );
}
