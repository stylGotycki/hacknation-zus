import { ChevronRight, HeartHandshake, Users } from "lucide-react";
import Link from "next/link";

import { PageHeading } from "@/components/zus/page-heading";
import { sideNavItems } from "@/lib/nav";
import { PUBLIC_PATHS } from "@/lib/routes";

const STAGES = [
  {
    title: "Planujesz dziecko",
    text: "Sprawdź, czy masz ubezpieczenie chorobowe w dniu porodu – od tego zależy zasiłek macierzyński.",
  },
  {
    title: "Jesteś w ciąży",
    text: "Zwolnienie z kodem B (100%), urlop przed porodem, ochrona przed zwolnieniem z pracy.",
  },
  {
    title: "Dziecko się urodziło",
    text: "Wybierz wariant zasiłku (81,5% albo 100% i 70%) w ciągu 21 dni i złóż wnioski.",
  },
  {
    title: "Jesteś na urlopie",
    text: "Zobacz, ile urlopu zostało, do kiedy go wykorzystać i jak podzielić się opieką.",
  },
];

/** Landing page of the guide, laid out like a zus.pl section page: icon, H1, list of links. */
export default function HomePage() {
  return (
    <div className="flex flex-col gap-10">
      <PageHeading title="Przewodnik rodzica" icon={Users}>
        Zasiłki i urlopy związane z rodzicielstwem w jednym miejscu: co Ci przysługuje w ciąży i po narodzinach dziecka,
        ile wyniesie zasiłek, ile urlopu zostało, jakie wnioski złożyć, do kiedy i gdzie.
      </PageHeading>

      <section aria-labelledby="stages" className="flex flex-col gap-4">
        <h2 id="stages" className="text-xl font-bold">
          Na jakim etapie jesteś?
        </h2>
        <ol className="grid gap-px border border-border bg-border sm:grid-cols-2">
          {STAGES.map((stage, index) => (
            <li key={stage.title} className="flex flex-col gap-1 bg-background p-5">
              <span className="text-sm font-bold text-primary">Etap {index + 1}</span>
              <span className="font-bold">{stage.title}</span>
              <span className="text-sm text-muted-foreground">{stage.text}</span>
            </li>
          ))}
        </ol>
        <div className="flex flex-wrap gap-3">
          <Link
            href={PUBLIC_PATHS.calculator}
            className="inline-flex h-11 items-center gap-2 rounded-sm bg-primary px-5 font-bold text-white hover:bg-primary-dark"
          >
            Sprawdź swoje uprawnienia <ChevronRight className="size-4" />
          </Link>
          <Link
            href={PUBLIC_PATHS.login}
            className="inline-flex h-11 items-center gap-2 rounded-sm border border-navy px-5 font-bold text-navy hover:bg-navy hover:text-white"
          >
            Pobierz moje dane z ZUS (symulacja) <ChevronRight className="size-4" />
          </Link>
        </div>
      </section>

      <section aria-labelledby="pages">
        <h2 id="pages" className="sr-only">
          Strony przewodnika
        </h2>
        <ul>
          {sideNavItems().map((item) => (
            <li key={item.route} className="border-b border-border">
              <Link href={item.href} className="group block px-2.5 py-4">
                <span className="font-bold text-link group-hover:underline">{item.sideLabel ?? item.label}</span>
                <span className="mt-0.5 block text-sm text-muted-foreground">{item.description}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex gap-4 border-l-[7px] border-primary bg-muted p-5">
        <HeartHandshake aria-hidden className="size-10 shrink-0 text-icon" strokeWidth={1.25} />
        <div>
          <h2 className="font-bold">Trudna sytuacja?</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Po stracie dziecka lub ciąży, przy wcześniactwie albo ciężkiej chorobie dziecka znajdziesz informacje o
            przysługujących świadczeniach i organizacje, które pomagają rodzicom.
          </p>
          <Link href={PUBLIC_PATHS.help} className="mt-2 inline-flex items-center gap-1 text-sm font-bold text-link hover:underline">
            Pomoc i wsparcie <ChevronRight className="size-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
