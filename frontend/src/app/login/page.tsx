import type { Metadata } from "next";

import { LoginView } from "@/components/mocks/login-view";

export const metadata: Metadata = { title: "Logowanie" };

export default function LoginPage() {
  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Zaloguj się przez mObywatel</h1>
        <p className="text-muted-foreground">
          To symulacja logowania. Wybierz osobę – wczytamy jej dane z ZUS, zwolnienia e-ZLA i wnioski.
        </p>
      </div>
      <LoginView />
    </section>
  );
}
