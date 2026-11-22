import { WalletCards } from "lucide-react";
import type { Metadata } from "next";

import { MyBenefitsView } from "@/components/account/my-benefits-view";
import { PageHeading } from "@/components/zus/page-heading";

export const metadata: Metadata = { title: "Moje urlopy i zasiłki" };

export default function AccountPage() {
  return (
    <section className="flex flex-col gap-6">
      <PageHeading title="Moje urlopy i zasiłki" icon={WalletCards}>
        Ile urlopu i zasiłku już wykorzystałeś, ile zostało i do kiedy – oraz co warto zrobić teraz.
      </PageHeading>
      <MyBenefitsView />
    </section>
  );
}
