import {
  Baby,
  Banknote,
  BriefcaseBusiness,
  FileCheck2,
  FileText,
  Heart,
  Hospital,
  Hourglass,
  type LucideIcon,
  Stethoscope,
  UserRound,
  Users,
} from "lucide-react";
import type { LeavePeriod } from "@/lib/api";
import { Lane, TimelineEvent } from "@/components/timeline/model";

// Lane x positions (px) inside the graph column.
export const LANE_X: Record<Lane, number> = {
  main: 20,
  mother: 60,
  father: 100,
};

export const GRAPH_WIDTH = 122;

export const DOT_Y = 30; // px from the top of a row to the centre of its dot

export const LINE = 5; // line thickness (px)

export const TODAY = (() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
})();

export const LANE_COLOR: Record<Lane, string> = {
  main: "bg-[#c9c9c9]",
  mother: "bg-primary",
  father: "bg-info",
};

export const LANE_TEXT: Record<Lane, string> = {
  main: "text-muted-foreground",
  mother: "text-primary",
  father: "text-info",
};

export const LANE_BORDER: Record<Lane, string> = {
  main: "border-muted-foreground",
  mother: "border-primary",
  father: "border-info",
};

export const LANE_ORDER: Record<Lane, number> = {
  main: 0,
  mother: 1,
  father: 2,
};

export const PERSON_NAME = {
  mother: "Mama",
  father: "Tata",
  family: "Rodzina",
} as const;

export const DEADLINE_STYLE = {
  open: {
    border: "border-navy",
    text: "text-navy",
    chip: "bg-muted text-navy",
  },
  soon: {
    border: "border-amber-600",
    text: "text-amber-700",
    chip: "bg-amber-100 text-amber-900",
  },
  overdue: {
    border: "border-destructive",
    text: "text-destructive",
    chip: "bg-destructive/10 text-destructive",
  },
} as const;

export const KIND_ICON: Record<LeavePeriod["kind"], LucideIcon> = {
  pregnancy_sickness: Stethoscope,
  maternity: Heart,
  maternity_equivalent: BriefcaseBusiness,
  supplementary: Hospital,
  parental: Users,
  paternity: UserRound,
};

/** Every kind of event has its own icon inside the dot. */
export function iconFor(event: TimelineEvent): LucideIcon {
  switch (event.type) {
    case "birth":
      return Baby;
    case "end":
      return BriefcaseBusiness; // back to work
    case "application":
      return FileCheck2;
    case "payment":
      return Banknote;
    case "deadline":
      return event.deadline?.kind === "use_by" ? Hourglass : FileText;
    default:
      return event.period?.work_fraction
        ? BriefcaseBusiness
        : KIND_ICON[event.period!.kind];
  }
}
