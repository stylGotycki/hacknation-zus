"""Risks and warnings: situations in which benefits can be lost, reduced or delayed."""

from datetime import timedelta

from app.rules.context import Context
from app.rules.models import (
    AveragedRateComparison,
    EmploymentType,
    InsuranceKind,
    Risk,
    Situation,
)

SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def build_risks(ctx: Context, averaged: AveragedRateComparison | None) -> list[Risk]:
    risks: list[Risk] = []
    params = ctx.params
    child = ctx.profile.child
    event = ctx.event
    today = ctx.today

    def add(code, severity, person, title, text, basis=None):
        risks.append(
            Risk(
                code=code,
                severity=severity,
                person=person,
                title_pl=title,
                text_pl=text,
                legal_basis=basis,
            )
        )

    for person, parent in ctx.parents.items():
        who = "Matka" if person == "mother" else "Ojciec"
        ins = ctx.insurance[person]
        ended = parent.insurance_ended_on

        if not ins.insured and ended is not None and ended >= today:
            add(
                f"insurance_ends_before_event_{person}",
                "high",
                person,
                f"{who}: ubezpieczenie ustanie przed porodem",
                f"Ubezpieczenie chorobowe kończy się {ended:%d.%m.%Y}, a poród przewidziano na "
                f"{event:%d.%m.%Y}. Utrata ubezpieczenia przed porodem oznacza utratę zasiłku macierzyńskiego.",
                "Ustawa zasiłkowa, art. 29–30",
            )
        elif not ins.insured:
            add(
                f"no_insurance_{person}",
                "high",
                person,
                f"{who}: brak ubezpieczenia chorobowego w dniu porodu",
                "Bez ubezpieczenia chorobowego w tym dniu zasiłek macierzyński nie przysługuje. "
                "Rozwiąż to przed porodem (np. dobrowolne ubezpieczenie chorobowe) albo sprawdź "
                "świadczenie rodzicielskie.",
                "Ustawa zasiłkowa, art. 29",
            )

        debt = ctx.debts.get(person)
        if debt is not None and debt.kind == "blocked":
            add(
                f"contribution_debt_{person}",
                "high",
                person,
                f"{who}: zadłużenie składkowe blokuje zasiłek",
                f"Zadłużenie {debt.amount:.2f} zł przekracza próg {debt.threshold:.2f} zł (1% płacy minimalnej). "
                "Zasiłek zostanie wypłacony dopiero po spłacie. Spłata w ciągu 6 miesięcy daje prawo do zasiłku "
                "za cały okres, później – od dnia spłaty. Raty płacone w terminie nie są zadłużeniem.",
                "Ustawa zasiłkowa – do weryfikacji artykułu",
            )
        elif debt is not None and debt.kind == "paid_late":
            add(
                f"contribution_debt_late_{person}",
                "medium",
                person,
                f"{who}: spłata zadłużenia po terminie skraca okres zasiłku",
                debt.note_pl or "",
                "Ustawa zasiłkowa – do weryfikacji artykułu",
            )

        if parent.base_raised_in_pregnancy:
            add(
                f"raised_base_{person}",
                "medium",
                person,
                f"{who}: podwyższona podstawa składek w ciąży",
                "ZUS może uznać, że podwyższenie podstawy składek w ciąży miało wyłącznie na celu uzyskanie "
                "wyższego zasiłku i ustalić niższą podstawę. Podstawa powinna odpowiadać rzeczywistym przychodom.",
                "Ustawa zasiłkowa – do weryfikacji artykułu",
            )

        if (
            parent.employment
            in (EmploymentType.CONTRACT, EmploymentType.SELF_EMPLOYED, EmploymentType.COOPERATING)
            and parent.sickness_insurance == InsuranceKind.VOLUNTARY
            and parent.insured_days is not None
            and parent.insured_days < params.lookup("sickness_waiting_days", "voluntary")
        ):
            add(
                f"fresh_insurance_{person}",
                "info",
                person,
                f"{who}: świeżo zgłoszone ubezpieczenie",
                "Umowa lub działalność rozpoczęta tuż przed porodem wyłącznie po to, by uzyskać zasiłek, "
                "może zostać zakwestionowana przez ZUS jako pozorna. Warto mieć dokumenty potwierdzające "
                "rzeczywiste wykonywanie pracy.",
                "Ustawa o systemie ubezpieczeń społecznych – do weryfikacji artykułu",
            )

        if parent.employment == EmploymentType.EMPLOYEE:
            if parent.fixed_term_contract and person == "mother":
                add(
                    "fixed_term_extended",
                    "info",
                    person,
                    "Umowa na czas określony przedłuża się do dnia porodu",
                    "Umowa na czas określony lub na okres próbny dłuższy niż miesiąc, która skończyłaby się "
                    "po upływie 3. miesiąca ciąży, jest przedłużana do dnia porodu.",
                    "Kodeks pracy, art. 177",
                )
            add(
                f"dismissal_protection_{person}",
                "info",
                person,
                f"{who}: ochrona przed zwolnieniem",
                "Pracodawca nie może wypowiedzieć umowy w ciąży ani w czasie urlopów rodzicielskich, "
                "a od dnia złożenia wniosku o urlop – do jego końca. Ochrona nie dotyczy osób, które "
                "nie są pracownikami.",
                "Kodeks pracy, art. 177 i 1868",
            )
            if parent.employer_insured_count is None:
                add(
                    f"employer_size_unknown_{person}",
                    "info",
                    person,
                    f"{who}: nie wiemy, kto wypłaci zasiłek",
                    f"Podaj, ilu ubezpieczonych zgłasza pracodawca: powyżej {params.integer('payer_threshold_insured')} "
                    "wypłaca on sam, w przeciwnym razie zasiłek wypłaca ZUS.",
                    "Ustawa zasiłkowa, art. 61",
                )

        fraction = (
            ctx.plan.mother_work_fraction if person == "mother" else ctx.plan.father_work_fraction
        )
        if fraction:
            add(
                f"work_during_parental_{person}",
                "info",
                person,
                f"{who}: praca w czasie urlopu rodzicielskiego",
                f"Pracujesz w {fraction * 100:.0f}% etatu: urlop wydłuża się proporcjonalnie, a zasiłek maleje "
                "proporcjonalnie do wymiaru pracy. Możliwe tylko u tego samego pracodawcy i do połowy etatu.",
                "Kodeks pracy, art. 186⁴; ustawa zasiłkowa, art. 31 ust. 4a",
            )

    # --- Parental leave rules -----------------------------------------------------------------
    plan = ctx.plan
    if ctx.ent.parental_weeks:
        if plan.father_reserved:
            add(
                "reserved_weeks",
                "medium",
                "family",
                f"{plan.father_reserved} tygodni urlopu rodzicielskiego przepada, jeśli z niego nie skorzystasz",
                f"Każdemu z rodziców przysługuje wyłącznie {plan.father_reserved} tygodni urlopu rodzicielskiego. "
                "Tej części nie można przenieść na drugiego rodzica.",
                "Kodeks pracy, art. 182¹ᵃ",
            )
        if ctx.ent.parental_deadline is not None:
            last_end = max((p.end for p in ctx.periods if p.kind == "parental"), default=None)
            if last_end is not None and last_end > ctx.ent.parental_deadline:
                add(
                    "parental_deadline_exceeded",
                    "high",
                    "family",
                    "Urlop rodzicielski wykracza poza dopuszczalny termin",
                    f"Urlop rodzicielski trzeba wykorzystać do {ctx.ent.parental_deadline:%d.%m.%Y}, "
                    f"a plan kończy się {last_end:%d.%m.%Y}.",
                    "Kodeks pracy, art. 182¹ᵃ",
                )
            else:
                add(
                    "parental_deadline",
                    "info",
                    "family",
                    "Do kiedy wykorzystać urlop rodzicielski",
                    f"Urlop rodzicielski można wykorzystać do {ctx.ent.parental_deadline:%d.%m.%Y} "
                    f"(do końca roku, w którym dziecko skończy {params.integer('parental_deadline_child_age_years')} lat), "
                    f"w nie więcej niż {params.integer('parental_max_parts')} częściach.",
                    "Kodeks pracy, art. 182¹ᵃ",
                )

    if (
        child.situation == Situation.BIRTH
        and ctx.ent.surviving_children > 0
        and "mother" in ctx.parents
    ):
        add(
            "mother_mandatory",
            "info",
            "mother",
            f"Matka musi wykorzystać {params.integer('maternity_mother_mandatory_weeks')} tygodni po porodzie",
            "Dopiero po tym okresie matka może zrezygnować z reszty urlopu macierzyńskiego na rzecz ojca "
            "(od razu po 14 tygodniach – wtedy ojciec przejmuje dalszą część).",
            "Kodeks pracy, art. 180",
        )

    # --- Deadlines of applications --------------------------------------------------------------
    for period in ctx.periods:
        lead_key = {
            "parental": "parental",
            "paternity": "paternity",
            "supplementary": "supplementary",
        }.get(period.kind)
        if lead_key is None:
            continue
        lead = int(params.table("application_lead_days")[lead_key])
        due = period.start - timedelta(days=lead)
        if due < today <= period.start and period.person in ctx.parents:
            add(
                f"application_late_{period.id}",
                "high",
                period.person,
                f"Termin na wniosek o {period.label_pl.lower()} minął",
                f"Wniosek należy złożyć co najmniej {lead} dni przed rozpoczęciem urlopu ({due:%d.%m.%Y}). "
                "Złóż go jak najszybciej i ustal z pracodawcą późniejszy początek urlopu.",
                "Kodeks pracy – do weryfikacji artykułu",
            )

    # --- Averaged rate (81.5%) ------------------------------------------------------------------
    if averaged is not None:
        add(
            "averaged_rate",
            "medium" if averaged.still_possible else "info",
            "mother",
            "Stawka uśredniona 81,5% – decyzja przy wniosku",
            averaged.note_pl,
            "Ustawa zasiłkowa, art. 30a i 31 ust. 3",
        )

    if ctx.profile.mother_cannot_care is not None:
        add(
            "mother_cannot_care",
            "info",
            "family",
            "Szczególna sytuacja matki",
            "Ojciec może przejąć urlop macierzyński wcześniej niż po 14 tygodniach, gdy matka jest w szpitalu, "
            "nie jest zdolna do samodzielnej egzystencji, zmarła lub porzuciła dziecko – w wymiarze "
            "odpowiadającym czasowi hospitalizacji lub pozostałej części urlopu.",
            "Kodeks pracy, art. 180; ustawa zasiłkowa",
        )

    for tag, title, text in (
        (
            "stillbirth",
            "Wsparcie po stracie dziecka",
            "Zasiłek macierzyński przysługuje także po urodzeniu martwego dziecka. Pomoc psychologiczną "
            "i wsparcie oferują fundacje i stowarzyszenia – ich listę znajdziesz w zakładce z informacjami.",
        ),
        (
            "child_death",
            "Wsparcie po stracie dziecka",
            "Zasiłek macierzyński zachowujesz także po śmierci dziecka (w wymiarze opisanym wyżej). "
            "Dostępna jest pomoc fundacji i stowarzyszeń.",
        ),
        (
            "premature",
            "Rodzice wcześniaków i dzieci w szpitalu",
            "Rodzice dzieci hospitalizowanych mogą liczyć na wsparcie fundacji i stowarzyszeń oraz na "
            "uzupełniający urlop macierzyński.",
        ),
        (
            "za_zyciem",
            "Program „Za życiem”",
            "Dziecko z zaświadczeniem „Za życiem” daje dłuższy urlop rodzicielski i prawo do dodatkowego "
            "wsparcia (koordynator, poradnictwo, opieka wytchnieniowa).",
        ),
    ):
        if tag in ctx.ent.tags:
            add(f"support_{tag}", "info", "family", title, text, None)

    risks.sort(key=lambda r: SEVERITY_ORDER[r.severity])
    return risks
