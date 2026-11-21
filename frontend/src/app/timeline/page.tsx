import type { Metadata } from "next";

import { TimelineView } from "@/components/timeline/timeline-view";

export const metadata: Metadata = { title: "Oś czasu" };

export default function TimelinePage() {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Oś czasu urlopów i terminów</h1>
        <p className="max-w-2xl text-muted-foreground">
          Plan urlopów mamy i taty oraz terminy składania wniosków – od narodzin dziecka po ostatni dzień na
          wykorzystanie urlopu.
        </p>
      </div>
      <TimelineView />
    </section>
  );
}
