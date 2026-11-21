import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NAV_ITEMS } from "@/lib/nav";
import { PUBLIC_PATHS } from "@/lib/routes";

// Landing page – full copy and visuals come in E9.
export default function HomePage() {
  const tiles = NAV_ITEMS.filter((item) => item.route !== "admin");

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col items-start gap-5">
        <Badge variant="secondary">E9 · strona startowa w przygotowaniu</Badge>
        <h1 className="max-w-3xl text-3xl font-semibold tracking-tight sm:text-5xl">
          Zostajesz rodzicem? Sprawdź, co Ci przysługuje.
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          Urlop macierzyński, rodzicielski i ojcowski, zasiłki i terminy – w jednym miejscu,
          z wnioskami wypełnianymi krok po kroku.
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
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
      </section>
    </div>
  );
}
