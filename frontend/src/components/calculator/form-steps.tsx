"use client";

import { ChevronRight } from "lucide-react";
import { Checkbox, Field, Input, Select } from "@/components/ui/form-controls";
import { type EmploymentType } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import {
  EMPLOYMENT,
  Family,
  FormState,
  Outcome,
  ParentForm,
  STEP_TITLE,
  Stage,
  StepId,
  addDays,
  alive,
  fatherInsured,
  insured,
  isBirth,
  motherInsured,
  num,
  todayIso,
} from "@/components/calculator/form-model";

export function Choice<T extends string>({
  legend,
  value,
  options,
  onChange,
  hint,
}: {
  legend: string;
  value: T | null;
  options: [T, string, string?][];
  onChange: (v: T) => void;
  hint?: string;
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-bold">{legend}</legend>
      {hint && <p className="-mt-1 text-xs text-muted-foreground">{hint}</p>}
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map(([id, label, desc]) => (
          <label
            key={id}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-sm border p-3 text-sm",
              value === id
                ? "border-primary bg-primary/5"
                : "border-border hover:border-navy",
            )}
          >
            <input
              type="radio"
              className="mt-0.5 size-4 accent-primary"
              checked={value === id}
              onChange={() => onChange(id)}
            />
            <span className="flex flex-col gap-0.5">
              <span className="font-bold">{label}</span>
              {desc && (
                <span className="text-xs text-muted-foreground">{desc}</span>
              )}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function Stepper({
  steps,
  current,
  onGo,
}: {
  steps: StepId[];
  current: number;
  onGo: (i: number) => void;
}) {
  return (
    <ol
      className="flex flex-wrap gap-x-1 gap-y-2 border-b border-band-border pb-3 text-sm"
      aria-label="Kroki kalkulatora"
    >
      {steps.map((s, i) => (
        <li key={s} className="flex items-center gap-1">
          <button
            type="button"
            disabled={i > current}
            onClick={() => onGo(i)}
            aria-current={i === current ? "step" : undefined}
            className={cn(
              "flex items-center gap-1.5 rounded-sm px-2 py-1",
              i === current
                ? "bg-primary font-bold text-white"
                : i < current
                  ? "text-link hover:underline"
                  : "text-muted-foreground",
            )}
          >
            <span
              className={cn(
                "flex size-5 items-center justify-center rounded-full text-[11px] font-bold",
                i === current
                  ? "bg-white text-primary"
                  : "border border-current",
              )}
            >
              {i + 1}
            </span>
            {STEP_TITLE[s]}
          </button>
          {i < steps.length - 1 && (
            <ChevronRight className="size-3 text-muted-foreground" />
          )}
        </li>
      ))}
    </ol>
  );
}

export type StepProps = {
  f: FormState;
  set: <K extends keyof FormState>(k: K, v: FormState[K]) => void;
};

export function SituationStep({ f, set }: StepProps) {
  return (
    <Choice<Stage>
      legend="Na jakim etapie jesteście?"
      value={f.stage}
      onChange={(v) => {
        set("stage", v);
        if (v !== "born") set("outcome", "alive");
      }}
      options={[
        [
          "pregnancy",
          "Jestem w ciąży",
          "Planujemy urlopy przed porodem – liczymy od przewidywanej daty porodu.",
        ],
        ["born", "Dziecko się urodziło", "Poród już nastąpił."],
        [
          "adoption",
          "Przysposobienie",
          "Przyjęliśmy dziecko (do 14 lat) i wystąpiliśmy do sądu o przysposobienie.",
        ],
        [
          "foster",
          "Rodzina zastępcza",
          "Niezawodowa rodzina zastępcza – dziecko do 7 lat (10 przy odroczeniu obowiązku szkolnego).",
        ],
      ]}
    />
  );
}

export function ChildStep({ f, set }: StepProps) {
  const many = (num(f.children) ?? 1) > 1;
  const today = todayIso();
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field
        label={
          f.stage === "pregnancy"
            ? "Przewidywana data porodu"
            : f.stage === "born"
              ? "Data porodu"
              : "Data przyjęcia dziecka na wychowanie"
        }
        hint={
          f.stage === "pregnancy" ? "Z zaświadczenia lekarskiego." : undefined
        }
      >
        <Input
          type="date"
          value={f.date}
          min={f.stage === "pregnancy" ? today : undefined}
          max={f.stage === "born" ? today : undefined}
          onChange={(e) => set("date", e.target.value)}
        />
      </Field>
      <Field
        label={
          f.stage === "pregnancy"
            ? "Ile dzieci się urodzi?"
            : f.stage === "born"
              ? "Ile dzieci urodziło się przy porodzie?"
              : "Ile dzieci przyjęto jednocześnie?"
        }
      >
        <Input
          inputMode="numeric"
          value={f.children}
          onChange={(e) => set("children", e.target.value)}
        />
      </Field>
      {(f.stage === "adoption" || f.stage === "foster") && (
        <>
          <Field label="Wiek dziecka w dniu przyjęcia (lata)" hint="Np. 2,5">
            <Input
              inputMode="decimal"
              value={f.age}
              onChange={(e) => set("age", e.target.value)}
            />
          </Field>
          {f.stage === "foster" && (
            <Checkbox
              label="Podjęto decyzję o odroczeniu obowiązku szkolnego"
              checked={f.schoolDeferred}
              onChange={(e) => set("schoolDeferred", e.target.checked)}
            />
          )}
        </>
      )}
      {f.stage === "born" && (
        <div className="sm:col-span-2">
          <Choice<Outcome>
            legend="Co się stało po porodzie?"
            value={f.outcome}
            onChange={(v) => set("outcome", v)}
            hint="Wiemy, że to trudne pytanie. Od odpowiedzi zależy długość urlopu i dokumenty."
            options={[
              ["alive", many ? "Dzieci żyją" : "Dziecko żyje"],
              [
                "stillborn",
                "Dziecko urodziło się martwe",
                "Urlop macierzyński 8 tygodni i zasiłek pogrzebowy.",
              ],
              ["died", "Dziecko zmarło po porodzie"],
            ]}
          />
        </div>
      )}
      {f.stage === "born" && f.outcome === "died" && (
        <Field label="Data zgonu dziecka">
          <Input
            type="date"
            value={f.diedOn}
            min={f.date}
            max={today}
            onChange={(e) => set("diedOn", e.target.value)}
          />
        </Field>
      )}
      {f.stage === "born" && f.outcome !== "alive" && many && (
        <Field label="Ile dzieci żyje?">
          <Input
            inputMode="numeric"
            value={f.surviving}
            onChange={(e) => set("surviving", e.target.value)}
          />
        </Field>
      )}
      {f.outcome !== "stillborn" && (
        <Checkbox
          label="Zaświadczenie „Za życiem”"
          hint="Ciężkie i nieodwracalne upośledzenie albo nieuleczalna choroba – dłuższy urlop rodzicielski (65 / 67 tygodni)."
          checked={f.zaZyciem}
          onChange={(e) => set("zaZyciem", e.target.checked)}
          className="sm:col-span-2"
        />
      )}
      {f.stage === "born" && f.outcome !== "stillborn" && (
        <>
          <Checkbox
            label="Wcześniak albo dziecko w szpitalu po porodzie"
            hint="Uzupełniający urlop macierzyński: do 8 albo 15 tygodni."
            checked={f.premature}
            onChange={(e) => set("premature", e.target.checked)}
            className="sm:col-span-2"
          />
          {f.premature && (
            <div className="grid gap-4 sm:col-span-2 sm:grid-cols-4">
              <Field label="Tydzień ciąży przy porodzie">
                <Input
                  inputMode="numeric"
                  value={f.gestation}
                  onChange={(e) => set("gestation", e.target.value)}
                />
              </Field>
              <Field label="Masa urodzeniowa (g)">
                <Input
                  inputMode="numeric"
                  value={f.weight}
                  onChange={(e) => set("weight", e.target.value)}
                />
              </Field>
              <Field label="Dni pobytu w szpitalu">
                <Input
                  inputMode="numeric"
                  value={f.hospitalDays}
                  onChange={(e) => set("hospitalDays", e.target.value)}
                />
              </Field>
              <Field
                label="Od którego dnia po porodzie?"
                hint="Ważne przy porodzie w terminie (od 5. do 28. dnia)."
              >
                <Input
                  inputMode="numeric"
                  value={f.hospitalFirstDay}
                  onChange={(e) => set("hospitalFirstDay", e.target.value)}
                />
              </Field>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function FamilyStep({ f, set }: StepProps) {
  if (isBirth(f))
    return (
      <Choice<Family>
        legend="Czy w rodzinie jest tata, który może korzystać z urlopów i zasiłków?"
        value={f.family === "father" ? "both" : f.family}
        onChange={(v) => set("family", v)}
        options={[
          [
            "both",
            "Tak – mama i tata",
            "Pokażemy podział urlopów i uprawnienia taty.",
          ],
          [
            "mother",
            "Nie – tylko mama",
            "Nie będziemy pytać o tatę ani o podział urlopów.",
          ],
        ]}
      />
    );
  return (
    <Choice<Family>
      legend="Kto przyjmuje dziecko na wychowanie?"
      value={f.family}
      onChange={(v) => set("family", v)}
      options={[
        ["both", "Mama i tata"],
        ["mother", "Tylko mama"],
        ["father", "Tylko tata"],
      ]}
    />
  );
}

export function ParentStep({
  f,
  set,
  who,
}: StepProps & { who: "mother" | "father" }) {
  const p = f[who];
  const upd = (patch: Partial<ParentForm>) => set(who, { ...p, ...patch });
  const employee = p.employment === "employee";
  const business =
    p.employment === "self_employed" || p.employment === "cooperating";
  const mother = who === "mother";
  const event =
    f.stage === "pregnancy"
      ? "porodu"
      : f.stage === "born"
        ? "porodu"
        : "przyjęcia dziecka";
  return (
    <div className="flex flex-col gap-4">
      <Field
        label={`Podstawa ubezpieczenia ${mother ? "mamy" : "taty"} w dniu ${event}`}
      >
        <Select
          value={p.employment}
          onChange={(e) =>
            upd({ employment: e.target.value as EmploymentType })
          }
        >
          {EMPLOYMENT.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </Select>
      </Field>
      {(p.employment === "contract" || business) && (
        <Checkbox
          label="Opłacam dobrowolne ubezpieczenie chorobowe"
          hint="Bez ubezpieczenia chorobowego w dniu porodu zasiłek macierzyński nie przysługuje. Zgłoszenia nie można złożyć wstecz."
          checked={p.voluntary}
          onChange={(e) => upd({ voluntary: e.target.checked })}
        />
      )}
      {p.employment === "self_employed" && (
        <Checkbox
          label="Korzystam z ulgi na start"
          hint="W uldze na start nie ma ubezpieczeń społecznych – także chorobowego."
          checked={p.startRelief}
          onChange={(e) => upd({ startRelief: e.target.checked })}
        />
      )}
      {p.employment === "other" && (
        <Checkbox
          label="Podlegam ubezpieczeniu chorobowemu"
          checked={p.otherInsured}
          onChange={(e) => upd({ otherInsured: e.target.checked })}
        />
      )}
      {(employee || p.employment === "unemployed") && (
        <Checkbox
          label={`${mother ? "Jestem" : "Tata jest"} na urlopie wychowawczym (z poprzednim dzieckiem)`}
          hint="Poród w czasie urlopu wychowawczego daje prawo do zasiłku macierzyńskiego."
          checked={p.childcareLeave}
          onChange={(e) => upd({ childcareLeave: e.target.checked })}
        />
      )}
      {insured(p) && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label={
              employee
                ? "Przeciętne miesięczne wynagrodzenie brutto (zł)"
                : "Przeciętna podstawa składki chorobowej (zł)"
            }
            hint="Z 12 miesięcy przed miesiącem porodu (albo z pełnych miesięcy ubezpieczenia)."
          >
            <Input
              inputMode="decimal"
              value={p.base}
              onChange={(e) => upd({ base: e.target.value })}
            />
          </Field>
          <Field
            label="Albo kwoty z kolejnych miesięcy (opcjonalnie)"
            hint="Oddziel spacją, do 12 wartości – policzymy średnią."
          >
            <Input
              value={p.history}
              onChange={(e) => upd({ history: e.target.value })}
              placeholder="np. 6000 6200 5800"
            />
          </Field>
          {(employee || p.employment === "contract") && (
            <Field
              label="Ilu ubezpieczonych zgłasza płatnik składek?"
              hint="Powyżej 20 osób zasiłek wypłaca pracodawca, w pozostałych przypadkach ZUS."
            >
              <Select
                value={p.payer}
                onChange={(e) =>
                  upd({ payer: e.target.value as ParentForm["payer"] })
                }
              >
                <option value="over20">Więcej niż 20</option>
                <option value="upTo20">20 lub mniej</option>
              </Select>
            </Field>
          )}
          {employee && (
            <div className="flex flex-col gap-2">
              <Checkbox
                label="Pracuję w niepełnym wymiarze"
                checked={p.partTime}
                onChange={(e) => upd({ partTime: e.target.checked })}
              />
              {p.partTime && (
                <Field label="Wymiar etatu (%)">
                  <Input
                    inputMode="numeric"
                    value={p.fraction}
                    onChange={(e) => upd({ fraction: e.target.value })}
                  />
                </Field>
              )}
            </div>
          )}
          {business && (
            <>
              <Field
                label="Zadłużenie z tytułu składek (zł)"
                hint="Powyżej 1% płacy minimalnej zasiłek jest wstrzymany do spłaty."
              >
                <Input
                  inputMode="decimal"
                  value={p.debt}
                  onChange={(e) => upd({ debt: e.target.value })}
                />
              </Field>
              {(num(p.debt) ?? 0) > 0 && (
                <Field label="Dzień spłaty zadłużenia (jeśli spłacone)">
                  <Input
                    type="date"
                    value={p.debtPaidOn}
                    onChange={(e) => upd({ debtPaidOn: e.target.value })}
                  />
                </Field>
              )}
            </>
          )}
        </div>
      )}
      {mother && isBirth(f) && employee && (
        <Checkbox
          label="Umowa o pracę ustała w czasie ciąży"
          hint="Np. upadłość lub likwidacja pracodawcy, rozwiązanie z naruszeniem prawa, koniec umowy na czas określony."
          checked={p.ended}
          onChange={(e) => upd({ ended: e.target.checked })}
        />
      )}
      {mother && isBirth(f) && employee && p.ended && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Ostatni dzień ubezpieczenia">
            <Input
              type="date"
              value={p.endedOn}
              onChange={(e) => upd({ endedOn: e.target.value })}
            />
          </Field>
          <Field label="Przyczyna">
            <Select
              value={p.endReason}
              onChange={(e) =>
                upd({ endReason: e.target.value as ParentForm["endReason"] })
              }
            >
              <option value="employer_bankruptcy">
                Upadłość, likwidacja albo śmierć pracodawcy
              </option>
              <option value="unlawful_dismissal">
                Rozwiązanie z naruszeniem prawa (wyrok sądu)
              </option>
              <option value="other">Inna przyczyna</option>
            </Select>
          </Field>
          <Checkbox
            label="Umowa na czas określony przedłużona do dnia porodu"
            hint="Umowa, która skończyłaby się po 3. miesiącu ciąży, przedłuża się do porodu (art. 177 § 3 KP)."
            checked={p.fixedTerm}
            onChange={(e) => upd({ fixedTerm: e.target.checked })}
            className="sm:col-span-2"
          />
        </div>
      )}
      {mother && isBirth(f) && insured(p) && (
        <>
          <Checkbox
            label="Zwolnienie lekarskie w ciąży (kod B)"
            checked={p.sick}
            onChange={(e) => upd({ sick: e.target.checked })}
          />
          {p.sick && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Zwolnienie od">
                <Input
                  type="date"
                  value={p.sickStart}
                  onChange={(e) => upd({ sickStart: e.target.value })}
                />
              </Field>
              <Field label="Zwolnienie do">
                <Input
                  type="date"
                  value={p.sickEnd}
                  onChange={(e) => upd({ sickEnd: e.target.value })}
                />
              </Field>
              {employee && (
                <>
                  <Field label="Dni chorobowego już opłaconych przez pracodawcę w tym roku">
                    <Input
                      inputMode="numeric"
                      value={p.sickUsed}
                      onChange={(e) => upd({ sickUsed: e.target.value })}
                    />
                  </Field>
                  <Checkbox
                    label="Ukończyłam 50 lat (w poprzednim roku)"
                    hint="Pracodawca płaci wtedy 14 dni zamiast 33."
                    checked={p.over50}
                    onChange={(e) => upd({ over50: e.target.checked })}
                  />
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function DifficultStep({ f, set }: StepProps) {
  const mInsured = motherInsured(f);
  const options: [FormState["difficult"], string, string?][] = [
    ["none", "Nie dotyczy", "Najczęstsza sytuacja."],
    [
      "hospital",
      "Mama przebywa w szpitalu",
      mInsured
        ? "Po co najmniej 8 tygodniach urlopu – na ten czas urlop wykorzystuje tata."
        : undefined,
    ],
    [
      "disabled",
      "Mama ma orzeczenie o niezdolności do samodzielnej egzystencji",
    ],
    ["death", "Mama zmarła"],
    ["abandoned", "Mama porzuciła dziecko"],
  ];
  if (!mInsured)
    options.push([
      "employed",
      "Mama (bez ubezpieczenia) podjęła pracę",
      "Co najmniej na pół etatu – zasiłek dla taty na czas jej pracy.",
    ]);
  return (
    <div className="flex flex-col gap-4">
      <Choice
        legend="Czy wydarzyło się coś, przez co mama nie może opiekować się dzieckiem?"
        value={f.difficult}
        onChange={(v) => set("difficult", v)}
        options={options}
      />
      {f.difficult !== "none" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label={
              f.difficult === "hospital"
                ? "Przyjęcie do szpitala"
                : f.difficult === "employed"
                  ? "Początek pracy"
                  : "Data zdarzenia"
            }
          >
            <Input
              type="date"
              value={f.difficultFrom}
              min={f.date}
              onChange={(e) => set("difficultFrom", e.target.value)}
            />
          </Field>
          {(f.difficult === "hospital" || f.difficult === "employed") && (
            <Field
              label={
                f.difficult === "hospital"
                  ? "Wypis (jeśli znany)"
                  : "Koniec pracy (jeśli znany)"
              }
            >
              <Input
                type="date"
                value={f.difficultTo}
                min={f.difficultFrom}
                onChange={(e) => set("difficultTo", e.target.value)}
              />
            </Field>
          )}
        </div>
      )}
    </div>
  );
}

export function PlanStep({ f, set }: StepProps) {
  const m = motherInsured(f);
  const t = fatherInsured(f);
  const both = m && t;
  const takenIn = f.stage === "adoption" || f.stage === "foster";
  const deadline21 = f.date ? addDays(f.date, 21) : "";
  const averagedOpen =
    f.stage === "pregnancy" || (f.date !== "" && todayIso() <= deadline21);
  const supplementaryPossible =
    f.stage === "born" && f.premature && (num(f.hospitalDays) ?? 0) > 0;
  const noDifficulty = f.difficult === "none";
  return (
    <div className="flex flex-col gap-6">
      {f.stage === "pregnancy" && m && (
        <Field
          label="Ile tygodni urlopu macierzyńskiego mama weźmie przed porodem?"
          hint="Od 0 do 6 tygodni – wliczają się do 20 tygodni urlopu."
        >
          <Select
            value={f.beforeBirthWeeks}
            onChange={(e) => set("beforeBirthWeeks", e.target.value)}
          >
            {[0, 1, 2, 3, 4, 5, 6].map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </Select>
        </Field>
      )}
      {both && !takenIn && noDifficulty && f.outcome === "alive" && (
        <Field
          label="Ile tygodni urlopu macierzyńskiego przejmie tata?"
          hint="Mama musi wykorzystać po porodzie co najmniej 14 tygodni; tata bierze resztę."
        >
          <Input
            inputMode="numeric"
            value={f.toFatherWeeks}
            onChange={(e) => set("toFatherWeeks", e.target.value)}
          />
        </Field>
      )}
      {both && f.outcome !== "died" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label="Ile tygodni urlopu rodzicielskiego weźmie tata?"
            hint="9 tygodni jest tylko dla taty – nie można ich przekazać mamie."
          >
            <Input
              inputMode="numeric"
              value={f.fatherParentalWeeks}
              onChange={(e) => set("fatherParentalWeeks", e.target.value)}
            />
          </Field>
          <Field
            label="Od kiedy urlop rodzicielski taty?"
            hint="Puste = zaraz po urlopie mamy. Można też równolegle z mamą."
          >
            <Input
              type="date"
              value={f.fatherParentalStart}
              onChange={(e) => set("fatherParentalStart", e.target.value)}
            />
          </Field>
        </div>
      )}
      {t && !m && (
        <p className="rounded-sm bg-muted p-3 text-sm">
          Mama nie ma tytułu do zasiłku – tata może wykorzystać cały urlop
          rodzicielski i (osobno) urlop ojcowski.
        </p>
      )}
      {t &&
        (f.stage === "pregnancy" ||
          f.stage === "born" ||
          f.stage === "adoption") && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Początek urlopu ojcowskiego"
              hint="2 tygodnie do ukończenia przez dziecko 12 miesięcy. Puste = od dnia porodu."
            >
              <Input
                type="date"
                value={f.paternityStart}
                onChange={(e) => set("paternityStart", e.target.value)}
              />
            </Field>
            <Field label="Urlop ojcowski w częściach">
              <Select
                value={f.paternityParts}
                onChange={(e) =>
                  set("paternityParts", e.target.value as "1" | "2")
                }
              >
                <option value="1">Jednorazowo</option>
                <option value="2">W 2 częściach (po tygodniu)</option>
              </Select>
            </Field>
          </div>
        )}
      {(["mother", "father"] as const).map((who) => {
        const p = f[who];
        if (
          !(who === "mother" ? m : t) ||
          p.employment !== "employee" ||
          f.outcome === "died"
        )
          return null;
        return (
          <Field
            key={who}
            label={`Czy ${who === "mother" ? "mama" : "tata"} będzie pracować w czasie urlopu rodzicielskiego? (% etatu)`}
            hint="0 = pełny urlop. Najwyżej 50% etatu – urlop wydłuża się proporcjonalnie, zasiłek jest niższy."
          >
            <Select
              value={p.workPercent}
              onChange={(e) => set(who, { ...p, workPercent: e.target.value })}
            >
              {[0, 10, 20, 25, 30, 40, 50].map((v) => (
                <option key={v} value={v}>
                  {v}%
                </option>
              ))}
            </Select>
          </Field>
        );
      })}
      {supplementaryPossible && (
        <div className="flex flex-col gap-3">
          <Checkbox
            label="Skorzystamy z uzupełniającego urlopu macierzyńskiego"
            hint="Bezpośrednio po urlopie macierzyńskim, jednorazowo, przez jedno z rodziców."
            checked={f.supplementary}
            onChange={(e) => set("supplementary", e.target.checked)}
          />
          {f.supplementary && both && (
            <Field label="Kto weźmie urlop uzupełniający?">
              <Select
                value={f.supplementaryBy}
                onChange={(e) =>
                  set("supplementaryBy", e.target.value as "mother" | "father")
                }
              >
                <option value="mother">Mama</option>
                <option value="father">Tata</option>
              </Select>
            </Field>
          )}
        </div>
      )}
      {f.outcome !== "died" && (m || (takenIn && t)) && (
        <div className="flex flex-col gap-3">
          {averagedOpen ? (
            <Checkbox
              label="Złożę wniosek o zasiłek w stałej stawce 81,5%"
              hint={`Za cały urlop macierzyński i rodzicielski zamiast 100% + 70%. Wniosek najpóźniej 21 dni po ${takenIn ? "przyjęciu dziecka" : "porodzie"}${deadline21 ? ` (do ${formatDate(deadline21)})` : ""}.`}
              checked={f.averaged}
              onChange={(e) => set("averaged", e.target.checked)}
            />
          ) : (
            <>
              <Checkbox
                label="Wniosek o stawkę 81,5% został złożony w ciągu 21 dni"
                hint="Termin minął – jeśli wniosku nie było, zasiłek wynosi 100% za macierzyński i 70% za rodzicielski."
                checked={f.averaged}
                onChange={(e) => set("averaged", e.target.checked)}
              />
              {f.averaged && (
                <Field label="Data złożenia wniosku">
                  <Input
                    type="date"
                    value={f.averagedAppliedOn}
                    onChange={(e) => set("averagedAppliedOn", e.target.value)}
                  />
                </Field>
              )}
            </>
          )}
        </div>
      )}
      <details className="text-sm">
        <summary className="cursor-pointer font-bold text-link">
          Więcej opcji
        </summary>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          {m && (
            <Field
              label="Początek urlopu rodzicielskiego mamy"
              hint="Puste = zaraz po macierzyńskim."
            >
              <Input
                type="date"
                value={f.motherParentalStart}
                onChange={(e) => set("motherParentalStart", e.target.value)}
              />
            </Field>
          )}
          {m && (
            <Field
              label="Na ile części mama dzieli urlop rodzicielski?"
              hint="Najwyżej 5."
            >
              <Input
                inputMode="numeric"
                value={f.partsMother}
                onChange={(e) => set("partsMother", e.target.value)}
              />
            </Field>
          )}
          {t && (
            <Field
              label="Na ile części tata dzieli urlop rodzicielski?"
              hint="Najwyżej 5."
            >
              <Input
                inputMode="numeric"
                value={f.partsFather}
                onChange={(e) => set("partsFather", e.target.value)}
              />
            </Field>
          )}
        </div>
      </details>
    </div>
  );
}
