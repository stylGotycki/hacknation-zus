import { ApiStatus } from "@/components/api-status";

export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>Przewodnik rodzica – projekt hackathonowy, nie jest oficjalnym serwisem ZUS.</p>
        <ApiStatus />
      </div>
    </footer>
  );
}
