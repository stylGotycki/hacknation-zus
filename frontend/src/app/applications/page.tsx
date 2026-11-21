import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Wnioski" };

export default function ApplicationsPage() {
  return (
    <PagePlaceholder
      epic="E6"
      title="Twoje wnioski"
      description="Wypełniaj wnioski krok po kroku, zapisuj wersje robocze i śledź ich status."
      planned={[
        "ZUS ZAM, wnioski o urlop macierzyński, rodzicielski i ojcowski",
        "Automatyczne zapisywanie wersji roboczych",
        "Status: złożony, w ZUS / u pracodawcy, rozpatrzony",
      ]}
    />
  );
}
