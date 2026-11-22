"use client";

import { FlaskConical } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  type FamilyProfile,
  type SampleCase,
  listSampleCases,
} from "@/lib/api";

/**
 * "Load a sample case": the user picks one of the ready-made cases (types of cases from the ZUS samples) and the
 * calculator is filled in and run. No files are read – this is a choice from a list, the rest is clicked through.
 */
export function SampleCases({
  onLoad,
}: {
  onLoad: (profile: FamilyProfile) => void;
}) {
  const [cases, setCases] = useState<SampleCase[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    listSampleCases()
      .then(setCases)
      .catch(() => setCases([]));
  }, []);

  if (cases.length === 0) return null;
  const chosen = cases.find((c) => c.id === selected);

  return (
    <details className="border border-border p-4">
      <summary className="flex cursor-pointer items-center gap-2 font-bold">
        <FlaskConical aria-hidden className="size-5 text-icon" />
        Wczytaj przykładową sprawę
      </summary>
      <div className="mt-3 flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">
          Wybierz gotową sprawę (typy spraw z przykładów ZUS: macierzyński,
          ojcowski, wcześniak, bliźnięta, adopcja, odmowy…). Kalkulator wypełni
          się danymi i od razu pokaże wynik – możesz je potem zmienić.
        </p>
        <label className="flex flex-col gap-1 text-sm font-bold">
          Przykładowa sprawa
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="rounded-sm border border-input bg-background px-3 py-2 font-normal"
          >
            <option value="">– wybierz –</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id} – {c.title_pl}
              </option>
            ))}
          </select>
        </label>
        {chosen && <p className="text-sm">{chosen.description_pl}</p>}
        <Button
          type="button"
          disabled={!chosen}
          onClick={() => chosen && onLoad(chosen.profile)}
          className="w-fit"
        >
          Wczytaj i policz
        </Button>
      </div>
    </details>
  );
}
