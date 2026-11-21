"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listCitizens, mobywatelLogin, type Citizen } from "@/lib/api";
import { PUBLIC_PATHS } from "@/lib/routes";
import { startSession } from "@/lib/session";

export function LoginView() {
  const router = useRouter();
  const [citizens, setCitizens] = useState<Citizen[] | null>(null);
  const [selected, setSelected] = useState<Citizen | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCitizens()
      .then(setCitizens)
      .catch((e: Error) => setError(e.message));
  }, []);

  async function confirm() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      // The pause imitates the confirmation in the mObywatel app.
      await new Promise((resolve) => setTimeout(resolve, 900));
      const result = await mobywatelLogin(selected.id);
      startSession(result.owner_id, result.citizen);
      router.push(PUBLIC_PATHS.zus);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zalogować.");
      setBusy(false);
    }
  }

  if (selected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="text-primary" /> mObywatel
          </CardTitle>
          <CardDescription>
            Serwis „Przewodnik rodzica” prosi o dostęp do Twoich danych: imię, nazwisko, PESEL.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="rounded-lg border bg-muted/40 p-4">
            <p className="font-medium">
              {selected.first_name} {selected.last_name}
            </p>
            <p className="text-sm text-muted-foreground">PESEL {selected.pesel_masked}</p>
          </div>
          {error && (
            <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
              {error}
            </div>
          )}
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setSelected(null)} disabled={busy}>
              Wróć
            </Button>
            <Button onClick={confirm} disabled={busy} className="flex-1">
              {busy && <Loader2 className="animate-spin" />}
              Potwierdź w aplikacji mObywatel
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          {error}
        </div>
      )}
      {!citizens && !error && <Loader2 className="animate-spin text-muted-foreground" />}
      <div className="grid gap-3 sm:grid-cols-2">
        {citizens?.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setSelected(c)}
            className="rounded-lg border p-4 text-left transition-colors hover:border-primary hover:bg-muted"
          >
            <span className="block font-medium">
              {c.first_name} {c.last_name}
            </span>
            <span className="block text-sm text-muted-foreground">{c.scenario_title_pl}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
