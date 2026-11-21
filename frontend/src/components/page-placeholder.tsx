import { Construction } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";

type Props = {
  title: string;
  description: string;
  epic: string;
  /** Bullet list of what this page will contain – a mini spec for the next epic. */
  planned?: string[];
  children?: ReactNode;
};

/** Shared "coming soon" layout for pages filled in by later epics. */
export function PagePlaceholder({ title, description, epic, planned = [], children }: Props) {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Badge variant="secondary">{epic} · w przygotowaniu</Badge>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
        <p className="max-w-2xl text-muted-foreground">{description}</p>
      </div>

      {planned.length > 0 && (
        <div className="rounded-xl border border-dashed p-5">
          <p className="mb-3 flex items-center gap-2 text-sm font-medium">
            <Construction className="size-4 text-primary" /> Co tu będzie
          </p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {planned.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {children}
    </section>
  );
}
