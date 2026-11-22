"""Three demo accounts for the mObywatel login mock.

Instead of one account per scenario, every account is a family with its own history: the answers
saved in the calculator, drafts and applications at different stages (see `seed_personas.py`).
Everything is invented: names, PESEL numbers, employers, bank accounts. Dates are fixed around
22.11.2026, the day of the hackathon demo.
"""

from typing import Any

PERSONAS: list[dict[str, Any]] = [
    {
        "id": "P1",
        "title_pl": "Początek ciąży – plan i wersja robocza",
        "description_pl": (
            "Aneta jest w 6. miesiącu ciąży (termin 18.03.2027), mąż Tomasz też pracuje. Policzyła uprawnienia "
            "i zaczęła wypełniać wniosek o urlop przed porodem – nie złożyła jeszcze żadnego wniosku."
        ),
        "people": {
            "mother": {
                "first_name": "Aneta",
                "last_name": "Nowak",
                "pesel": "93061512345",
                "address": "ul. Lipowa 12/4, 30-001 Kraków",
                "employer_name": "Bank Południowy S.A.",
                "employer_address": "ul. Długa 5, 31-147 Kraków",
                "place": "Kraków",
            },
            "father": {
                "first_name": "Tomasz",
                "last_name": "Nowak",
                "pesel": "91020212345",
                "address": "ul. Lipowa 12/4, 30-001 Kraków",
                "employer_name": "Instal-Serwis Sp. z o.o.",
                "employer_address": "ul. Fabryczna 3, 31-553 Kraków",
                "place": "Kraków",
            },
        },
        "profile": {
            "child": {"due_date": "2027-03-18"},
            "mother": {
                "employment": "employee",
                "average_monthly_base": 8200,
                "employer_insured_count": 120,
                "sick_leave_start": "2026-11-02",
                "sick_leave_end": "2026-11-12",
            },
            "father": {
                "employment": "employee",
                "average_monthly_base": 6900,
                "employer_insured_count": 40,
            },
            "plan": {"maternity_before_birth_weeks": 2},
        },
        "calculated_on": "2026-11-18",
        "actions": [
            {
                "kind": "draft",
                "form": "leave_maternity_before",
                "person": "mother",
                "step": 1,
                "only": ["first_name", "last_name", "employer_name", "employer_address", "place"],
            },
        ],
    },
    {
        "id": "P2",
        "title_pl": "Tuż przed porodem – część wniosków złożona",
        "description_pl": (
            "Karolina rodzi 19.12.2026. Jej wniosek o urlop przed porodem jest już rozpatrzony, mąż Marek "
            "(zarabia dużo więcej) złożył wniosek o urlop ojcowski, a wniosek o urlop rodzicielski czeka w wersji roboczej."
        ),
        "people": {
            "mother": {
                "first_name": "Karolina",
                "last_name": "Wiśniewska",
                "pesel": "94031812345",
                "address": "ul. Różana 7/2, 60-101 Poznań",
                "employer_name": "Studio Projektów Arkada Sp. z o.o.",
                "employer_address": "ul. Półwiejska 20, 61-888 Poznań",
                "place": "Poznań",
            },
            "father": {
                "first_name": "Marek",
                "last_name": "Wiśniewski",
                "pesel": "90112212345",
                "address": "ul. Różana 7/2, 60-101 Poznań",
                "employer_name": "Delta Logistyka Sp. z o.o.",
                "employer_address": "ul. Magazynowa 9, 62-020 Swarzędz",
                "place": "Poznań",
            },
        },
        "profile": {
            "child": {"due_date": "2026-12-19"},
            "mother": {
                "employment": "employee",
                "average_monthly_base": 5400,
                "employer_insured_count": 25,
            },
            "father": {
                "employment": "employee",
                "average_monthly_base": 9500,
                "employer_insured_count": 300,
            },
            "plan": {"maternity_before_birth_weeks": 4},
        },
        "calculated_on": "2026-10-30",
        "actions": [
            {
                "kind": "application",
                "form": "leave_maternity_before",
                "person": "mother",
                "filed": "2026-11-03",
                "decided": "2026-11-10",
                "via": "pracodawcę",
            },
            {
                "kind": "application",
                "form": "leave_paternity",
                "person": "father",
                "filed": "2026-11-15",
                "in_progress": "2026-11-17",
                "via": "pracodawcę",
            },
            {"kind": "draft", "form": "leave_parental", "person": "mother", "step": 1},
        ],
    },
    {
        "id": "P3",
        "title_pl": "Po porodzie – wnioski w różnych stadiach",
        "description_pl": (
            "Joanna urodziła 8.07.2026, tata Piotr prowadzi firmę. Wniosek o urlop rodzicielski i ZAM taty są "
            "rozpatrzone, wniosek o pracę w czasie urlopu złożyła po terminie, a termin na stawkę 81,5% minął."
        ),
        "people": {
            "mother": {
                "first_name": "Joanna",
                "last_name": "Zielińska",
                "pesel": "92082212345",
                "address": "ul. Kwiatowa 3/9, 50-100 Wrocław",
                "employer_name": "Pracownia Medyczna Zdrowie Sp. z o.o.",
                "employer_address": "ul. Świdnicka 40, 50-024 Wrocław",
                "place": "Wrocław",
            },
            "father": {
                "first_name": "Piotr",
                "last_name": "Zieliński",
                "pesel": "90051012345",
                "address": "ul. Kwiatowa 3/9, 50-100 Wrocław",
                "payer_name": "Piotr Zieliński – usługi informatyczne",
                "payer_nip": "8991234567",
                "payer_address": "ul. Kwiatowa 3/9, 50-100 Wrocław",
                "bank_account": "61109010140000071219812874",
                "place": "Wrocław",
            },
        },
        "profile": {
            "child": {"birth_date": "2026-07-08"},
            "mother": {
                "employment": "employee",
                "average_monthly_base": 6100,
                "employer_insured_count": 60,
                "planned_work_fraction": 0.5,
            },
            "father": {
                "employment": "self_employed",
                "sickness_insurance": "voluntary",
                "average_monthly_base": 4200,
                "insured_days": 900,
            },
            "plan": {"paternity_start": "2026-07-20"},
        },
        "calculated_on": "2026-07-12",
        "child_name": ("Maja", "Zielińska", "Wrocław"),
        "actions": [
            {
                "kind": "application",
                "form": "zus_zam",
                "person": "father",
                "filed": "2026-07-14",
                "in_progress": "2026-07-16",
                "decided": "2026-07-24",
                "via": "ZUS",
                "only_kind": "paternity",
            },
            {
                "kind": "application",
                "form": "leave_parental",
                "person": "mother",
                "filed": "2026-10-22",
                "in_progress": "2026-10-23",
                "decided": "2026-10-30",
                "via": "pracodawcę",
            },
            {
                "kind": "application",
                "form": "parental_work",
                "person": "mother",
                "filed": "2026-11-19",
                "via": "pracodawcę",
            },
        ],
    },
]


def personas() -> list[dict[str, Any]]:
    """Persona records in the shape the mock API expects: id, titles, profile."""
    return PERSONAS


CITIZENS: dict[str, dict[str, str]] = {
    p["id"]: {k: p["people"]["mother"][k] for k in ("first_name", "last_name", "pesel")}
    for p in PERSONAS
}
