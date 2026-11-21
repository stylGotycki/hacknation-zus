/**
 * Thin fetch wrapper for the FastAPI backend.
 * - In the browser: relative `/api/...` (nginx, or the Next.js rewrite, forwards it).
 * - On the server (Server Components): straight to the backend inside the Docker network.
 */
const BASE =
  typeof window === "undefined" ? (process.env.INTERNAL_API_URL ?? "http://localhost:8000") : "";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// --- Types mirroring backend schemas (keep in sync with /api/docs) -----------------------

export type LegalParameter = {
  key: string;
  value: unknown;
  valid_from: string;
  valid_to: string | null;
  description_pl: string;
  legal_basis: string;
};

export type ParametersResponse = { date: string; parameters: LegalParameter[] };
