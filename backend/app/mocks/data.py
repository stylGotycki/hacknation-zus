"""Builds mocked records of the external systems for the persona scenarios (E3).

Everything here is invented: names, PESEL numbers, document numbers. The ZUS data is derived from
the scenario profile so that the numbers shown in the mocks agree with the rules engine.
"""

import zlib
from datetime import date, timedelta

CITIZENS: dict[str, dict] = {
    "S1": {"first_name": "Zofia", "last_name": "Lisowska", "pesel": "90021412345"},
    "S2": {"first_name": "Anna", "last_name": "Lubicka", "pesel": "92050312345"},
    "S3": {"first_name": "Marta", "last_name": "Gorecka", "pesel": "91111112345"},
    "S4": {"first_name": "Ewa", "last_name": "Lewandowska", "pesel": "89070512345"},
    "S5": {"first_name": "Agata", "last_name": "Gołębiowska", "pesel": "93032212345"},
    "S6": {"first_name": "Zuzanna", "last_name": "Leśniak", "pesel": "94092912345"},
    "S7": {"first_name": "Katarzyna", "last_name": "Łukasik", "pesel": "88041812345"},
    "S8": {"first_name": "Jolanta", "last_name": "Grabowska", "pesel": "85120112345"},
    "S9": {"first_name": "Natalia", "last_name": "Łaska", "pesel": "95010612345"},
    "S10": {"first_name": "Alicja", "last_name": "Chojnacka", "pesel": "90082312345"},
    "S11": {"first_name": "Dorota", "last_name": "Byczek", "pesel": "87061712345"},
    "S12": {"first_name": "Weronika", "last_name": "Lubaś", "pesel": "93110912345"},
    "S13": {"first_name": "Tomasz", "last_name": "Grzelak", "pesel": "88030412345"},
    "S14": {"first_name": "Magdalena", "last_name": "Lipińska", "pesel": "86072012345"},
    "S15": {"first_name": "Paulina", "last_name": "Leszczyńska", "pesel": "92121212345"},
}

TITLES = {
    "employee": ("0110", "Pracownik – umowa o pracę"),
    "contract": ("0411", "Zleceniobiorca – umowa zlecenie"),
    "self_employed": ("0510", "Prowadzący pozarolniczą działalność"),
    "cooperating": ("0510", "Osoba współpracująca"),
    "unemployed": ("", "Brak tytułu do ubezpieczeń"),
    "other": ("", "Inny tytuł"),
}


def mask_pesel(pesel: str) -> str:
    return f"{pesel[:6]}*****"


def citizen_card(scenario: dict) -> dict:
    person = CITIZENS[scenario["id"]]
    return {
        "id": scenario["id"],
        "first_name": person["first_name"],
        "last_name": person["last_name"],
        "pesel_masked": mask_pesel(person["pesel"]),
        "scenario_title_pl": scenario["title_pl"],
        "scenario_description_pl": scenario["description_pl"],
    }


def event_date(profile: dict) -> date:
    child = profile["child"]
    raw = child.get("birth_date") or child.get("due_date") or child.get("placement_date")
    return date.fromisoformat(raw)


def parent_data(profile: dict) -> tuple[str, dict]:
    """The parent the citizen represents: the mother, unless only the father has an insurance title."""
    mother, father = profile.get("mother"), profile.get("father")
    if mother and (mother.get("employment") != "unemployed" or not father):
        return "mother", mother
    return "father", father


def insurance_record(profile: dict) -> dict:
    role, parent = parent_data(profile)
    event = event_date(profile)
    code, title = TITLES.get(parent.get("employment", "other"), TITLES["other"])
    insurance = parent.get("sickness_insurance") or (
        "mandatory" if parent.get("employment") == "employee" else "none"
    )
    ended = parent.get("insurance_ended_on")
    since = event - timedelta(days=parent.get("insured_days") or 400)
    periods = []
    if insurance != "none":
        periods.append(
            {
                "title_code": code,
                "title_pl": title,
                "sickness_insurance": insurance,
                "from": since.isoformat(),
                "to": ended,
                "payer_pl": "Płatnik składek: ACME Sp. z o.o. (przykład)"
                if parent.get("employment") in ("employee", "contract")
                else "Składki opłaca ubezpieczony",
            }
        )
    insured_on_event = bool(periods) and (ended is None or date.fromisoformat(ended) >= event)
    return {
        "role": role,
        "event_date": event.isoformat(),
        "insured_on_event": insured_on_event,
        "periods": periods,
        "bases": base_history(parent, event),
        "summary_pl": (
            "Ubezpieczenie chorobowe w dniu zdarzenia: TAK"
            if insured_on_event
            else "Ubezpieczenie chorobowe w dniu zdarzenia: NIE"
        ),
    }


def base_history(parent: dict, event: date) -> list[dict]:
    """Up to 12 months before the event; the mean matches the profile's average base."""
    values = parent.get("monthly_bases")
    if not values:
        average = parent.get("average_monthly_base")
        if average is None:
            return []
        wobble = [0, 40, -30, 25, -20, 35, -45, 15, -10, 30, -25, 0]
        values = [round(average * (1 + w / 10000 * 10), 2) for w in wobble]
        values[-1] = round(average * 12 - sum(values[:-1]), 2)
    months = []
    year, month = event.year, event.month
    for value in reversed(values):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        months.append({"month": f"{year}-{month:02d}", "base": value})
    return list(reversed(months))


def debt_certificate(profile: dict, threshold: float) -> dict:
    role, parent = parent_data(profile)
    event = event_date(profile)
    amount = float(parent.get("contribution_debt") or 0)
    installments = bool(parent.get("debt_in_installments"))
    blocks = amount > threshold and not installments
    return {
        "role": role,
        "as_of": event.isoformat(),
        "number": f"ZAS/{event.year}/{zlib.crc32(event.isoformat().encode()) % 90000 + 10000}",
        "debt_amount": amount,
        "threshold": threshold,
        "in_installments": installments,
        "blocks_benefit": blocks,
        "summary_pl": (
            f"Zadłużenie z tytułu składek: {amount:.2f} zł – powyżej progu {threshold:.2f} zł, "
            "zasiłek zostanie wypłacony dopiero po spłacie."
            if blocks
            else f"Zadłużenie z tytułu składek: {amount:.2f} zł – nie blokuje wypłaty zasiłku."
        ),
    }


def ezla_records(profile: dict) -> list[dict]:
    role, parent = parent_data(profile)
    records = []
    if parent.get("sick_leave_start") and parent.get("sick_leave_end"):
        start = date.fromisoformat(parent["sick_leave_start"])
        end = date.fromisoformat(parent["sick_leave_end"])
        records.append(
            {
                "number": f"ZLA-{start.year}-{start.month:02d}{start.day:02d}-001",
                "code": "B",
                "code_description_pl": "Niezdolność do pracy przypadająca na okres ciąży",
                "from": start.isoformat(),
                "to": end.isoformat(),
                "days": (end - start).days + 1,
                "issued_by_pl": "lek. med. J. Nowicka (przykład)",
                "payer_pl": "Pracodawca (33 dni), potem ZUS",
            }
        )
    return records


PUE_ANSWERS = [
    (
        ("ubezpiecz", "tytuł"),
        "Dane o ubezpieczeniu widzisz w zakładce „Ubezpieczenie”. Jeśli coś się nie zgadza, "
        "zgłoś to płatnikowi składek – to on przekazuje zgłoszenia do ZUS.",
    ),
    (
        ("zadłuż", "składk", "niedopłat"),
        "Stan zadłużenia na dzień powstania prawa do zasiłku pokazuje "
        "zaświadczenie w zakładce „Zadłużenie”. Zaległość powyżej 1% płacy minimalnej wstrzymuje wypłatę zasiłku.",
    ),
    (
        ("termin", "kiedy", "wniosek"),
        "Wniosek o zasiłek macierzyński złóż najpóźniej w terminie pokazanym na "
        "osi czasu. Roszczenie o wypłatę przedawnia się po 6 miesiącach od ostatniego dnia okresu zasiłku.",
    ),
    (
        ("zla", "zwolnien", "chorob"),
        "Zaświadczenia e-ZLA trafiają do ZUS automatycznie. Ich listę sprawdzisz "
        "w zakładce „e-ZLA”.",
    ),
]


def pue_answer(text: str) -> str:
    lowered = text.lower()
    for keywords, answer in PUE_ANSWERS:
        if any(k in lowered for k in keywords):
            return answer
    return (
        "Dziękujemy za wiadomość. Konsultant PUE odpowie w ciągu 3 dni roboczych. "
        "To symulacja – pytanie nie zostało wysłane do ZUS."
    )
