/**
 * Thin fetch wrapper for the FastAPI backend.
 * - In the browser: relative `/api/...` (nginx, or the Next.js rewrite, forwards it).
 * - On the server (Server Components): straight to the backend inside the Docker network.
 */
const BASE =
  typeof window === "undefined"
    ? (process.env.INTERNAL_API_URL ?? "http://localhost:8000")
    : "";

/** Stable anonymous id of this browser; the mObywatel mock (E7) will replace it with a real identity. */
function ownerHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    let id = localStorage.getItem("parent-guide:owner");
    if (!id) {
      id = `guest-${crypto.randomUUID()}`;
      localStorage.setItem("parent-guide:owner", id);
    }
    return { "X-Owner-Id": id };
  } catch {
    return { "X-Owner-Id": "guest" };
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...ownerHeader(),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    let detail: unknown;
    try {
      detail = (JSON.parse(text) as { detail?: unknown }).detail;
    } catch {
      detail = undefined;
    }
    // A plain message from the backend (HTTPException) is shown as is; anything else stays technical.
    throw new Error(
      typeof detail === "string" ? detail : `API ${res.status}: ${text}`,
    );
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}
