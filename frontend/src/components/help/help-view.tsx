import { ExternalLink } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OFFICIAL_LINKS, SUPPORT_DISCLAIMER, SUPPORT_GROUPS } from "@/content/support";
import { PUBLIC_PATHS } from "@/lib/routes";

export function HelpView() {
  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold">Oficjalne informacje</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {OFFICIAL_LINKS.map((link) => (
            <a key={link.href} href={link.href} target="_blank" rel="noopener noreferrer" className="group">
              <Card className="h-full transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-start justify-between gap-2 text-base">
                    {link.title}
                    <ExternalLink className="mt-1 size-4 shrink-0 text-muted-foreground" aria-label="otwiera się w nowej karcie" />
                  </CardTitle>
                  <CardDescription>{link.text}</CardDescription>
                </CardHeader>
              </Card>
            </a>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold">Odpis aktu urodzenia</h2>
        <Card>
          <CardHeader>
            <CardDescription>
              Odpis bywa potrzebny do wniosków o świadczenia. Przećwicz wypełnienie wniosku – to symulacja, nic nie
              trafi do urzędu. Prawdziwy wniosek złożysz na gov.pl.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={`${PUBLIC_PATHS.applications}?form=civil_registry_extract`}>Wypełnij wniosek (symulacja)</Link>
            </Button>
            <Button asChild variant="outline">
              <a href="https://www.gov.pl/web/cyfryzacja/rejestr-stanu-cywilnego" target="_blank" rel="noopener noreferrer">
                Wniosek na gov.pl <ExternalLink />
              </a>
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-xl font-semibold">Wsparcie w trudnych sytuacjach</h2>
          <p className="max-w-2xl text-sm text-muted-foreground">{SUPPORT_DISCLAIMER}</p>
        </div>
        {SUPPORT_GROUPS.map((group) => (
          <div key={group.id} className="flex flex-col gap-3" id={group.id}>
            <div>
              <h3 className="font-medium">{group.title}</h3>
              <p className="max-w-3xl text-sm text-muted-foreground">{group.intro}</p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {group.organizations.map((org) => (
                <li key={org.name} className="rounded-lg border p-4">
                  <p className="font-medium">{org.name}</p>
                  <p className="text-sm text-muted-foreground">{org.text}</p>
                  <p className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    {org.krs && <span>KRS {org.krs}</span>}
                    {org.href && (
                      <a
                        href={org.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary underline-offset-4 hover:underline"
                      >
                        Strona organizacji <ExternalLink className="size-3" />
                      </a>
                    )}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>
    </div>
  );
}
