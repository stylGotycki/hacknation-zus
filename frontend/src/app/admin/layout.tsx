import { ChevronLeft } from "lucide-react";
import Link from "next/link";

/** The admin panel is a plain standalone page – not part of the parent's guide layout. */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-white">
      <p className="bg-navy px-4 py-1.5 text-center text-[13px] text-white">
        Wersja demonstracyjna — projekt HackNation 2026, nie jest serwisem ZUS.
      </p>
      <header className="border-b border-band-border">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3">
          <div>
            <p className="text-lg font-bold">Panel administratora</p>
            <p className="text-sm text-muted-foreground">Przewodnik rodzica – reguły, parametry i stawki</p>
          </div>
          <Link href="/" className="inline-flex items-center gap-1 text-sm font-bold text-link hover:underline">
            <ChevronLeft className="size-4" /> Przewodnik rodzica
          </Link>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  );
}
