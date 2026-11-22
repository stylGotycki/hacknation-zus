"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  listCitizens,
  mobywatelLogin,
  mobywatelLoginPesel,
  type Citizen,
} from "@/lib/api";
import { PUBLIC_PATHS } from "@/lib/routes";
import { startSession } from "@/lib/session";

export function LoginView() {
  const router = useRouter();
  const [citizens, setCitizens] = useState<Citizen[] | null>(null);
  const [selected, setSelected] = useState<Citizen | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pesel, setPesel] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

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
      await startSession(result.owner_id, result.citizen);
      router.push(PUBLIC_PATHS.zus);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zalogować.");
      setBusy(false);
    }
  }

  async function loginWithPesel(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await new Promise((resolve) => setTimeout(resolve, 900));
      const result = await mobywatelLoginPesel(pesel, firstName, lastName);
      await startSession(result.owner_id, result.citizen);
      router.push(
        result.citizen.demo ? PUBLIC_PATHS.zus : PUBLIC_PATHS.calculator,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się zalogować.");
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
            Serwis „Przewodnik rodzica” prosi o dostęp do Twoich danych: imię,
            nazwisko, PESEL.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="rounded-lg border bg-muted/40 p-4">
            <p className="font-medium">
              {selected.first_name} {selected.last_name}
            </p>
            <p className="text-sm text-muted-foreground">
              PESEL {selected.pesel_masked}
            </p>
          </div>
          {error && (
            <div
              role="alert"
              className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm"
            >
              {error}
            </div>
          )}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setSelected(null)}
              disabled={busy}
            >
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
    <div className="flex flex-col gap-6">
      <form
        onSubmit={loginWithPesel}
        className="flex flex-col gap-3 rounded-lg border p-4"
      >
        <h2 className="text-lg font-semibold">
          Zaloguj się własnym numerem PESEL
        </h2>
        <p className="text-sm text-muted-foreground">
          Wpisz dowolny poprawny PESEL (11 cyfr z sumą kontrolną, np.
          44051401359). To symulacja – nic nie jest wysyłane do mObywatela, a
          konto jest puste: dane wpisujesz w kalkulatorze.
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-sm font-bold">
            PESEL
            <input
              required
              inputMode="numeric"
              autoComplete="off"
              maxLength={11}
              value={pesel}
              onChange={(e) => setPesel(e.target.value.replace(/\D/g, ""))}
              className="rounded-sm border border-input px-3 py-2 font-normal"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm font-bold">
            Imię (opcjonalnie)
            <input
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="rounded-sm border border-input px-3 py-2 font-normal"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm font-bold">
            Nazwisko (opcjonalnie)
            <input
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="rounded-sm border border-input px-3 py-2 font-normal"
            />
          </label>
        </div>
        <Button
          type="submit"
          disabled={busy || pesel.length !== 11}
          className="w-fit"
        >
          {busy && <Loader2 className="animate-spin" />}
          Zaloguj
        </Button>
      </form>
      {error && (
        <div
          role="alert"
          className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm"
        >
          {error}
        </div>
      )}
      <h2 className="text-lg font-semibold">
        Albo wybierz konto demonstracyjne
      </h2>
      {!citizens && !error && (
        <Loader2 className="animate-spin text-muted-foreground" />
      )}
      <div className="grid gap-3">
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
            <span className="block text-sm font-bold text-primary">
              {c.scenario_title_pl}
            </span>
            <span className="mt-1 block text-sm text-muted-foreground">
              {c.scenario_description_pl}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
