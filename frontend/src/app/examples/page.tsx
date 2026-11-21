import type { Metadata } from "next";

import { ExamplesView } from "@/components/examples/examples-view";

export const metadata: Metadata = { title: "Przykłady" };

export default function ExamplesPage() {
  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Przykładowe sytuacje rodzin</h1>
        <p className="max-w-2xl text-muted-foreground">
          Dwanaście typowych historii zbudowanych na podstawie spraw rozpatrywanych w ZUS. Wybierz tę, która
          jest podobna do Twojej, i zobacz zasiłki, kwoty, terminy oraz oś czasu.
        </p>
      </div>
      <ExamplesView />
    </section>
  );
}
