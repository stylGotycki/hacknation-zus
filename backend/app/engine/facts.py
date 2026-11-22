"""Input data in the language of the rules.

The calculator sends a `FamilyProfile` (English API model). Rules edited in the admin panel
read Polish names – `dziecko.liczba`, `mama.zatrudnienie`, `plan.przed_porodem_tyg` – so a
ZUS analyst can read them next to the act. This module builds that dictionary and documents
every field (FACT_FIELDS, shown in the admin panel as the data dictionary).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.rules.models import (
    EmploymentType,
    FamilyProfile,
    InsuranceKind,
    JobLossReason,
    ParentProfile,
    Situation,
)

EVENT = {
    Situation.BIRTH: "porod",
    Situation.ADOPTION: "przysposobienie",
    Situation.FOSTER: "rodzina_zastepcza",
}
EMPLOYMENT = {
    EmploymentType.EMPLOYEE: "umowa_o_prace",
    EmploymentType.CONTRACT: "zlecenie",
    EmploymentType.SELF_EMPLOYED: "dzialalnosc",
    EmploymentType.COOPERATING: "wspolpracujaca",
    EmploymentType.UNEMPLOYED: "bez_pracy",
    EmploymentType.OTHER: "inne",
}
INSURANCE = {
    InsuranceKind.MANDATORY: "obowiazkowe",
    InsuranceKind.VOLUNTARY: "dobrowolne",
    InsuranceKind.NONE: "brak",
}
JOB_LOSS = {
    JobLossReason.EMPLOYER_BANKRUPTCY: "upadlosc_likwidacja_smierc",
    JobLossReason.UNLAWFUL_DISMISSAL: "naruszenie_prawa",
    JobLossReason.OTHER: "inna",
}
MOTHER_SITUATION = {
    "hospital": "szpital",
    "disabled": "niezdolnosc",
    "death": "zgon",
    "abandoned": "porzucenie",
    "employed": "zatrudnienie",
}

# Root names a rule may read besides other rules. (path, type, description)
FACT_FIELDS: list[tuple[str, str, str]] = [
    ("dziecko.zdarzenie", "tekst", "porod | przysposobienie | rodzina_zastepcza"),
    ("dziecko.urodzone", "tak/nie", "poród już nastąpił (podano datę porodu)"),
    (
        "dziecko.data",
        "data",
        "data zdarzenia: porodu, przewidywanego porodu albo przyjęcia dziecka",
    ),
    ("dziecko.data_porodu", "data", "data porodu (gdy dziecko się urodziło)"),
    ("dziecko.data_przewidywana", "data", "przewidywana data porodu"),
    ("dziecko.data_przyjecia", "data", "data przyjęcia dziecka na wychowanie"),
    ("dziecko.data_urodzenia", "data", "data urodzenia dziecka (przy przyjęciu wyliczona z wieku)"),
    (
        "dziecko.liczba",
        "liczba",
        "liczba dzieci urodzonych przy jednym porodzie / przyjętych jednocześnie",
    ),
    ("dziecko.liczba_zywych", "liczba", "liczba dzieci pozostałych przy życiu"),
    ("dziecko.martwe_urodzenie", "tak/nie", "urodzenie martwego dziecka"),
    ("dziecko.data_zgonu", "data", "data zgonu dziecka (przy martwym urodzeniu = data porodu)"),
    ("dziecko.tydzien_ciazy", "liczba", "tydzień ciąży, w którym urodziło się dziecko"),
    ("dziecko.masa_g", "liczba", "masa urodzeniowa w gramach (najniższa przy porodzie mnogim)"),
    (
        "dziecko.dni_szpitala",
        "liczba",
        "suma dni pobytu dziecka w szpitalu uwzględnianych przy urlopie uzupełniającym",
    ),
    (
        "dziecko.pierwszy_dzien_szpitala",
        "liczba",
        "który dzień po porodzie był pierwszym dniem pobytu w szpitalu",
    ),
    ("dziecko.za_zyciem", "tak/nie", "dziecko ma zaświadczenie „Za życiem”"),
    ("dziecko.wiek_lat", "liczba", "wiek dziecka przyjętego na wychowanie (lata, z ułamkiem)"),
    ("dziecko.odroczony_obowiazek", "tak/nie", "odroczony obowiązek szkolny (rodzina zastępcza)"),
    ("mama.* / tata.*", "", "te same pola dla każdego z rodziców:"),
    ("mama.obecny", "tak/nie", "rodzic jest w rodzinie / we wniosku"),
    (
        "mama.zatrudnienie",
        "tekst",
        "umowa_o_prace | zlecenie | dzialalnosc | wspolpracujaca | bez_pracy | inne",
    ),
    ("mama.pracownik", "tak/nie", "pracownik w rozumieniu Kodeksu pracy (umowa o pracę)"),
    ("mama.ubezpieczenie", "tekst", "ubezpieczenie chorobowe: obowiazkowe | dobrowolne | brak"),
    (
        "mama.ubezpieczony_w_dniu_zdarzenia",
        "tak/nie",
        "podlega ubezpieczeniu chorobowemu w dniu porodu / przyjęcia",
    ),
    ("mama.urlop_wychowawczy", "tak/nie", "w dniu porodu przebywa na urlopie wychowawczym"),
    ("mama.ustanie_ubezpieczenia", "data", "dzień ustania ubezpieczenia (np. rozwiązania umowy)"),
    ("mama.przyczyna_ustania", "tekst", "upadlosc_likwidacja_smierc | naruszenie_prawa | inna"),
    (
        "mama.umowa_przedluzona_do_porodu",
        "tak/nie",
        "umowa na czas określony przedłużona do dnia porodu",
    ),
    ("mama.dni_ubezpieczenia", "liczba", "dni nieprzerwanego ubezpieczenia chorobowego"),
    (
        "mama.liczba_ubezpieczonych",
        "liczba",
        "ilu ubezpieczonych zgłasza płatnik składek (stan na 30 listopada)",
    ),
    (
        "mama.podstawa_brutto",
        "kwota",
        "przeciętne miesięczne wynagrodzenie / podstawa składki chorobowej (przed potrąceniem 13,71%)",
    ),
    ("mama.wymiar_etatu", "liczba", "wymiar czasu pracy (1 = pełny etat)"),
    ("mama.ulga_na_start", "tak/nie", "korzysta z ulgi na start (brak ubezpieczeń społecznych)"),
    ("mama.dlug", "kwota", "zadłużenie z tytułu składek w dniu powstania prawa do świadczenia"),
    ("mama.dlug_splacony", "data", "dzień spłaty całego zadłużenia"),
    (
        "mama.praca_w_rodzicielskim",
        "liczba",
        "część etatu wykonywana w trakcie urlopu rodzicielskiego (0–0,5)",
    ),
    ("mama.zwolnienie_b_od", "data", "początek zwolnienia lekarskiego z kodem B"),
    ("mama.zwolnienie_b_do", "data", "koniec zwolnienia lekarskiego z kodem B"),
    (
        "mama.dni_chorobowego_w_roku",
        "liczba",
        "dni wynagrodzenia chorobowego już wypłaconego w roku",
    ),
    ("mama.wiek_50", "tak/nie", "pracownik po roku, w którym ukończył 50 lat"),
    (
        "sytuacja_matki.rodzaj",
        "tekst",
        "szpital | niezdolnosc | zgon | porzucenie | zatrudnienie (matka bez tytułu do ubezpieczenia podjęła pracę)",
    ),
    (
        "sytuacja_matki.od",
        "data",
        "data zdarzenia (przyjęcia do szpitala, zgonu, porzucenia, podjęcia pracy)",
    ),
    ("sytuacja_matki.do", "data", "data zakończenia (wypisu ze szpitala, ustania zatrudnienia)"),
    ("plan.przed_porodem_tyg", "liczba", "tygodnie urlopu macierzyńskiego przed porodem"),
    ("plan.dla_taty_tyg", "liczba", "tygodnie urlopu macierzyńskiego, które przejmuje tata"),
    ("plan.rodzicielski_tata_tyg", "liczba", "tygodnie urlopu rodzicielskiego taty (puste = 9)"),
    (
        "plan.rodzicielski_tata_od",
        "data",
        "początek urlopu rodzicielskiego taty (puste = po mamie)",
    ),
    (
        "plan.rodzicielski_mama_od",
        "data",
        "początek urlopu rodzicielskiego mamy (puste = po urlopie macierzyńskim)",
    ),
    (
        "plan.czesci_mama / plan.czesci_tata",
        "liczba",
        "na ile części rodzic dzieli urlop rodzicielski",
    ),
    ("plan.ojcowski_od", "data", "początek urlopu ojcowskiego"),
    ("plan.ojcowski_czesci", "liczba", "na ile części tata dzieli urlop ojcowski"),
    (
        "plan.uzupelniajacy",
        "tak/nie",
        "rodzina chce skorzystać z uzupełniającego urlopu macierzyńskiego",
    ),
    ("plan.uzupelniajacy_bierze", "tekst", "mama | tata"),
    ("plan.stawka_usredniona", "tak/nie", "wniosek o zasiłek w wysokości 81,5% (art. 30a)"),
    ("plan.wniosek_usredniony_zlozony", "data", "data złożenia wniosku o stawkę uśrednioną"),
]
FACT_ROOTS = {"dziecko", "mama", "tata", "sytuacja_matki", "plan"}


def _mean(values: list[float] | None, fallback: float | None) -> float | None:
    vals = [v for v in values or [] if v is not None]
    return sum(vals) / len(vals) if vals else fallback


def _parent(p: ParentProfile | None, event: date, born: bool = False) -> dict[str, Any]:
    if p is None:
        return {
            "obecny": False,
            "pracownik": False,
            "zatrudnienie": None,
            "ubezpieczenie": "brak",
            "ubezpieczony_w_dniu_zdarzenia": False,
            "dlug": 0,
            "praca_w_rodzicielskim": 0,
            "dni_chorobowego_w_roku": 0,
            "wiek_50": False,
            "urlop_wychowawczy": False,
            "ulga_na_start": False,
            "umowa_przedluzona_do_porodu": False,
            "wymiar_etatu": 1,
        }
    insurance = INSURANCE[p.sickness_insurance or InsuranceKind.NONE]
    insured = (
        insurance != "brak"
        and not p.start_relief
        and (p.insurance_ended_on is None or p.insurance_ended_on >= event)
    )
    # Sickness in pregnancy ends the day before the birth: from the birth on the maternity allowance
    # is paid, so a longer e-ZLA must not be paid (and counted) twice.
    sick_from, sick_to = p.sick_leave_start, p.sick_leave_end
    if born and sick_from and sick_to and sick_to >= event:
        sick_to = event - timedelta(days=1)
        if sick_from > sick_to:
            sick_from = sick_to = None
    return {
        "obecny": True,
        "zatrudnienie": EMPLOYMENT[p.employment],
        "pracownik": p.employment == EmploymentType.EMPLOYEE,
        "ubezpieczenie": "brak" if p.start_relief else insurance,
        "ubezpieczony_w_dniu_zdarzenia": insured,
        "urlop_wychowawczy": p.on_childcare_leave,
        "ustanie_ubezpieczenia": p.insurance_ended_on,
        "przyczyna_ustania": JOB_LOSS.get(p.job_loss_reason) if p.job_loss_reason else None,
        "umowa_przedluzona_do_porodu": p.fixed_term_contract,
        "dni_ubezpieczenia": p.insured_days,
        "liczba_ubezpieczonych": p.employer_insured_count,
        "podstawa_brutto": _mean(p.monthly_bases, p.average_monthly_base),
        "wymiar_etatu": p.working_time_fraction,
        "ulga_na_start": p.start_relief,
        "dlug": p.contribution_debt,
        "dlug_splacony": p.debt_paid_on,
        "praca_w_rodzicielskim": p.planned_work_fraction,
        "zwolnienie_b_od": sick_from,
        "zwolnienie_b_do": sick_to,
        "dni_chorobowego_w_roku": p.sick_days_used_this_year,
        "wiek_50": p.age_over_50,
    }


def build_facts(profile: FamilyProfile) -> dict[str, Any]:
    child = profile.child
    event = child.event_date
    assert event is not None  # guaranteed by FamilyProfile validation
    surviving = child.children_surviving
    if surviving is None:
        lost = child.stillborn or child.died_on is not None
        surviving = max(child.children_count - 1, 0) if lost else child.children_count
    if child.situation == Situation.BIRTH:
        birth_of_child = child.birth_date or child.due_date
    else:
        birth_of_child = event - timedelta(days=round((child.age_years or 0) * 365.25))
    plan = profile.plan
    return {
        "dziecko": {
            "zdarzenie": EVENT[child.situation],
            "urodzone": child.is_born,
            "data": event,
            "data_porodu": child.birth_date,
            "data_przewidywana": child.due_date,
            "data_przyjecia": child.placement_date,
            "data_urodzenia": birth_of_child,
            "liczba": child.children_count,
            "liczba_zywych": surviving,
            "martwe_urodzenie": child.stillborn,
            "data_zgonu": child.birth_date
            if child.stillborn and not child.died_on
            else child.died_on,
            "tydzien_ciazy": child.gestation_weeks,
            "masa_g": child.birth_weight_g,
            "dni_szpitala": child.hospital_days,
            "pierwszy_dzien_szpitala": child.hospital_first_day,
            "za_zyciem": child.za_zyciem,
            "wiek_lat": child.age_years,
            "odroczony_obowiazek": child.school_deferred,
        },
        "mama": _parent(profile.mother, event, child.birth_date is not None),
        "tata": _parent(profile.father, event, child.birth_date is not None),
        "sytuacja_matki": {
            "rodzaj": MOTHER_SITUATION.get(profile.mother_cannot_care.value)
            if profile.mother_cannot_care
            else None,
            "od": profile.mother_situation_from,
            "do": profile.mother_situation_to,
        },
        "plan": {
            "przed_porodem_tyg": plan.maternity_before_birth_weeks,
            "dla_taty_tyg": plan.maternity_weeks_to_father,
            "rodzicielski_tata_tyg": plan.parental_weeks_father,
            "rodzicielski_tata_od": plan.parental_father_start,
            "rodzicielski_mama_od": plan.parental_mother_start,
            "czesci_mama": plan.parental_parts_mother,
            "czesci_tata": plan.parental_parts_father,
            "ojcowski_od": plan.paternity_start,
            "ojcowski_czesci": plan.paternity_parts,
            "uzupelniajacy": plan.use_supplementary_leave,
            "uzupelniajacy_bierze": "tata" if plan.supplementary_taken_by == "father" else "mama",
            "stawka_usredniona": plan.averaged_rate,
            "wniosek_usredniony_zlozony": plan.averaged_rate_applied_on,
        },
    }
