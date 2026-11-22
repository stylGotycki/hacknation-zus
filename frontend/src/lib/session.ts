import { formFromProfile, stepsFor } from "@/components/calculator/form-model";
import {
  evaluateFamily,
  getGuideState,
  type Citizen,
  type FamilyProfile,
} from "@/lib/api";
import {
  saveLastForm,
  saveLastProfile,
  saveLastResult,
  saveLastStep,
} from "@/lib/last-result";

const OWNER_KEY = "parent-guide:owner";
const CITIZEN_KEY = "parent-guide:citizen";
// Settings of the device, not data of the user: they survive logging out.
const KEEP = [/^parent-guide:a11y-/, /^parent-guide:admin-token$/];

/** The simulated mObywatel session lives in the browser; logging in replaces the guest id. */
export function loadCitizen(): Citizen | null {
  try {
    const raw = localStorage.getItem(CITIZEN_KEY);
    return raw ? (JSON.parse(raw) as Citizen) : null;
  } catch {
    return null;
  }
}

/** Puts what the account saved (calculator answers, step, last result) back into this tab. */
export async function restoreFromAccount(): Promise<void> {
  const state = await getGuideState();
  if (!state.form && !state.profile) return;
  // A ready-made account (demo family) has only the profile: the answers are rebuilt from it and
  // the calculator opens on the result.
  const form = state.form ?? formFromProfile(state.profile as FamilyProfile);
  saveLastForm(form);
  saveLastStep(
    state.form
      ? state.step
      : stepsFor(form as Parameters<typeof stepsFor>[0]).length - 1,
  );
  if (state.profile) {
    saveLastProfile(state.profile);
    try {
      saveLastResult(await evaluateFamily(state.profile as FamilyProfile));
    } catch {
      // A plan that no longer passes the rules: the calculator shows the reason on the result step.
    }
  }
}

export async function startSession(
  ownerId: string,
  citizen: Citizen,
): Promise<void> {
  try {
    clearUserData();
    localStorage.setItem(OWNER_KEY, ownerId);
    localStorage.setItem(CITIZEN_KEY, JSON.stringify(citizen));
  } catch {
    // Without storage the session cannot be kept; the user simply stays a guest.
    return;
  }
  try {
    await restoreFromAccount();
  } catch {
    // The account is still logged in; the calculator simply starts empty.
  }
  window.dispatchEvent(new Event("parent-guide:session"));
}

/** Removes everything the user entered from this browser (their account keeps it on the server). */
function clearUserData(): void {
  for (const storage of [localStorage, sessionStorage]) {
    const keys = Array.from({ length: storage.length }, (_, i) =>
      storage.key(i),
    ).filter(
      (k): k is string =>
        Boolean(k?.startsWith("parent-guide:")) &&
        !KEEP.some((re) => re.test(k!)),
    );
    keys.forEach((k) => storage.removeItem(k));
  }
}

/** Logging out wipes the data from the browser; logging in again brings it back from the account. */
export function endSession(): void {
  try {
    clearUserData();
  } catch {
    // Nothing to clean up when storage is blocked.
  }
  window.dispatchEvent(new Event("parent-guide:session"));
  // A full reload resets every page's state, so nothing of the previous user stays on screen.
  window.location.assign("/");
}

/** In a fresh tab the browser has nothing yet: bring the saved state from the account first. */
export async function ensureRestored(): Promise<void> {
  try {
    if (sessionStorage.getItem("parent-guide:last-form")) return;
    await restoreFromAccount();
  } catch {
    // Offline or storage blocked: pages work with what they have.
  }
}
