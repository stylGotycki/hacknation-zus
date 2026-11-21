import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Przykłady" };

export default function ExamplesPage() {
  return (
    <PagePlaceholder
      epic="E3"
      title="Przykładowe sytuacje rodzin"
      description="Scenariusze oparte na prawdziwych sprawach ZUS – zobacz, jak wygląda Twoja sytuacja."
      planned={[
        "12 scenariuszy (S1–S12): pracownica, JDG, zadłużenie, bliźnięta, wcześniak…",
        "Dla każdego: świadczenia, kwoty, oś czasu",
        "Przycisk „Wczytaj ten profil”",
      ]}
    />
  );
}
