"use client";

import { Contrast, Type } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

type Setting = "font" | "contrast";
const VALUES: Record<Setting, string> = { font: "large", contrast: "high" };
const storageKey = (s: Setting) => `parent-guide:a11y-${s}`;

function readSetting(s: Setting): boolean {
  try {
    return window.localStorage.getItem(storageKey(s)) === "1";
  } catch {
    return false;
  }
}

function applySetting(s: Setting, on: boolean) {
  const root = document.documentElement;
  if (on) root.dataset[s] = VALUES[s];
  else delete root.dataset[s];
  try {
    window.localStorage.setItem(storageKey(s), on ? "1" : "0");
  } catch {
    /* storage unavailable (private mode) – the toggle still works for this page view */
  }
}

/** The two navy square buttons from the zus.pl header: larger text and high contrast. */
export function AccessibilityToggles({ className }: { className?: string }) {
  const [font, setFont] = useState(false);
  const [contrast, setContrast] = useState(false);

  useEffect(() => {
    const f = readSetting("font");
    const c = readSetting("contrast");
    setFont(f);
    setContrast(c);
    applySetting("font", f);
    applySetting("contrast", c);
  }, []);

  const button =
    "grid size-11 place-items-center rounded-sm bg-navy text-white transition-opacity hover:opacity-90 aria-pressed:ring-2 aria-pressed:ring-orange aria-pressed:ring-offset-2";

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <button
        type="button"
        className={button}
        aria-pressed={font}
        title="Powiększ tekst"
        aria-label="Powiększ tekst"
        onClick={() => {
          setFont(!font);
          applySetting("font", !font);
        }}
      >
        <Type className="size-6" />
      </button>
      <button
        type="button"
        className={button}
        aria-pressed={contrast}
        title="Wysoki kontrast"
        aria-label="Wysoki kontrast"
        onClick={() => {
          setContrast(!contrast);
          applySetting("contrast", !contrast);
        }}
      >
        <Contrast className="size-6" />
      </button>
    </div>
  );
}
