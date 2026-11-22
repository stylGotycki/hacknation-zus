import type { Metadata } from "next";

import { AdminView } from "@/components/admin/admin-view";

export const metadata: Metadata = { title: "Panel administratora" };

export default function AdminPage() {
  return <AdminView />;
}
