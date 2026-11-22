import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  title: string;
  /** Large grey line icon above the title, like the illustrations on zus.pl subpages. */
  icon?: LucideIcon;
  children?: ReactNode;
};

/** zus.pl page header: line icon, H1 and an optional lead paragraph. */
export function PageHeading({ title, icon: Icon, children }: Props) {
  return (
    <div className="flex flex-col gap-4">
      {Icon && (
        <Icon
          aria-hidden
          className="size-[72px] text-icon lg:size-[88px]"
          strokeWidth={1}
        />
      )}
      <h1 className="text-[28px] font-bold leading-tight lg:text-[34px]">
        {title}
      </h1>
      {children && (
        <div className="max-w-3xl text-[17px] leading-relaxed text-muted-foreground">
          {children}
        </div>
      )}
    </div>
  );
}
