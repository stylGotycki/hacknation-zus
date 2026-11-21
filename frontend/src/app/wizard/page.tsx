import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Sprawdź uprawnienia" };

export default function WizardPage() {
  return (
    <PagePlaceholder
      epic="E4"
      title="Sprawdź swoje uprawnienia"
      description="Kilka pytań o rodzinę i pracę – na końcu lista świadczeń, które Ci przysługują."
      planned={[
        "Pytania o rodziców, dziecko i formę zatrudnienia",
        "Wynik z silnika reguł (E1) z uzasadnieniem i podstawą prawną",
        "Przejście do osi czasu i wniosków",
      ]}
    />
  );
}
