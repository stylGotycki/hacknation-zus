"""Form definitions (E6). Keys are English; every label shown to the user is Polish.

The leave requests are designed here (the task asks to design them). `zus_zam` is a simplified
version of the ZUS ZAM form (since 24.10.2026 it also replaces ZUR and ZAO) – it is a simulation,
not the official printout.
"""

from typing import Literal

from pydantic import BaseModel


class FormField(BaseModel):
    key: str
    label_pl: str
    type: Literal["text", "date", "number", "select", "checkbox", "textarea"] = "text"
    required: bool = False
    hint_pl: str | None = None
    options: list[tuple[str, str]] | None = None  # (value, label_pl) for select


class FormStep(BaseModel):
    title_pl: str
    fields: list[FormField]


class FormDefinition(BaseModel):
    code: str
    title_pl: str
    description_pl: str
    submitted_to: Literal["employer", "zus"]
    steps: list[FormStep]


def _person_step(employer: bool) -> FormStep:
    fields = [
        FormField(key="first_name", label_pl="Imię", required=True),
        FormField(key="last_name", label_pl="Nazwisko", required=True),
        FormField(key="pesel", label_pl="PESEL", required=True, hint_pl="11 cyfr"),
    ]
    if employer:
        fields += [
            FormField(key="employer_name", label_pl="Nazwa pracodawcy", required=True),
            FormField(key="position", label_pl="Stanowisko"),
        ]
    else:
        fields += [
            FormField(key="address", label_pl="Adres zamieszkania", required=True),
            FormField(key="phone", label_pl="Telefon"),
        ]
    return FormStep(title_pl="Dane wnioskodawcy", fields=fields)


_DECLARATION = FormField(
    key="declaration",
    label_pl="Oświadczam, że dane we wniosku są prawdziwe",
    type="checkbox",
    required=True,
)

FORMS: dict[str, FormDefinition] = {
    "leave_maternity": FormDefinition(
        code="leave_maternity",
        title_pl="Wniosek o udzielenie urlopu macierzyńskiego",
        description_pl="Składasz go do pracodawcy. Jeśli zaraz po macierzyńskim chcesz wziąć rodzicielski, "
        "wystarczy jeden wniosek.",
        submitted_to="employer",
        steps=[
            _person_step(True),
            FormStep(
                title_pl="Dziecko i termin urlopu",
                fields=[
                    FormField(key="child_date", label_pl="Data porodu (przewidywana lub rzeczywista)", type="date", required=True),
                    FormField(key="leave_start", label_pl="Początek urlopu", type="date", required=True),
                    FormField(key="leave_end", label_pl="Koniec urlopu", type="date", required=True),
                    FormField(
                        key="with_parental",
                        label_pl="Zaraz po macierzyńskim chcę wykorzystać urlop rodzicielski (jeden wniosek)",
                        type="checkbox",
                    ),
                    FormField(key="notes", label_pl="Uwagi", type="textarea"),
                ],
            ),
            FormStep(title_pl="Oświadczenie", fields=[_DECLARATION]),
        ],
    ),
    "leave_parental": FormDefinition(
        code="leave_parental",
        title_pl="Wniosek o udzielenie urlopu rodzicielskiego",
        description_pl="Składasz go do pracodawcy co najmniej 21 dni przed rozpoczęciem urlopu. "
        "Możesz podzielić urlop na nie więcej niż 5 części.",
        submitted_to="employer",
        steps=[
            _person_step(True),
            FormStep(
                title_pl="Termin urlopu",
                fields=[
                    FormField(key="leave_start", label_pl="Początek urlopu", type="date", required=True),
                    FormField(key="leave_end", label_pl="Koniec urlopu", type="date", required=True),
                    FormField(key="part_number", label_pl="Numer części urlopu (1–5)", type="number", required=True),
                    FormField(
                        key="work_percent",
                        label_pl="Pracuję w czasie urlopu (% etatu)",
                        type="number",
                        hint_pl="0 – pełny urlop; maksymalnie 50%.",
                    ),
                    FormField(key="child_date", label_pl="Data urodzenia dziecka", type="date", required=True),
                ],
            ),
            FormStep(title_pl="Oświadczenie", fields=[_DECLARATION]),
        ],
    ),
    "leave_paternity": FormDefinition(
        code="leave_paternity",
        title_pl="Wniosek o udzielenie urlopu ojcowskiego",
        description_pl="Składasz go do pracodawcy najpóźniej 7 dni przed rozpoczęciem urlopu. "
        "Urlop trwa 14 dni, możesz wziąć go w dwóch częściach.",
        submitted_to="employer",
        steps=[
            _person_step(True),
            FormStep(
                title_pl="Termin urlopu",
                fields=[
                    FormField(key="leave_start", label_pl="Początek urlopu", type="date", required=True),
                    FormField(key="leave_end", label_pl="Koniec urlopu", type="date", required=True),
                    FormField(key="child_date", label_pl="Data urodzenia dziecka", type="date", required=True),
                ],
            ),
            FormStep(title_pl="Oświadczenie", fields=[_DECLARATION]),
        ],
    ),
    "zus_zam": FormDefinition(
        code="zus_zam",
        title_pl="Wniosek o zasiłek macierzyński (ZAM)",
        description_pl="Składasz go do ZUS, jeśli nie jesteś pracownikiem (np. prowadzisz firmę lub masz umowę "
        "zlecenie). Od 24.10.2026 jeden wniosek zastępuje ZAM, ZUR i ZAO. To uproszczona symulacja druku.",
        submitted_to="zus",
        steps=[
            _person_step(False),
            FormStep(
                title_pl="Dziecko",
                fields=[
                    FormField(key="child_date", label_pl="Data urodzenia / przyjęcia dziecka", type="date", required=True),
                    FormField(key="children_count", label_pl="Liczba dzieci", type="number", required=True),
                ],
            ),
            FormStep(
                title_pl="Za jaki okres",
                fields=[
                    FormField(key="for_maternity", label_pl="Za okres urlopu macierzyńskiego", type="checkbox"),
                    FormField(key="for_parental", label_pl="Za okres urlopu rodzicielskiego", type="checkbox"),
                    FormField(key="for_paternity", label_pl="Za okres urlopu ojcowskiego", type="checkbox"),
                    FormField(key="benefit_start", label_pl="Od dnia", type="date", required=True),
                    FormField(key="benefit_end", label_pl="Do dnia", type="date", required=True),
                ],
            ),
            FormStep(
                title_pl="Wypłata",
                fields=[
                    FormField(key="bank_account", label_pl="Numer rachunku bankowego", required=True, hint_pl="26 cyfr"),
                    FormField(
                        key="attachments",
                        label_pl="Załączniki (np. zaświadczenie „Za życiem”, zaświadczenie ze szpitala)",
                        type="textarea",
                    ),
                ],
            ),
            FormStep(title_pl="Oświadczenie", fields=[_DECLARATION]),
        ],
    ),
}


def missing_fields(definition: FormDefinition, data: dict) -> list[str]:
    """Keys of required fields that are empty (an unchecked required checkbox counts as empty)."""
    missing = []
    for step in definition.steps:
        for field in step.fields:
            if field.required and data.get(field.key) in (None, "", False):
                missing.append(field.key)
    return missing
