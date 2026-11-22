import type {
  ApplicationRecord,
  Deadline,
  LeavePeriod,
  Payment,
  Suggestion,
} from "@/lib/api";

export type Lane = "main" | "mother" | "father";

export type TimelineEvent = {
  id: string;
  date: string;
  lane: Lane;
  type: "birth" | "start" | "end" | "deadline" | "application" | "payment";
  /** First start of an uninterrupted block / last end: draws the branch and merge connectors. */
  branch?: boolean;
  title: string;
  lines: string[];
  deadline?: Deadline;
  period?: LeavePeriod;
  application?: ApplicationRecord;
  payment?: Payment;
};

/** Extra data for the details panel: forms to file and applications already filed. */
export type TimelineExtras = {
  suggestions: Suggestion[];
  applications: ApplicationRecord[];
};

export type Segment = { lane: Lane; from: "top" | "dot"; to: "dot" | "bottom" };
