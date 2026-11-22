import { CalendarRange } from "lucide-react";
import type { Metadata } from "next";

import { TimelineView } from "@/components/timeline/timeline-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Oś czasu" };

export default function TimelinePage() {
  return (
    <section className="flex flex-col gap-6">
      <PageHeading title="Oś czasu urlopów i terminów" icon={CalendarRange}>
        Plan urlopów mamy i taty oraz terminy składania wniosków – od narodzin dziecka po ostatni dzień na wykorzystanie urlopu.
      </PageHeading>
      <TimelineView />
    </section>
  );
}
