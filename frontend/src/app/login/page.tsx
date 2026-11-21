import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";

export const metadata: Metadata = { title: "Logowanie" };

export default function LoginPage() {
  return (
    <PagePlaceholder
      epic="E7"
      title="Zaloguj się przez mObywatel"
      description="Symulacja logowania – wybierz personę, a jej dane z ZUS i e-ZLA zostaną wczytane."
      planned={[
        "Mock ekranu mObywatel z listą person (scenariusze z E3)",
        "Mock danych z ZUS: historia ubezpieczenia, podstawa wymiaru",
        "Mock zwolnień e-ZLA i wysyłki do PUE ZUS",
      ]}
    />
  );
}
