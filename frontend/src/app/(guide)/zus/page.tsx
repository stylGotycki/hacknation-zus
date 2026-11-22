import { ShieldCheck } from "lucide-react";
import type { Metadata } from "next";

import { ZusView } from "@/components/mocks/zus-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Dane z ZUS" };

export default function ZusPage() {
  return (
    <section className="flex flex-col gap-8">
      <PageHeading title="Dane z ZUS" icon={ShieldCheck}>
        Po zalogowaniu pobieramy dane o ubezpieczeniu, zadłużeniu i zwolnieniach e-ZLA oraz liczymy z nich uprawnienia. Wszystko to symulacja – dane są przykładowe i nie pochodzą z ZUS.
      </PageHeading>
      <ZusView />
    </section>
  );
}
