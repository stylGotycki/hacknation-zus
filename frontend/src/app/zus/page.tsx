import type { Metadata } from "next";

import { ZusView } from "@/components/mocks/zus-view";

export const metadata: Metadata = { title: "Dane z ZUS" };

export default function ZusPage() {
  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Dane z ZUS</h1>
        <p className="max-w-2xl text-muted-foreground">
          Po zalogowaniu pobieramy dane o ubezpieczeniu, zadłużeniu i zwolnieniach e-ZLA oraz liczymy z nich
          uprawnienia. Wszystko to symulacja – dane są przykładowe i nie pochodzą z ZUS.
        </p>
      </div>
      <ZusView />
    </section>
  );
}
