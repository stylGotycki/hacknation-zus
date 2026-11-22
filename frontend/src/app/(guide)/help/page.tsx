import { HeartHandshake, Mail, Phone, Video } from "lucide-react";
import type { Metadata } from "next";

import { HelpView } from "@/components/help/help-view";
import { PageHeading } from "@/components/zus/page-heading";
import { ZUS_CONTACT } from "@/lib/zus-site";

export const metadata: Metadata = { title: "Pomoc i wsparcie" };

export default function HelpPage() {
  return (
    <section className="flex flex-col gap-8">
      <PageHeading title="Pomoc i wsparcie" icon={HeartHandshake}>
        Oficjalne źródła informacji, organizacje wspierające rodziców w szczególnych sytuacjach i symulacja wniosku o odpis aktu urodzenia.
      </PageHeading>
      <section id="kontakt" aria-labelledby="kontakt-title" className="flex flex-col gap-3 border-l-[7px] border-primary bg-muted p-5">
        <h2 id="kontakt-title" className="text-xl font-bold">
          Kontakt z ZUS w sprawach rodzicielskich
        </h2>
        <ul className="grid gap-2 text-[15px] sm:grid-cols-3">
          <li>
            <a href={`mailto:${ZUS_CONTACT.email}`} className="flex items-center gap-2 font-bold text-link hover:underline">
              <Mail className="size-4" /> {ZUS_CONTACT.email}
            </a>
            <span className="text-sm text-muted-foreground">skrzynka dla przyszłych i obecnych rodziców</span>
          </li>
          <li>
            <a href={ZUS_CONTACT.phoneHref} className="flex items-center gap-2 font-bold text-link hover:underline">
              <Phone className="size-4" /> {ZUS_CONTACT.phone}
            </a>
            <span className="text-sm text-muted-foreground">Centrum Kontaktu Klientów</span>
          </li>
          <li>
            <span className="flex items-center gap-2 font-bold">
              <Video className="size-4" /> e-wizyta
            </span>
            <span className="text-sm text-muted-foreground">wideorozmowa z pracownikiem ZUS, placówki ZUS</span>
          </li>
        </ul>
      </section>
      <HelpView />
    </section>
  );
}
