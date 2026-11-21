import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NAV_ITEMS } from "@/lib/nav";
import { PUBLIC_PATHS } from "@/lib/routes";

const STEPS = [
  {
    title: "Wybierz sytuację",
    text: "Zacznij od gotowego przykładu rodziny albo odpowiedz na kilka pytań w kreatorze.",
    href: PUBLIC_PATHS.examples,
    cta: "Przykładowe sprawy",
  },
  {
    title: "Sprawdź ubezpieczenie",
    text: "Zaloguj się symulowanym profilem zaufanym i zobacz dane z ZUS: tytuł ubezpieczenia, zadłużenie, zwolnienia.",
    href: PUBLIC_PATHS.login,
    cta: "Zaloguj (symulacja)",
  },
  {
    title: "Policz świadczenia",
    text: "Kalkulator pokaże zasiłki, długość urlopów i terminy, a oś czasu ułoży plan mamy i taty.",
    href: PUBLIC_PATHS.calculator,
    cta: "Otwórz kalkulator",
  },
  {
    title: "Złóż wnioski",
    text: "Wnioski wypełnią się danymi, które już podałeś. Zapiszesz wersję roboczą i wrócisz do niej później.",
    href: PUBLIC_PATHS.applications,
    cta: "Przejdź do wniosków",
  },
];

const PROMISES = [
  "Wyniki oparte na przepisach – z podaniem podstawy prawnej.",
  "Bez logowania do prawdziwych systemów i bez przesyłania dokumentów.",
  "Kwoty i terminy z obowiązujących parametrów, nie z domysłów.",
];

export default function HomePage() {
  const tiles = NAV_ITEMS.filter((item) => item.route !== "admin");

  return (
    <div className="flex flex-col gap-16">
      <section className="flex flex-col items-start gap-5">
        <p className="text-sm font-medium text-primary">Przewodnik dla przyszłych i świeżych rodziców</p>
        <h1 className="max-w-3xl text-3xl font-semibold tracking-tight sm:text-5xl">
          Zostajesz rodzicem? Sprawdź, co Ci przysługuje.
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          Urlop macierzyński, rodzicielski i ojcowski, zasiłki i terminy – w jednym miejscu, z wnioskami wypełnianymi
          krok po kroku.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild size="lg">
            <Link href={PUBLIC_PATHS.wizard}>
              Sprawdź uprawnienia <ArrowRight />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href={PUBLIC_PATHS.examples}>Zobacz przykłady</Link>
          </Button>
        </div>
        <ul className="mt-2 flex flex-col gap-1.5 text-sm text-muted-foreground">
          {PROMISES.map((text) => (
            <li key={text} className="flex items-start gap-2">
              <Check className="mt-0.5 size-4 shrink-0 text-primary" /> {text}
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-5" aria-labelledby="how-it-works">
        <h2 id="how-it-works" className="text-2xl font-semibold tracking-tight">
          Jak to działa
        </h2>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title}>
              <Card className="h-full">
                <CardHeader>
                  <span className="mb-1 flex size-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {index + 1}
                  </span>
                  <CardTitle className="text-base">{step.title}</CardTitle>
                  <CardDescription>{step.text}</CardDescription>
                  <Link href={step.href} className="mt-2 text-sm font-medium text-primary underline-offset-4 hover:underline">
                    {step.cta} →
                  </Link>
                </CardHeader>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex flex-col gap-5" aria-labelledby="all-tools">
        <h2 id="all-tools" className="text-2xl font-semibold tracking-tight">
          Wszystko w jednym miejscu
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tiles.map((item) => (
            <Link key={item.route} href={item.href} className="group">
              <Card className="h-full transition-shadow group-hover:shadow-md">
                <CardHeader>
                  <item.icon className="mb-2 size-6 text-primary" />
                  <CardTitle>{item.label}</CardTitle>
                  <CardDescription>{item.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-muted/40 p-6">
        <h2 className="text-lg font-semibold">Trudna sytuacja?</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Po stracie dziecka lub ciąży, przy wcześniactwie albo ciężkiej chorobie dziecka znajdziesz oficjalne informacje i
          organizacje, które pomagają rodzicom.
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link href={PUBLIC_PATHS.help}>Pomoc i wsparcie</Link>
        </Button>
      </section>
    </div>
  );
}
