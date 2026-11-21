import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Oś czasu" };

export default function TimelinePage() {
  return (
    <PagePlaceholder
      epic="E5"
      title="Oś czasu urlopów"
      description="Plan urlopów mamy i taty w formie osi – jak gałęzie w gicie."
      planned={[
        "Gałąź mamy i gałąź taty z okresami urlopów",
        "Terminy na złożenie wniosków",
        "Szczegóły okresu po kliknięciu",
      ]}
    />
  );
}
