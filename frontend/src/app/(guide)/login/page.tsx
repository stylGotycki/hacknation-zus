import { UserRound } from "lucide-react";
import type { Metadata } from "next";

import { LoginView } from "@/components/mocks/login-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Logowanie" };

export default function LoginPage() {
  return (
    <section className="flex w-full flex-col gap-6">
      <PageHeading title="Zaloguj się przez mObywatel" icon={UserRound}>
        To symulacja logowania. Wybierz osobę – wczytamy jej dane z ZUS,
        zwolnienia e-ZLA i wnioski.
      </PageHeading>
      <p className="max-w-3xl border-l-[5px] border-navy bg-muted p-3 text-sm">
        <strong>Demo aplikacji.</strong> Trzy konta demonstracyjne mają już
        wprowadzone wnioski i historię. Pozostałe dane i formularze uzupełniasz
        ręcznie – system nie odczytuje skanów ani zdjęć dokumentów (brak OCR).
      </p>
      <LoginView />
    </section>
  );
}
