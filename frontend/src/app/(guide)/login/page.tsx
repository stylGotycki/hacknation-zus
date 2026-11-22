import { UserRound } from "lucide-react";
import type { Metadata } from "next";

import { LoginView } from "@/components/mocks/login-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Logowanie" };

export default function LoginPage() {
  return (
    <section className="flex w-full flex-col gap-6">
      <PageHeading title="Zaloguj się przez mObywatel" icon={UserRound}>
        To symulacja logowania. Wybierz osobę – wczytamy jej dane z ZUS, zwolnienia e-ZLA i wnioski.
      </PageHeading>
      <LoginView />
    </section>
  );
}
