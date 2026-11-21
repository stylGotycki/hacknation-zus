import type { Metadata } from "next";

import { AdminView } from "@/components/admin/admin-view";

export const metadata: Metadata = { title: "Panel administratora" };

export default function AdminPage() {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Panel administratora</h1>
        <p className="max-w-2xl text-muted-foreground">
          Zmieniaj parametry prawne (stawki, limity, progi) po zmianie przepisów i prowadź obieg złożonych wniosków.
        </p>
      </div>
      <AdminView />
    </section>
  );
}
