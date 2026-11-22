import { FileText } from "lucide-react";
import type { Metadata } from "next";

import { ApplicationsView } from "@/components/applications/applications-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Wnioski" };

export default function ApplicationsPage() {
  return (
    <section className="flex flex-col gap-8">
      <PageHeading title="Twoje wnioski" icon={FileText}>
        Wypełniaj wnioski o urlopy i zasiłek krok po kroku. Dane z wyliczenia uzupełniamy za Ciebie, wersje robocze zapisują się same, a status złożonych wniosków możesz śledzić tutaj. To symulacja – wnioski nie trafiają do prawdziwego pracodawcy ani do ZUS.
      </PageHeading>
      <ApplicationsView />
    </section>
  );
}
