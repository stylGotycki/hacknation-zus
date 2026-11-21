import type { Citizen } from "@/lib/api";

const OWNER_KEY = "parent-guide:owner";
const CITIZEN_KEY = "parent-guide:citizen";

/** The simulated mObywatel session lives in the browser; logging in replaces the guest id. */
export function loadCitizen(): Citizen | null {
  try {
    const raw = localStorage.getItem(CITIZEN_KEY);
    return raw ? (JSON.parse(raw) as Citizen) : null;
  } catch {
    return null;
  }
}

export function startSession(ownerId: string, citizen: Citizen): void {
  try {
    localStorage.setItem(OWNER_KEY, ownerId);
    localStorage.setItem(CITIZEN_KEY, JSON.stringify(citizen));
    window.dispatchEvent(new Event("parent-guide:session"));
  } catch {
    // Without storage the session cannot be kept; the user simply stays a guest.
  }
}

export function endSession(): void {
  try {
    localStorage.removeItem(CITIZEN_KEY);
    localStorage.removeItem(OWNER_KEY);
    window.dispatchEvent(new Event("parent-guide:session"));
  } catch {
    // Nothing to clean up when storage is blocked.
  }
}
