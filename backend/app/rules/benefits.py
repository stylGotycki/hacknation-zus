"""Builds the user-facing list of benefits from the context and the timeline."""

from datetime import date, timedelta

from app.rules.context import Context
from app.rules.dates import weeks_to_days
from app.rules.eligibility import payer_for
from app.rules.models import (
    BenefitResult,
    CareSituation,
    EmploymentType,
    InsuranceKind,
    LeavePeriod,
    ParentProfile,
    Person,
    Situation,
    Status,
)
from app.rules.money import net_estimate

BENEFITS_ACT = "Ustawa zasiłkowa"
LABOR_CODE = "Kodeks pracy"

KIND_TITLE = {
    ("maternity", "mother"): "Zasiłek macierzyński za okres urlopu macierzyńskiego",
    ("maternity", "father"): "Zasiłek macierzyński za przejętą część urlopu macierzyńskiego",
    ("supplementary", "mother"): "Zasiłek za uzupełniający urlop macierzyński",
    ("supplementary", "father"): "Zasiłek za uzupełniający urlop macierzyński",
    ("parental", "mother"): "Zasiłek macierzyński za okres urlopu rodzicielskiego",
    ("parental", "father"): "Zasiłek macierzyński za okres urlopu rodzicielskiego",
    ("paternity", "father"): "Zasiłek macierzyński za okres urlopu ojcowskiego",
}
KIND_BASIS = {
    "maternity": [f"{LABOR_CODE}, art. 180", f"{BENEFITS_ACT}, art. 29 i 31"],
    "supplementary": [f"{LABOR_CODE}, art. 180²", f"{BENEFITS_ACT}, art. 31"],
    "parental": [f"{LABOR_CODE}, art. 182¹ᵃ", f"{BENEFITS_ACT}, art. 31"],
    "paternity": [f"{LABOR_CODE}, art. 182³", f"{BENEFITS_ACT}, art. 29 i 31"],
}


def _documents(ctx: Context, person: Person, kind: str) -> list[str]:
    parent = ctx.parents[person]
    payer = ctx.payers[person]
    child = ctx.profile.child
    docs: list[str] = []
    employee = parent.employment == EmploymentType.EMPLOYEE

    if employee:
        docs.append("Wniosek o udzielenie urlopu (składany do pracodawcy)")
        if kind in ("maternity", "parental") and person == "mother":
            docs.append(
                "Jeśli urlop rodzicielski następuje zaraz po macierzyńskim, "
                "wystarczy jeden wniosek o oba urlopy"
            )
        if payer.who == "zus":
            docs.append("Pracodawca przekaże do ZUS zaświadczenie płatnika składek Z-3")
    else:
        docs.append(
            "Wniosek ZAM o zasiłek macierzyński (od 24.10.2026 jeden formularz zastępuje "
            "dotychczasowe ZAM, ZUR i ZAO)"
        )
        if parent.employment == EmploymentType.CONTRACT and payer.who == "zus":
            docs.append("Zleceniodawca przekaże do ZUS zaświadczenie płatnika składek Z-3a")

    if kind == "maternity" and not child.is_born and child.situation == Situation.BIRTH:
        docs.append("Zaświadczenie lekarskie o przewidywanej dacie porodu (urlop przed porodem)")
    if child.situation == Situation.BIRTH:
        docs.append("Skrócony odpis aktu urodzenia dziecka")
    else:
        docs.append(
            "Zaświadczenie sądu o wszczęciu postępowania lub postanowienie o umieszczeniu dziecka"
        )
    if "stillbirth" in ctx.ent.tags:
        docs.append("Zaświadczenie o urodzeniu martwego dziecka / odpis aktu zgonu")
    if "child_death" in ctx.ent.tags:
        docs.append("Odpis aktu zgonu dziecka")
    if kind == "supplementary":
        docs.append("Zaświadczenie ze szpitala o pobycie dziecka")
        docs.append(
            "Oświadczenie, że drugi rodzic nie skorzysta z uzupełniającego urlopu ani zasiłku"
        )
    if kind == "parental" and ctx.ent.parental_weeks and child.za_zyciem:
        docs.append("Zaświadczenie „Za życiem” (wydłuża urlop rodzicielski)")
    if kind == "paternity":
        docs.append("Wniosek o urlop ojcowski (najpóźniej 7 dni przed rozpoczęciem)")
    return docs


def _deadline(ctx: Context, kind: str, start: date) -> tuple[date | None, int | None, str | None]:
    """Last day to file the leave application; None once the leave has already started."""
    leads = ctx.params.table("application_lead_days")
    if kind not in leads or start <= ctx.today:
        return None, None, None
    lead = int(leads[kind])
    due = start - timedelta(days=lead)
    note = f"Wniosek do pracodawcy najpóźniej {lead} dni przed rozpoczęciem urlopu."
    return due, (due - ctx.today).days, note


def _group(periods: list[LeavePeriod], person: Person, kind: str) -> list[LeavePeriod]:
    return [p for p in periods if p.person == person and p.kind == kind]


def _aggregate(group: list[LeavePeriod]) -> dict:
    days = sum(p.days for p in group)
    totals = [p.total_gross for p in group]
    nets = [p.total_net_estimate for p in group]
    known = all(t is not None for t in totals)
    # Average rate weighted by days (periods can have different rates, e.g. 81.5% and 70%).
    rate = sum((p.rate or 0) * p.days for p in group) / days if days else None
    first = group[0]
    return {
        "weeks": round(days / 7, 2),
        "days": days,
        "rate": round(rate, 4) if rate is not None else None,
        "monthly_gross": first.monthly_gross,
        "total_gross": round(sum(t or 0 for t in totals), 2) if known else None,
        "total_net_estimate": round(sum(n or 0 for n in nets), 2) if known else None,
        "start": min(p.start for p in group),
        "end": max(p.end for p in group),
    }


def _monthly_net(ctx: Context, monthly_gross: float | None) -> tuple[float | None, bool]:
    if monthly_gross is None:
        return None, False
    net = net_estimate(monthly_gross, ctx.params)
    minimum = ctx.params.number("minimum_maternity_benefit_net")
    return (minimum, True) if net < minimum else (net, False)


def allowance_benefits(ctx: Context) -> list[BenefitResult]:
    """Allowances for periods that exist on the timeline, plus 'not eligible' entries."""
    out: list[BenefitResult] = []
    for person in ("mother", "father"):
        if person not in ctx.parents:
            continue
        parent = ctx.parents[person]
        ins = ctx.insurance[person]

        for kind in ("maternity", "supplementary", "parental", "paternity"):
            group = _group(ctx.periods, person, kind)  # type: ignore[arg-type]
            if not group:
                continue
            agg = _aggregate(group)
            monthly_net, raised = _monthly_net(ctx, agg["monthly_gross"])
            payer = ctx.payers[person]
            debt = ctx.debts.get(person)
            reasons: list[str] = [ctx.ent.maternity_note_pl] if kind == "maternity" else []
            if kind == "supplementary":
                reasons = [ctx.ent.supplementary_note_pl]
            if kind == "parental":
                reasons = [
                    f"Wspólna pula urlopu rodzicielskiego: {ctx.ent.parental_weeks} tygodni; "
                    f"po {ctx.plan.father_reserved or 0} tyg. przypada każdemu z rodziców "
                    "wyłącznie (nie można ich przenieść)."
                    if ctx.plan.father_reserved
                    else f"Pula urlopu rodzicielskiego: {ctx.ent.parental_weeks} tygodni."
                ]
                fraction = (
                    ctx.plan.mother_work_fraction
                    if person == "mother"
                    else ctx.plan.father_work_fraction
                )
                if fraction:
                    reasons.append(
                        f"Łączysz urlop z pracą w {fraction * 100:.0f}% etatu: urlop trwa dłużej, "
                        "a zasiłek jest proporcjonalnie niższy."
                    )
            if kind == "paternity":
                reasons = ["14 dni kalendarzowych; liczba dzieci nie wydłuża urlopu."]
            if (
                agg["rate"] is not None
                and abs(agg["rate"] - ctx.params.number("rate_averaged")) < 0.001
            ):
                reasons.append(
                    "Stawka uśredniona 81,5% (wniosek złożony w terminie 21 dni od porodu)."
                )

            status = Status.ELIGIBLE
            if agg["monthly_gross"] is None:
                status = Status.CONDITIONAL
                reasons.append("Podaj średnią podstawę z 12 miesięcy, aby policzyć kwotę.")
            if (
                debt is not None
                and debt.kind in ("blocked", "paid_late", "paid_in_time")
                and debt.note_pl
            ):
                reasons.append(debt.note_pl)
                if debt.kind == "blocked":
                    status = Status.CONDITIONAL

            deadline, days_left, deadline_note = _deadline(ctx, kind, agg["start"])
            out.append(
                BenefitResult(
                    code=f"{kind}_allowance_{person}",
                    person=person,  # type: ignore[arg-type]
                    title_pl=KIND_TITLE[(kind, person)],
                    status=status,
                    summary_pl=_summary(agg, monthly_net),
                    reasons_pl=reasons,
                    legal_basis=KIND_BASIS[kind],
                    weeks=agg["weeks"],
                    days=agg["days"],
                    rate=agg["rate"],
                    monthly_gross=agg["monthly_gross"],
                    monthly_net_estimate=monthly_net,
                    total_gross=agg["total_gross"],
                    total_net_estimate=agg["total_net_estimate"],
                    raised_to_minimum=raised,
                    start=agg["start"],
                    end=agg["end"],
                    payer=payer.who,
                    apply_to_pl=payer.apply_to_pl,
                    documents_pl=_documents(ctx, person, kind),
                    deadline=deadline,
                    days_left=days_left,
                    deadline_note_pl=deadline_note,
                )
            )

        if not ins.insured and person in ("mother", "father"):
            out.append(_not_eligible(ctx, person, parent))  # type: ignore[arg-type]
    return out


def _summary(agg: dict, monthly_net: float | None) -> str:
    text = f"{agg['weeks']:g} tyg. ({agg['days']} dni)"
    if agg["rate"] is not None:
        text += f", {agg['rate'] * 100:g}% podstawy"
    if agg["monthly_gross"] is not None:
        text += f", ok. {agg['monthly_gross']:.2f} zł brutto miesięcznie"
    if agg["total_gross"] is not None:
        text += f", łącznie ok. {agg['total_gross']:.2f} zł brutto"
    return text + "."


def _not_eligible(ctx: Context, person: Person, parent: ParentProfile) -> BenefitResult:
    ins = ctx.insurance[person]
    reasons = list(ins.reasons_pl)
    reasons.append(
        "Zasiłek macierzyński przysługuje, jeśli w dniu porodu (lub przyjęcia dziecka) "
        "podlegasz ubezpieczeniu chorobowemu – nie jest potrzebny żaden minimalny staż."
    )
    if parent.employment in (
        EmploymentType.CONTRACT,
        EmploymentType.SELF_EMPLOYED,
        EmploymentType.COOPERATING,
    ):
        reasons.append(
            "Dobrowolne ubezpieczenie chorobowe trzeba zgłosić przed porodem – "
            "jeśli jeszcze możesz, to zmienia Twoją sytuację."
        )
    return BenefitResult(
        code=f"maternity_allowance_{person}",
        person=person,
        title_pl="Zasiłek macierzyński",
        status=Status.NOT_ELIGIBLE,
        summary_pl="Nie przysługuje – brak ubezpieczenia chorobowego w dniu porodu.",
        reasons_pl=reasons,
        legal_basis=[f"{BENEFITS_ACT}, art. 29"],
    )


# --------------------------------------------------------------------------------------------
# Benefits that are not (only) leave periods
# --------------------------------------------------------------------------------------------


def pregnancy_benefits(ctx: Context) -> list[BenefitResult]:
    out: list[BenefitResult] = []
    mother = ctx.parents.get("mother")
    if mother is None or ctx.profile.child.situation != Situation.BIRTH:
        return out
    ins = ctx.insurance["mother"]
    base = ctx.bases["mother"]
    params = ctx.params
    waiting = params.table("sickness_waiting_days")
    rate = params.number("rate_sickness_pregnancy")
    monthly = round(base.net_base * rate, 2) if base.net_base is not None else None
    payer = payer_for(mother, params)

    if ctx.profile.child.is_born and not mother.on_pregnancy_sick_leave:
        return out

    # Sickness benefit during pregnancy (e-ZLA with code B).
    kind = mother.sickness_insurance
    needed = int(waiting["voluntary" if kind == InsuranceKind.VOLUNTARY else "mandatory"])
    reasons = [
        "Zwolnienie lekarskie e-ZLA w ciąży ma kod literowy „B” – zasiłek wynosi wtedy 100% podstawy.",
        f"Okres zasiłkowy trwa maksymalnie {params.integer('sickness_benefit_period_days')} dni.",
    ]
    if mother.employment == EmploymentType.EMPLOYEE:
        reasons.append(
            f"Przez pierwsze {params.integer('sickness_employer_paid_days')} dni niezdolności w roku "
            "pracodawca wypłaca wynagrodzenie chorobowe, potem zasiłek."
        )
    else:
        reasons.append(
            "Zasiłek przysługuje od pierwszego dnia niezdolności do pracy; powstrzymaj się od pracy."
        )

    if kind == InsuranceKind.NONE or (
        mother.insurance_ended_on is not None and mother.insurance_ended_on < ctx.today
    ):
        status = Status.NOT_ELIGIBLE
        summary = "Zasiłek chorobowy nie przysługuje bez ubezpieczenia chorobowego."
    elif mother.insured_days is None:
        status = Status.CONDITIONAL
        summary = f"Przysługuje po {needed} dniach nieprzerwanego ubezpieczenia – podaj, od ilu dni jesteś ubezpieczona."
    elif mother.insured_days >= needed:
        status = Status.ELIGIBLE
        summary = "Przysługuje 100% podstawy za okres niezdolności do pracy z kodem B."
    else:
        status = Status.CONDITIONAL
        summary = f"Prawo do zasiłku powstanie za {needed - mother.insured_days} dni (okres wyczekiwania {needed} dni)."

    docs = ["Zaświadczenie lekarskie e-ZLA z kodem „B” (trafia do ZUS i pracodawcy elektronicznie)"]
    if mother.employment == EmploymentType.EMPLOYEE:
        if payer.who == "zus":
            docs.append("Pracodawca przekaże do ZUS zaświadczenie Z-3 (lub ZAS-12 na dalszy okres)")
    elif mother.employment == EmploymentType.CONTRACT:
        docs.append(
            "Zaświadczenie płatnika składek Z-3a (przekazuje zleceniodawca, jeśli wypłaca ZUS)"
        )
    else:
        docs.append("Wniosek ZAS-53 o zasiłek chorobowy – składasz sama do ZUS")

    period_days = employer_days = zus_days = None
    total = None
    if mother.sick_leave_start and mother.sick_leave_end and monthly is not None:
        raw_days = (mother.sick_leave_end - mother.sick_leave_start).days + 1
        period_days = min(raw_days, params.integer("sickness_benefit_period_days"))
        if mother.employment == EmploymentType.EMPLOYEE:
            cap = params.integer(
                "employer_sickness_paid_days_over_50" if mother.age_over_50 else "sickness_employer_paid_days"
            )
            employer_days = min(period_days, max(0, cap - mother.sick_days_used_this_year))
            zus_days = period_days - employer_days
            reasons.append(
                f"Za {employer_days} dni zapłaci pracodawca (wynagrodzenie chorobowe, limit {cap} dni "
                f"w roku{', po 50. roku życia' if mother.age_over_50 else ''}), "
                f"za {zus_days} dni zasiłek z ZUS."
            )
        else:
            zus_days = period_days
        total = round(period_days * monthly / params.integer("benefit_days_per_month"), 2)
        if raw_days > period_days:
            reasons.append(f"Okres zasiłkowy obejmuje najwyżej {period_days} dni – dalsze dni nie są płatne.")

    out.append(
        BenefitResult(
            code="sickness_pregnancy",
            person="mother",
            title_pl="Zasiłek chorobowy w ciąży",
            status=status,
            summary_pl=summary,
            reasons_pl=reasons,
            legal_basis=[f"{BENEFITS_ACT}, art. 4, 8 i 11 ust. 2"],
            rate=rate,
            monthly_gross=monthly,
            monthly_net_estimate=net_estimate(monthly, params) if monthly is not None else None,
            days=period_days or params.integer("sickness_benefit_period_days"),
            total_gross=total,
            total_net_estimate=round(total * (1 - params.number("health_contribution_rate")), 2)
            if total is not None
            else None,
            start=mother.sick_leave_start,
            end=mother.sick_leave_end,
            employer_days=employer_days,
            zus_days=zus_days,
            payer=payer.who,
            apply_to_pl=payer.apply_to_pl,
            documents_pl=docs,
        )
    )

    if status != Status.NOT_ELIGIBLE or ins.pregnancy_equivalent is False:
        out.append(
            BenefitResult(
                code="rehabilitation_benefit",
                person="mother",
                title_pl="Świadczenie rehabilitacyjne",
                status=Status.INFO,
                summary_pl="Może przysługiwać po wyczerpaniu zasiłku chorobowego (270 dni), "
                "jeśli leczenie rokuje powrót do zdolności do pracy.",
                reasons_pl=[
                    "Decyzję o prawie do świadczenia wydaje ZUS na podstawie orzeczenia lekarza orzecznika.",
                    "Wysokość zależy od okresu pobierania – sprawdź aktualne stawki na zus.pl.",
                ],
                legal_basis=[f"{BENEFITS_ACT}, art. 18"],
                payer="zus",
                apply_to_pl="Wniosek składasz w ZUS przed upływem okresu zasiłkowego.",
            )
        )

    if ins.pregnancy_equivalent:
        out.append(
            BenefitResult(
                code="maternity_equivalent_allowance",
                person="mother",
                title_pl="Zasiłek w wysokości zasiłku macierzyńskiego",
                status=Status.CONDITIONAL,
                summary_pl="Może przysługiwać do dnia porodu mimo ustania ubezpieczenia – 100% podstawy.",
                reasons_pl=[
                    "Przysługuje, gdy umowa o pracę została rozwiązana w ciąży z powodu upadłości, "
                    "likwidacji lub śmierci pracodawcy albo z naruszeniem prawa (potwierdzonym "
                    "prawomocnym wyrokiem sądu).",
                    "Wypłata trwa do dnia porodu.",
                ],
                legal_basis=[f"{BENEFITS_ACT}, art. 30"],
                rate=params.number("rate_maternity"),
                monthly_gross=round(base.net_base * params.number("rate_maternity"), 2)
                if base.net_base is not None
                else None,
                payer="zus",
                apply_to_pl="Wniosek składasz bezpośrednio w ZUS.",
                documents_pl=[
                    "Dokument potwierdzający przyczynę rozwiązania umowy (np. wyrok sądu)"
                ],
            )
        )
    return out


def _care_limit(care, params) -> tuple[int, str]:
    """Annual limit (days) for the described situation and a Polish explanation."""
    limits = params.table("care_allowance_limits_days")
    ages = params.table("care_allowance_age_limits_years")
    age = care.child_age_years
    if care.situation == CareSituation.FAMILY_MEMBER:
        return int(limits["other"]), "Chory członek rodziny wspólnie z Tobą mieszkający: limit 14 dni w roku."
    if care.situation == CareSituation.HEALTHY_CHILD:
        if age < ages["healthy_child"]:
            return int(limits["child_under_8_or_sick_under_14"]), "Zdrowe dziecko do 8 lat: limit 60 dni."
        if care.child_disabled and age < ages["disabled_child"]:
            return int(limits["disabled_14_17"]), "Dziecko niepełnosprawne 8–17 lat: limit 30 dni."
        return 0, "Na zdrowe dziecko od 8 lat zasiłek nie przysługuje."
    # sick child
    if age < ages["sick_child"]:
        return int(limits["child_under_8_or_sick_under_14"]), "Chore dziecko do 14 lat: limit 60 dni."
    if care.child_disabled and age < ages["disabled_child"]:
        return int(limits["disabled_14_17"]), "Chore dziecko niepełnosprawne 14–17 lat: limit 30 dni."
    if age < ages["disabled_child"] + 1:
        return int(limits["other"]), "Chore dziecko powyżej 14 lat: limit 14 dni."
    return 0, "Dziecko pełnoletnie nie jest objęte zasiłkiem na dziecko."


def care_benefits(ctx: Context) -> list[BenefitResult]:
    if ctx.ent.surviving_children == 0:
        return []
    params = ctx.params
    limits = params.table("care_allowance_limits_days")
    rate = params.number("rate_care_allowance")
    care = ctx.profile.care
    out = []
    for person in ctx.parents:
        if not ctx.insured(person):
            continue
        base = ctx.bases[person]
        monthly = round(base.net_base * rate, 2) if base.net_base is not None else None
        payer = ctx.payers[person]
        general_limit = int(limits["child_under_8_or_sick_under_14"])
        reasons = [
            "Przysługuje, gdy musisz osobiście opiekować się dzieckiem do 8 lat "
            "(m.in. gdy zamknięto żłobek lub przedszkole) albo chorym dzieckiem do 14 lat.",
            f"Limit {general_limit} dni dotyczy całej rodziny łącznie, niezależnie od liczby dzieci "
            "i liczby uprawnionych rodziców.",
            "Co do zasady nie przysługuje, gdy w domu jest inna osoba, która może zająć się "
            "dzieckiem (nie dotyczy chorego dziecka do 2 lat).",
        ]
        status = Status.INFO
        summary = (
            f"Do {general_limit} dni w roku kalendarzowym, {rate * 100:g}% podstawy"
            + (f" (ok. {monthly:.2f} zł brutto miesięcznie)." if monthly is not None else ".")
        )
        days = general_limit
        total = None
        if care is not None:
            limit, why = _care_limit(care, params)
            reasons.insert(0, why)
            cap = int(limits["total_cap"])
            remaining = max(0, min(limit, cap) - care.days_used_this_year)
            if care.situation == CareSituation.FAMILY_MEMBER:
                remaining = max(0, min(remaining, int(limits["other"]) - care.days_used_for_family_members))
            other_can_care = care.other_household_member_available and not (
                care.situation == CareSituation.SICK_CHILD and care.child_age_years < 2
            )
            if limit == 0:
                status, days = Status.NOT_ELIGIBLE, 0
                summary = why
            elif other_can_care:
                status, days = Status.NOT_ELIGIBLE, 0
                summary = "Zasiłek nie przysługuje, bo inny domownik może zająć się opieką."
                reasons.append("Wyjątek dotyczy tylko chorego dziecka do 2 lat.")
            elif remaining == 0:
                status, days = Status.NOT_ELIGIBLE, 0
                summary = f"Limit {limit} dni w tym roku został już wykorzystany przez rodzinę."
            else:
                days = min(care.days_planned, remaining)
                status = Status.ELIGIBLE
                summary = f"Za {days} dni opieki przysługuje {rate * 100:g}% podstawy"
                if monthly is not None:
                    total = round(days * monthly / params.integer("benefit_days_per_month"), 2)
                    summary += f" – ok. {total:.2f} zł brutto."
                else:
                    summary += "."
                if days < care.days_planned:
                    reasons.append(
                        f"Zaplanowano {care.days_planned} dni, ale do limitu zostało {remaining} dni."
                    )
                reasons.append(f"Do wykorzystania w tym roku: {remaining} dni z limitu {limit}.")
        out.append(
            BenefitResult(
                code=f"care_allowance_{person}",
                person=person,
                title_pl="Zasiłek opiekuńczy (gdy dziecko zachoruje)",
                status=status,
                summary_pl=summary,
                reasons_pl=reasons,
                legal_basis=[f"{BENEFITS_ACT}, art. 32–34"],
                days=days,
                rate=rate,
                monthly_gross=monthly,
                monthly_net_estimate=net_estimate(monthly, params) if monthly is not None else None,
                total_gross=total,
                total_net_estimate=round(total * (1 - params.number("health_contribution_rate")), 2)
                if total is not None
                else None,
                payer=payer.who,
                apply_to_pl="Zwolnienie e-ZLA na opiekę wystawia lekarz; informujesz pracodawcę, "
                "a nie-pracownik składa wniosek do ZUS.",
            )
        )
    return out


def fallback_benefit(ctx: Context) -> list[BenefitResult]:
    """Parental benefit ("kosiniakowe") when nobody in the family gets maternity allowance."""
    if any(ctx.insured(person) for person in ctx.parents):
        return []
    params = ctx.params
    weeks = int(params.by_count("parental_benefit_weeks", ctx.ent.surviving_children or 1))
    monthly = params.number("parental_benefit_monthly")
    days = weeks_to_days(weeks)
    return [
        BenefitResult(
            code="parental_benefit",
            person="family",
            title_pl="Świadczenie rodzicielskie („kosiniakowe”)",
            status=Status.CONDITIONAL,
            summary_pl=f"{monthly:.0f} zł miesięcznie przez {weeks} tygodni "
            f"(łącznie ok. {monthly * days / 30:.0f} zł).",
            reasons_pl=[
                "Przysługuje rodzicom, którym nie należy się zasiłek macierzyński "
                "(np. brak ubezpieczenia chorobowego w dniu porodu).",
                "Nie przysługuje, jeśli którekolwiek z rodziców pobiera zasiłek macierzyński.",
                "Kwota jest stała, nie zależy od zarobków.",
            ],
            legal_basis=["Ustawa o świadczeniach rodzinnych (świadczenie rodzicielskie)"],
            weeks=weeks,
            days=days,
            monthly_gross=monthly,
            monthly_net_estimate=monthly,
            total_gross=round(monthly * days / 30, 2),
            total_net_estimate=round(monthly * days / 30, 2),
            payer="municipality",
            apply_to_pl="Wniosek składasz w urzędzie gminy lub ośrodku pomocy społecznej "
            "(właściwy organ sprawdź w gminie).",
            documents_pl=[
                "Wniosek o świadczenie rodzicielskie",
                "Skrócony odpis aktu urodzenia dziecka",
            ],
        )
    ]
