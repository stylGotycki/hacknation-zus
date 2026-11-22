import { ChevronRight, SearchX } from "lucide-react";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { GuideFrame } from "@/components/zus/guide-frame";
import { PageHeading } from "@/components/zus/page-heading";

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <GuideFrame>
    <section className="flex flex-col items-start gap-6">
      <PageHeading title="Nie znaleziono strony" icon={SearchX}>
        Ta strona nie istnieje albo została przeniesiona.
      </PageHeading>
      <Link href="/" className="inline-flex items-center gap-1 font-bold text-link hover:underline">
        Wróć do przewodnika <ChevronRight className="size-4" />
      </Link>
    </section>
      </GuideFrame>
      <SiteFooter />
    </>
  );
}
