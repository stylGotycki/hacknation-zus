import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="flex flex-col items-start gap-4">
      <h1 className="text-2xl font-semibold">Nie znaleziono strony</h1>
      <p className="text-muted-foreground">Ta strona nie istnieje albo została przeniesiona.</p>
      <Button asChild>
        <Link href="/">Wróć na start</Link>
      </Button>
    </section>
  );
}
