import type { Metadata } from "next";

import { PagePlaceholder } from "@/components/page-placeholder";
import { api, type ParametersResponse } from "@/lib/api";

export const metadata: Metadata = { title: "Panel administratora" };
// Always render on request: parameters come from the live database.
export const dynamic = "force-dynamic";

// Objects as "key: value" lines so long tables (e.g. care allowance limits) can wrap.
function formatValue(value: unknown) {
  if (value !== null && typeof value === "object") {
    return Object.entries(value)
      .map(([k, v]) => `${k}: ${v}`)
      .join("\n");
  }
  return String(value);
}

export default async function AdminPage() {
  const today = new Date().toISOString().slice(0, 10);
  const data = await api<ParametersResponse>(`/parameters?date=${today}`).catch(() => null);

  return (
    <PagePlaceholder
      epic="E8"
      title="Panel administratora"
      description="Parametry prawne obowiązujące dziś. Edycja i obieg wniosków pojawią się w E8."
      planned={["Edycja parametrów z datą obowiązywania", "Lista wniosków i zmiana statusów"]}
    >
      {data === null ? (
        <p className="text-sm text-destructive">Nie udało się pobrać parametrów z API.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-4 py-2 font-medium">Parametr</th>
                <th className="px-4 py-2 font-medium">Wartość</th>
                <th className="hidden px-4 py-2 font-medium md:table-cell">Opis</th>
                <th className="px-4 py-2 font-medium">Od</th>
              </tr>
            </thead>
            <tbody>
              {data.parameters.map((p) => (
                <tr key={`${p.key}-${p.valid_from}`} className="border-t align-top">
                  <td className="px-4 py-2 font-mono text-xs">{p.key}</td>
                  <td className="min-w-64 whitespace-pre-line break-words px-4 py-2 font-mono text-xs">
                    {formatValue(p.value)}
                  </td>
                  <td className="hidden min-w-72 px-4 py-2 text-muted-foreground md:table-cell">
                    {p.description_pl}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2">{p.valid_from}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PagePlaceholder>
  );
}
