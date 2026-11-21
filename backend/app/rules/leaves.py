"""How long each leave lasts (Labor Code), before any plan or money is applied."""

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.rules.dates import add_months, end_of_year
from app.rules.models import ChildProfile, Situation
from app.rules.params import Params


class PlanError(ValueError):
    """The chosen plan breaks a legal limit (message is meant for a developer, English)."""


@dataclass
class Entitlement:
    surviving_children: int
    maternity_weeks: int
    maternity_note_pl: str
    # The latest day the maternity allowance can run to (set after the child's death).
    maternity_end_cap: date | None = None
    supplementary_weeks: int = 0
    supplementary_note_pl: str = ""
    parental_weeks: int = 0
    parental_deadline: date | None = None
    paternity_days: int = 0
    paternity_deadline: date | None = None
    leave_blocked_reason_pl: str | None = None
    tags: list[str] = field(default_factory=list)
    notes_pl: list[str] = field(default_factory=list)


def surviving_children(child: ChildProfile) -> int:
    if child.children_surviving is not None:
        return min(child.children_surviving, child.children_count)
    if child.stillborn:
        return 0
    if child.died_on is not None:
        return max(child.children_count - 1, 0)
    return child.children_count


def _supplementary_weeks(child: ChildProfile, params: Params) -> tuple[int, str]:
    crit = params.table("supplementary_leave_criteria")
    caps = params.table("supplementary_maternity_max_weeks")
    if child.hospital_days <= 0:
        return 0, (
            "Uzupełniający urlop przysługuje, gdy dziecko urodziło się przedwcześnie "
            "lub wymagało hospitalizacji – podaj liczbę dni pobytu w szpitalu."
        )

    gestation = child.gestation_weeks
    long_case = (gestation is not None and gestation < crit["long_gestation_weeks_below"]) or (
        child.birth_weight_g is not None and child.birth_weight_g <= crit["long_birth_weight_g_max"]
    )
    if long_case:
        cap, label = int(caps["long"]), "poród przed 28. tygodniem ciąży lub masa do 1000 g"
    else:
        cap = int(caps["short"])
        preterm = gestation is not None and gestation < crit["preterm_gestation_weeks_below"]
        if preterm:
            label = "poród przed 37. tygodniem ciąży"
        else:
            window_from, window_to = crit["term_first_day_window"]
            first = child.hospital_first_day
            if (
                child.hospital_days < crit["term_min_stay_days"]
                or first is None
                or not window_from <= first <= window_to
            ):
                return 0, (
                    "Dziecko urodzone w terminie: urlop przysługuje, gdy pobyt w szpitalu trwał "
                    f"co najmniej {crit['term_min_stay_days']} dni, a jego pierwszy dzień "
                    f"przypadł między {window_from}. a {window_to}. dniem po porodzie."
                )
            label = "dziecko urodzone w terminie, ale hospitalizowane"

    weeks = min(math.ceil(child.hospital_days / 7), cap)
    return weeks, (
        f"{label}: 1 tydzień urlopu za każdy rozpoczęty tydzień pobytu dziecka w szpitalu "
        f"(maksymalnie {cap} tyg.)."
    )


def _parental_weeks(count: int, za_zyciem: bool, params: Params) -> int:
    key = ("za_zyciem_" if za_zyciem else "") + ("multiple" if count > 1 else "single")
    return int(params.lookup("parental_leave_weeks", key))


def compute_entitlement(child: ChildProfile, params: Params) -> Entitlement:
    event = child.event_date
    assert event is not None  # guaranteed by FamilyProfile validation
    survivors = surviving_children(child)
    tags: list[str] = []
    notes: list[str] = []

    if child.situation != Situation.BIRTH:
        return _adoption_entitlement(child, params, event, survivors)

    # --- Child did not survive (stillbirth / death) ------------------------------------------
    death_limit = params.integer("stillbirth_child_death_weeks_limit")
    min_after_death = params.integer("child_death_min_days")
    cap: date | None = None
    if survivors == 0:
        weeks = params.integer("stillbirth_maternity_weeks")
        base_note = (
            "Urodzenie martwego dziecka lub zgon dziecka przed ukończeniem "
            f"{death_limit} tygodni życia: {weeks} tygodni po porodzie, "
            f"nie krócej niż {min_after_death} dni od dnia zgonu."
            if child.died_on
            else f"Urodzenie martwego dziecka: urlop macierzyński w wymiarze {weeks} tygodni."
        )
        tags.append("stillbirth" if child.stillborn else "child_death")
        if child.died_on is not None and child.birth_date is not None:
            age_weeks = (child.died_on - child.birth_date).days / 7
            if age_weeks >= death_limit:
                # Died after the early period: the usual leave continues for 7 days only.
                weeks = int(params.by_count("maternity_leave_weeks", child.children_count))
                cap = child.died_on + timedelta(days=min_after_death)
                base_note = (
                    "Zgon dziecka po ukończeniu 8 tygodni życia: prawo do zasiłku macierzyńskiego "
                    f"zachowane przez {min_after_death} dni od dnia zgonu."
                )
        return Entitlement(
            surviving_children=0,
            maternity_weeks=weeks,
            maternity_note_pl=base_note,
            maternity_end_cap=cap,
            tags=tags,
            notes_pl=["Urlop rodzicielski, ojcowski i uzupełniający nie przysługują."],
        )

    # --- Child alive -------------------------------------------------------------------------
    maternity = int(params.by_count("maternity_leave_weeks", survivors))
    note = f"{maternity} tygodni urlopu macierzyńskiego dla {survivors} "
    note += "dziecka." if survivors == 1 else "dzieci urodzonych przy jednym porodzie."
    if survivors < child.children_count:
        note += " Wymiar odpowiada liczbie dzieci pozostałych przy życiu."
        tags.append("child_death")

    supplementary, supplementary_note = _supplementary_weeks(child, params)
    if supplementary:
        tags.append("premature")

    parental = _parental_weeks(survivors, child.za_zyciem, params)
    if child.za_zyciem:
        tags.append("za_zyciem")
        notes.append("Dziecko z zaświadczeniem „Za życiem” – wydłużony urlop rodzicielski.")

    deadline_years = params.integer("parental_deadline_child_age_years")
    birth_year = (child.birth_date or event).year
    paternity_months = params.integer("paternity_deadline_months")

    return Entitlement(
        surviving_children=survivors,
        maternity_weeks=maternity,
        maternity_note_pl=note,
        supplementary_weeks=supplementary,
        supplementary_note_pl=supplementary_note,
        parental_weeks=parental,
        parental_deadline=end_of_year(birth_year + deadline_years),
        paternity_days=params.integer("paternity_leave_days"),
        paternity_deadline=add_months(child.birth_date or event, paternity_months),
        tags=tags,
        notes_pl=notes,
    )


def _adoption_entitlement(
    child: ChildProfile, params: Params, event: date, survivors: int
) -> Entitlement:
    limits = params.table("adoption_leave_max_child_age_years")
    if child.situation == Situation.ADOPTION:
        age_limit = limits["adoption"]
    elif child.school_deferred:
        age_limit = limits["foster_school_deferred"]
    else:
        age_limit = limits["foster"]

    maternity = int(params.by_count("maternity_leave_weeks", child.children_count))
    parental = _parental_weeks(child.children_count, child.za_zyciem, params)
    age = child.age_years

    blocked = None
    if age is not None and age > age_limit:
        blocked = (
            f"Dziecko jest starsze niż {age_limit} lat – urlop na warunkach macierzyńskiego "
            "i rodzicielski nie przysługują."
        )

    # Parental leave must end by the end of the year of the child's 6th birthday.
    if age is not None:
        birth_year_estimate = event.year - int(age)
    else:
        birth_year_estimate = event.year
    deadline_years = params.integer("parental_deadline_child_age_years")

    # Paternity (adoption): 12 months from taking in the child, not beyond the age limit.
    paternity_deadline = add_months(event, params.integer("paternity_deadline_months"))
    adoption_age = limits["adoption"]
    if age is not None:
        fourteenth = date(event.year - int(age) + adoption_age, event.month, min(event.day, 28))
        paternity_deadline = min(paternity_deadline, fourteenth)

    kind = "przysposobienie" if child.situation == Situation.ADOPTION else "rodzina zastępcza"
    return Entitlement(
        surviving_children=survivors,
        maternity_weeks=0 if blocked else maternity,
        maternity_note_pl=(
            f"Urlop na warunkach urlopu macierzyńskiego ({kind}): {maternity} tygodni "
            f"(dziecko do {age_limit} lat)."
        ),
        parental_weeks=0 if blocked else parental,
        parental_deadline=end_of_year(birth_year_estimate + deadline_years),
        paternity_days=0 if blocked else params.integer("paternity_leave_days"),
        paternity_deadline=paternity_deadline,
        leave_blocked_reason_pl=blocked,
        tags=["adoption" if child.situation == Situation.ADOPTION else "foster"],
        notes_pl=[
            "Nie ma urlopu przed porodem. Uzupełniający urlop dla dzieci przyjętych na "
            "wychowanie – sprawdź w ZUS lub u pracodawcy."
        ],
    )
