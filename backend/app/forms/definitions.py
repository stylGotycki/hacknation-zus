"""Applications the guide prepares. Keys are English; everything shown to the user is Polish.

The content of every form follows the official sources attached to the task:
  * leave requests to the employer – Rozporządzenie MRPiPS z 11.03.2025 w sprawie wniosków
    dotyczących uprawnień pracowników związanych z rodzicielstwem (RW): each form lists exactly
    the items of its paragraph and the documents attached to it;
  * the ZUS application for maternity allowance (ZAM) – Rozporządzenie w sprawie dokumentów do
    ustalenia prawa do zasiłków (RZ), § 12, § 13, § 16 and załącznik nr 6 (points 1–19).

A form has: data steps, the text of the request (`body`, with {key} placeholders, paragraphs
shown only when their `when` condition holds), the attachments, the statements (oświadczenia)
and the confirmation that the data are true, shown on the summary page before sending.
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
    # "key" (truthy) or "key=value": the field is shown and required only when it holds.
    when: str | None = None


class FormStep(BaseModel):
    title_pl: str
    fields: list[FormField]
    when: str | None = None


class Paragraph(BaseModel):
    text_pl: str
    when: str | None = None


class FormDefinition(BaseModel):
    code: str
    title_pl: str
    description_pl: str
    submitted_to: Literal["employer", "zus", "registry"]
    addressee_pl: str
    legal_basis_pl: str
    deadline_pl: str = ""
    # Who files it: a single role, or both (then the form asks: field `applicant_role`).
    roles: list[Literal["mother", "father"]] = ["mother", "father"]
    # Deadline rules (termin) this application fulfils – the timeline replaces their points.
    fulfils: list[str] = []
    steps: list[FormStep]
    body: list[Paragraph]
    attachments: list[Paragraph] = []
    statements: list[FormField] = []
    instructions_pl: list[str] = []
    sources_pl: str = ""


ROLE_OPTIONS = [
    ("mother", "Matka dziecka (pracownica / ubezpieczona)"),
    ("father", "Ojciec dziecka (pracownik / ubezpieczony)"),
]
SITUATION_OPTIONS = [
    ("birth", "Urodzenie dziecka"),
    ("adoption", "Przyjęcie dziecka na wychowanie i wystąpienie do sądu o przysposobienie"),
    ("foster", "Przyjęcie dziecka na wychowanie jako rodzina zastępcza (nie zawodowa)"),
]

TRUTH = FormField(
    key="declaration",
    label_pl="Oświadczam, że dane zawarte we wniosku są zgodne z prawdą",
    type="checkbox",
    required=True,
)


def _employee(role: bool = False) -> FormStep:
    """RW: every request contains the employee's first name and surname; the rest is the letter header."""
    fields = [
        FormField(key="first_name", label_pl="Imię", required=True),
        FormField(key="last_name", label_pl="Nazwisko", required=True),
    ]
    if role:
        fields.append(
            FormField(
                key="applicant_role",
                label_pl="Składam jako",
                type="select",
                required=True,
                options=ROLE_OPTIONS,
            )
        )
    fields += [
        FormField(key="employer_name", label_pl="Pracodawca (nazwa)", required=True),
        FormField(key="employer_address", label_pl="Adres pracodawcy"),
        FormField(key="place", label_pl="Miejscowość", required=True),
    ]
    return FormStep(title_pl="Pracownik i pracodawca", fields=fields)


def _child(birth_required: bool = True) -> list[FormField]:
    return [
        FormField(key="child_first_name", label_pl="Imię dziecka", required=birth_required),
        FormField(key="child_last_name", label_pl="Nazwisko dziecka", required=birth_required),
        FormField(
            key="child_birth_date",
            label_pl="Data urodzenia dziecka",
            type="date",
            required=birth_required,
        ),
    ]


_SITUATION = FormField(
    key="situation",
    label_pl="Wniosek dotyczy",
    type="select",
    required=True,
    options=SITUATION_OPTIONS,
)
_TAKEN_IN = [
    FormField(
        key="placement_date",
        label_pl="Data przyjęcia dziecka na wychowanie",
        type="date",
        required=True,
        when="situation!=birth",
    ),
    FormField(
        key="school_deferred",
        label_pl="Wobec dziecka podjęto decyzję o odroczeniu obowiązku szkolnego",
        type="checkbox",
        when="situation!=birth",
    ),
]
# RW § 5 ust. 4, § 15 ust. 4, § 18 ust. 2 – documents for a child taken in.
_TAKEN_IN_DOCS = [
    Paragraph(
        text_pl="Oświadczenie o dacie przyjęcia dziecka na wychowanie ({placement_date}) oraz kopia wniosku o wszczęcie "
        "postępowania w sprawie przysposobienia z poświadczeniem sądu opiekuńczego o dacie wystąpienia do sądu "
        "(albo zaświadczenie sądu opiekuńczego o tej dacie), zawierające datę urodzenia dziecka.",
        when="situation=adoption",
    ),
    Paragraph(
        text_pl="Oświadczenie o dacie przyjęcia dziecka na wychowanie ({placement_date}) oraz kopia prawomocnego "
        "orzeczenia sądu opiekuńczego o umieszczeniu dziecka w rodzinie zastępczej albo kopia umowy zawartej "
        "między rodziną zastępczą a starostą.",
        when="situation=foster",
    ),
    Paragraph(
        text_pl="Kopia prawomocnej decyzji o odroczeniu obowiązku szkolnego.",
        when="school_deferred",
    ),
]
_BIRTH_CERT = Paragraph(
    text_pl="Odpis skrócony aktu urodzenia dziecka (lub zagraniczny dokument potwierdzający urodzenie, z tłumaczeniem "
    "na język polski, jeśli wymaga go § 21) albo jego kopia. Nie dołączasz go, jeśli jest już w Twoich aktach osobowych.",
)
EMPLOYER_INSTRUCTIONS = [
    "Wniosek składasz w postaci papierowej lub elektronicznej.",
    "Dokumentów, które są już w Twoich aktach osobowych, nie dołączasz (RW § 22).",
    "Jeśli dołączasz kopię dokumentu, na żądanie pracodawcy pokazujesz oryginał (RW § 23).",
]
RW = "Rozporządzenie MRPiPS z 11.03.2025 w sprawie wniosków dotyczących uprawnień pracowników związanych z rodzicielstwem (Dz.U. 2025 poz. 322)"


FORMS: dict[str, FormDefinition] = {
    # --- RW § 2 ------------------------------------------------------------------------------
    "leave_maternity_before": FormDefinition(
        code="leave_maternity_before",
        title_pl="Wniosek o udzielenie części urlopu macierzyńskiego przed przewidywaną datą porodu",
        description_pl="Składasz go do pracodawcy, jeśli chcesz zacząć urlop macierzyński przed porodem (najwyżej 6 tygodni). "
        "Urlopu po porodzie nie trzeba wnioskować.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 180 § 2 Kodeksu pracy; § 2 RW",
        deadline_pl="Najpóźniej 14 dni przed rozpoczęciem urlopu (Poradnik ZUS 2026).",
        roles=["mother"],
        fulfils=["t_mac_przed"],
        steps=[
            _employee(),
            FormStep(
                title_pl="Urlop przed porodem",
                fields=[
                    FormField(
                        key="leave_start",
                        label_pl="Data, od której ma być udzielona część urlopu",
                        type="date",
                        required=True,
                    ),
                    FormField(
                        key="due_date",
                        label_pl="Przewidywana data porodu (z zaświadczenia lekarskiego)",
                        type="date",
                        required=True,
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 180 § 2 Kodeksu pracy wnoszę o udzielenie mi części urlopu macierzyńskiego przed "
                "przewidywaną datą porodu od dnia {leave_start}. Przewidywana data porodu: {due_date}."
            )
        ],
        attachments=[
            Paragraph(
                text_pl="Kopia zaświadczenia lekarskiego wystawionego na zwykłym druku, określającego przewidywaną datę porodu."
            )
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 3 ------------------------------------------------------------------------------
    "leave_maternity_resignation": FormDefinition(
        code="leave_maternity_resignation",
        title_pl="Wniosek w sprawie rezygnacji z pozostałej części urlopu macierzyńskiego i powrotu do pracy",
        description_pl="Po wykorzystaniu co najmniej 14 tygodni urlopu po porodzie możesz wrócić do pracy, a pozostałą część "
        "urlopu przejmie tata.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 180 § 8 Kodeksu pracy; § 3 RW",
        deadline_pl="Najpóźniej 7 dni przed powrotem do pracy (art. 180 § 8 KP).",
        roles=["mother"],
        fulfils=["t_rezygnacja"],
        steps=[
            _employee(),
            FormStep(
                title_pl="Powrót do pracy",
                fields=[
                    FormField(
                        key="return_date",
                        label_pl="Termin powrotu do pracy",
                        type="date",
                        required=True,
                    )
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 180 § 8 Kodeksu pracy rezygnuję z pozostałej części urlopu macierzyńskiego "
                "i wracam do pracy od dnia {return_date}."
            )
        ],
        attachments=[
            Paragraph(
                text_pl="Kopia wniosku ojca dziecka (pracownika) o udzielenie pozostałej części urlopu macierzyńskiego albo kopia "
                "oświadczenia ubezpieczonego ojca dziecka o przerwaniu działalności zarobkowej w celu sprawowania opieki "
                "nad dzieckiem przez okres, który pozostał do końca urlopu macierzyńskiego."
            )
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 5 ------------------------------------------------------------------------------
    "leave_maternity_father": FormDefinition(
        code="leave_maternity_father",
        title_pl="Wniosek o udzielenie pozostałej części urlopu macierzyńskiego",
        description_pl="Składa go tata (pracownik), gdy mama rezygnuje z pozostałej części urlopu macierzyńskiego "
        "lub zasiłku po wykorzystaniu co najmniej 14 tygodni po porodzie.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 180 § 9 Kodeksu pracy; § 5 RW",
        deadline_pl="Najpóźniej 14 dni przed rozpoczęciem urlopu (art. 180 § 9 KP).",
        roles=["father"],
        fulfils=["t_tata_macierzynski"],
        steps=[
            _employee(),
            FormStep(title_pl="Dziecko", fields=_child()),
            FormStep(
                title_pl="Urlop",
                fields=[
                    FormField(
                        key="before_birth_used",
                        label_pl="Okres urlopu (zasiłku) macierzyńskiego wykorzystanego przez mamę przed porodem",
                        required=True,
                        hint_pl="Np. „od 01.03.2026 do 14.03.2026” albo „nie wykorzystała”.",
                    ),
                    FormField(key="leave_start", label_pl="Urlop od", type="date", required=True),
                    FormField(key="leave_end", label_pl="Urlop do", type="date", required=True),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 180 § 9 Kodeksu pracy wnoszę o udzielenie mi pozostałej części urlopu macierzyńskiego "
                "na dziecko {child_first_name} {child_last_name}, urodzone {child_birth_date}, w okresie od {leave_start} "
                "do {leave_end}."
            ),
            Paragraph(
                text_pl="Oświadczam, że okres urlopu macierzyńskiego (zasiłku macierzyńskiego) wykorzystanego przed porodem: "
                "{before_birth_used}."
            ),
        ],
        attachments=[
            _BIRTH_CERT,
            Paragraph(
                text_pl="Oświadczenie matki dziecka o zamiarze rezygnacji z pozostałej części urlopu macierzyńskiego "
                "(albo z pobierania zasiłku macierzyńskiego za ten okres)."
            ),
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 14 -----------------------------------------------------------------------------
    "leave_supplementary": FormDefinition(
        code="leave_supplementary",
        title_pl="Wniosek o udzielenie uzupełniającego urlopu macierzyńskiego",
        description_pl="Przysługuje, gdy dziecko urodziło się przedwcześnie lub po porodzie wymagało hospitalizacji. "
        "Wykorzystujesz go bezpośrednio po urlopie macierzyńskim.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 180² § 4 Kodeksu pracy; § 14 RW",
        deadline_pl="Najpóźniej 21 dni przed zakończeniem urlopu macierzyńskiego (art. 180² § 4 KP).",
        fulfils=["t_uzupelniajacy"],
        steps=[
            _employee(role=True),
            FormStep(
                title_pl="Urlop",
                fields=[
                    FormField(
                        key="maternity_end",
                        label_pl="Termin zakończenia urlopu macierzyńskiego",
                        type="date",
                        required=True,
                    ),
                    FormField(
                        key="leave_start",
                        label_pl="Uzupełniający urlop od",
                        type="date",
                        required=True,
                    ),
                    FormField(
                        key="leave_end",
                        label_pl="Uzupełniający urlop do",
                        type="date",
                        required=True,
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 180² § 4 Kodeksu pracy wnoszę o udzielenie mi uzupełniającego urlopu macierzyńskiego "
                "w okresie od {leave_start} do {leave_end}. Urlop macierzyński kończy się {maternity_end}."
            )
        ],
        attachments=[
            Paragraph(
                text_pl="Zaświadczenie ze szpitala, o którym mowa w art. 180² § 5 Kodeksu pracy (okres pobytu dziecka "
                "w szpitalu, tydzień ciąży lub masa urodzeniowa)."
            )
        ],
        statements=[
            FormField(
                key="other_parent_not_using",
                label_pl="Oświadczam, że drugi z rodziców dziecka nie zamierza korzystać z uzupełniającego urlopu "
                "macierzyńskiego ani z zasiłku macierzyńskiego za okres odpowiadający temu urlopowi",
                type="checkbox",
                required=True,
            )
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 15 -----------------------------------------------------------------------------
    "leave_parental": FormDefinition(
        code="leave_parental",
        title_pl="Wniosek o udzielenie urlopu rodzicielskiego (lub jego części)",
        description_pl="Urlop rodzicielski możesz wykorzystać jednorazowo albo w nie więcej niż 5 częściach.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 182¹ᵈ § 1 Kodeksu pracy; § 15 RW",
        deadline_pl="Najpóźniej 21 dni przed rozpoczęciem urlopu (art. 182¹ᵈ § 1 KP).",
        fulfils=["t_rodzicielski_mama", "t_rodzicielski_tata"],
        steps=[
            _employee(role=True),
            FormStep(title_pl="Sytuacja", fields=[_SITUATION, *_TAKEN_IN]),
            FormStep(
                title_pl="Urlop",
                fields=[
                    FormField(key="leave_start", label_pl="Urlop od", type="date", required=True),
                    FormField(key="leave_end", label_pl="Urlop do", type="date", required=True),
                    FormField(
                        key="used_so_far",
                        label_pl="Dotychczas wykorzystany urlop rodzicielski (lub zasiłek za jego okres)",
                        required=True,
                        hint_pl="Okres albo „nie korzystałem/am”.",
                    ),
                    FormField(
                        key="used_parts",
                        label_pl="Liczba wykorzystanych części urlopu (lub wniosków o zasiłek za jego części)",
                        type="number",
                        required=True,
                    ),
                    FormField(
                        key="za_zyciem",
                        label_pl="Dziecko ma zaświadczenie z art. 4 ust. 3 ustawy „Za życiem” (urlop w wymiarze z art. 182¹ᵃ § 2 KP)",
                        type="checkbox",
                    ),
                ],
            ),
            FormStep(
                title_pl="Drugi rodzic",
                fields=[
                    FormField(
                        key="other_parent",
                        label_pl="Drugi z rodziców w okresie objętym wnioskiem",
                        type="select",
                        required=True,
                        options=[
                            (
                                "none",
                                "nie zamierza korzystać z urlopu rodzicielskiego ani z zasiłku za jego okres",
                            ),
                            ("period", "zamierza korzystać w okresie (wpisz poniżej)"),
                        ],
                    ),
                    FormField(
                        key="other_parent_period",
                        label_pl="Okres, w którym korzysta drugi rodzic",
                        required=True,
                        when="other_parent=period",
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 182¹ᵈ § 1 Kodeksu pracy wnoszę o udzielenie mi urlopu rodzicielskiego (jego części) "
                "w okresie od {leave_start} do {leave_end}."
            ),
            Paragraph(
                text_pl="Dotychczas wykorzystany urlop rodzicielski (zasiłek za jego okres): {used_so_far}; liczba wykorzystanych "
                "części: {used_parts}."
            ),
            Paragraph(
                text_pl="Oświadczam, że drugi z rodziców dziecka {other_parent} {other_parent_period}."
            ),
        ],
        attachments=[
            Paragraph(text_pl=_BIRTH_CERT.text_pl, when="situation=birth"),
            Paragraph(
                text_pl="Kopia zaświadczenia, o którym mowa w art. 4 ust. 3 ustawy „Za życiem”.",
                when="za_zyciem",
            ),
            *_TAKEN_IN_DOCS,
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 16 -----------------------------------------------------------------------------
    "parental_work": FormDefinition(
        code="parental_work",
        title_pl="Wniosek o łączenie urlopu rodzicielskiego z pracą",
        description_pl="W czasie urlopu rodzicielskiego możesz pracować u swojego pracodawcy w wymiarze nie wyższym niż "
        "połowa etatu. Urlop wydłuża się wtedy proporcjonalnie.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 182¹ᵉ § 2 Kodeksu pracy; § 16 RW",
        deadline_pl="Najpóźniej 21 dni przed rozpoczęciem pracy (art. 182¹ᵉ § 2 KP).",
        fulfils=["t_praca_mama", "t_praca_tata"],
        steps=[
            _employee(role=True),
            FormStep(
                title_pl="Praca w czasie urlopu",
                fields=[
                    FormField(
                        key="work_time",
                        label_pl="Wymiar czasu pracy",
                        required=True,
                        hint_pl="Nie więcej niż połowa etatu, np. „1/2 etatu”.",
                    ),
                    FormField(
                        key="work_start",
                        label_pl="Łączę urlop z pracą od",
                        type="date",
                        required=True,
                    ),
                    FormField(key="work_end", label_pl="do", type="date", required=True),
                    FormField(
                        key="extension_work",
                        label_pl="Część urlopu powstała z proporcjonalnego wydłużenia",
                        type="select",
                        required=True,
                        options=[
                            ("no", "nie zamierzam łączyć jej z pracą"),
                            ("yes", "zamierzam łączyć ją z pracą w wymiarze (wpisz poniżej)"),
                        ],
                    ),
                    FormField(
                        key="extension_work_time",
                        label_pl="Wymiar czasu pracy w wydłużonej części",
                        required=True,
                        when="extension_work=yes",
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 182¹ᵉ § 2 Kodeksu pracy wnoszę o umożliwienie mi łączenia korzystania z urlopu "
                "rodzicielskiego z wykonywaniem pracy w wymiarze {work_time} w okresie od {work_start} do {work_end}."
            ),
            Paragraph(
                text_pl="Oświadczam, że części urlopu rodzicielskiego powstałej w wyniku proporcjonalnego wydłużenia "
                "{extension_work} {extension_work_time}."
            ),
        ],
        instructions_pl=[
            *EMPLOYER_INSTRUCTIONS[:1],
            "Pracodawca uwzględnia wniosek, chyba że nie pozwala na to organizacja pracy lub rodzaj pracy – "
            "o odmowie informuje Cię w ciągu 7 dni (art. 182¹ᵉ § 2 KP).",
        ],
        sources_pl=RW,
    ),
    # --- RW § 17 -----------------------------------------------------------------------------
    "leave_paternity": FormDefinition(
        code="leave_paternity",
        title_pl="Wniosek o udzielenie urlopu ojcowskiego (lub jego części)",
        description_pl="Urlop ojcowski trwa 2 tygodnie; możesz go wykorzystać jednorazowo albo w dwóch częściach, "
        "nie krótszych niż tydzień.",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 182³ § 2 Kodeksu pracy; § 17 RW",
        deadline_pl="Najpóźniej 7 dni przed rozpoczęciem urlopu (art. 182³ § 2 KP).",
        roles=["father"],
        fulfils=["t_ojcowski"],
        steps=[
            _employee(),
            FormStep(
                title_pl="Urlop",
                fields=[
                    FormField(key="leave_start", label_pl="Urlop od", type="date", required=True),
                    FormField(key="leave_end", label_pl="Urlop do", type="date", required=True),
                    FormField(key="adopted", label_pl="Dziecko przysposobione", type="checkbox"),
                    FormField(
                        key="used_before",
                        label_pl="Czy korzystałeś już z urlopu ojcowskiego (jego części)?",
                        type="select",
                        required=True,
                        options=[
                            ("no", "nie korzystałem"),
                            ("yes", "korzystałem (wpisz okres poniżej)"),
                        ],
                    ),
                    FormField(
                        key="used_before_period",
                        label_pl="Okres wykorzystanego urlopu ojcowskiego",
                        required=True,
                        when="used_before=yes",
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 182³ § 2 Kodeksu pracy wnoszę o udzielenie mi urlopu ojcowskiego (jego części) "
                "w okresie od {leave_start} do {leave_end}."
            ),
            Paragraph(
                text_pl="Oświadczam, że z urlopu ojcowskiego (jego części) {used_before} {used_before_period}."
            ),
        ],
        attachments=[
            _BIRTH_CERT,
            Paragraph(
                text_pl="Kopia prawomocnego postanowienia sądu o przysposobieniu dziecka.",
                when="adopted",
            ),
        ],
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RW § 18 -----------------------------------------------------------------------------
    "leave_taken_in": FormDefinition(
        code="leave_taken_in",
        title_pl="Wniosek o udzielenie urlopu na warunkach urlopu macierzyńskiego",
        description_pl="Dla rodzica, który przyjął dziecko na wychowanie i wystąpił do sądu o przysposobienie albo przyjął "
        "je jako rodzina zastępcza (poza zawodową).",
        submitted_to="employer",
        addressee_pl="Pracodawca",
        legal_basis_pl="art. 183 § 6 Kodeksu pracy; § 18 RW",
        deadline_pl="W ciągu 7 dni od przyjęcia dziecka; urlop zaczyna się najpóźniej 21 dni od przyjęcia (art. 183 § 6 KP).",
        fulfils=["t_na_warunkach"],
        steps=[
            _employee(role=True),
            FormStep(
                title_pl="Dziecko",
                fields=[
                    *_child(),
                    FormField(
                        key="situation",
                        label_pl="Przyjęcie dziecka",
                        type="select",
                        required=True,
                        options=SITUATION_OPTIONS[1:],
                    ),
                    *_TAKEN_IN,
                ],
            ),
            FormStep(
                title_pl="Urlop",
                fields=[
                    FormField(key="leave_start", label_pl="Urlop od", type="date", required=True),
                    FormField(key="leave_end", label_pl="Urlop do", type="date", required=True),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Na podstawie art. 183 § 6 Kodeksu pracy wnoszę o udzielenie mi urlopu na warunkach urlopu "
                "macierzyńskiego na dziecko {child_first_name} {child_last_name}, urodzone {child_birth_date}, przyjęte "
                "na wychowanie {placement_date}, w okresie od {leave_start} do {leave_end}."
            )
        ],
        attachments=_TAKEN_IN_DOCS,
        instructions_pl=EMPLOYER_INSTRUCTIONS,
        sources_pl=RW,
    ),
    # --- RZ § 12, § 13, § 16, załącznik nr 6 ------------------------------------------------
    "zus_zam": FormDefinition(
        code="zus_zam",
        title_pl="Wniosek o zasiłek macierzyński (ZAM)",
        description_pl="Składasz go do ZUS, jeśli zasiłek wypłaca ZUS – np. prowadzisz działalność, współpracujesz przy niej "
        "albo pracujesz na umowie u małego płatnika składek. Najwygodniej przez eZUS.",
        submitted_to="zus",
        addressee_pl="Zakład Ubezpieczeń Społecznych",
        legal_basis_pl="§ 12 i załącznik nr 6 RZ",
        deadline_pl="Za okres przed rozpoczęciem korzystania z zasiłku; roszczenie przedawnia się po 6 miesiącach od "
        "ostatniego dnia okresu, za który zasiłek przysługuje (art. 67 UZ).",
        fulfils=[
            "t_rodzicielski_mama",
            "t_rodzicielski_tata",
            "t_ojcowski",
            "t_uzupelniajacy",
            "t_usredniona",
            "t_przedawnienie",
        ],
        steps=[
            FormStep(
                title_pl="Płatnik składek",
                fields=[
                    FormField(
                        key="payer_nip",
                        label_pl="NIP płatnika składek",
                        hint_pl="Przy własnej działalności – Twój NIP.",
                    ),
                    FormField(key="payer_regon", label_pl="REGON płatnika składek"),
                    FormField(key="payer_name", label_pl="Nazwa płatnika składek", required=True),
                    FormField(
                        key="payer_address", label_pl="Adres płatnika składek", required=True
                    ),
                ],
            ),
            FormStep(
                title_pl="Ubezpieczony",
                fields=[
                    FormField(key="first_name", label_pl="Pierwsze imię", required=True),
                    FormField(key="last_name", label_pl="Nazwisko", required=True),
                    FormField(
                        key="applicant_role",
                        label_pl="Składam jako",
                        type="select",
                        required=True,
                        options=ROLE_OPTIONS,
                    ),
                    FormField(
                        key="pesel",
                        label_pl="PESEL",
                        required=True,
                        hint_pl="Gdy nie masz – seria i numer paszportu.",
                    ),
                    FormField(key="address", label_pl="Adres zamieszkania", required=True),
                    FormField(
                        key="self_insured",
                        label_pl="Podlegam ubezpieczeniu jako osoba prowadząca pozarolniczą działalność lub współpracująca, "
                        "duchowny albo marynarz (art. 6 ust. 1 pkt 5, 10 i 24 ustawy o systemie ubezpieczeń społecznych)",
                        type="checkbox",
                    ),
                ],
            ),
            FormStep(
                title_pl="Dziecko",
                fields=[
                    _SITUATION,
                    FormField(
                        key="due_date",
                        label_pl="Przewidywana data porodu",
                        type="date",
                        hint_pl="Gdy wniosek obejmuje okres przed porodem.",
                    ),
                    FormField(key="child_first_name", label_pl="Imię dziecka"),
                    FormField(key="child_last_name", label_pl="Nazwisko dziecka"),
                    FormField(
                        key="child_pesel", label_pl="PESEL dziecka", hint_pl="Jeśli został nadany."
                    ),
                    FormField(
                        key="child_birth_date", label_pl="Data urodzenia dziecka", type="date"
                    ),
                    FormField(key="birth_place", label_pl="Miejsce urodzenia dziecka"),
                    *_TAKEN_IN,
                    FormField(
                        key="za_zyciem",
                        label_pl="Dziecko ma zaświadczenie z art. 4 ust. 3 ustawy „Za życiem”",
                        type="checkbox",
                    ),
                ],
            ),
            FormStep(
                title_pl="Zasiłek",
                fields=[
                    FormField(
                        key="for_maternity",
                        label_pl="Zasiłek za okres urlopu macierzyńskiego",
                        type="checkbox",
                    ),
                    FormField(
                        key="for_taken_in",
                        label_pl="Zasiłek za okres urlopu na warunkach urlopu macierzyńskiego",
                        type="checkbox",
                    ),
                    FormField(
                        key="for_supplementary",
                        label_pl="Zasiłek za okres uzupełniającego urlopu macierzyńskiego",
                        type="checkbox",
                    ),
                    FormField(
                        key="for_parental",
                        label_pl="Zasiłek za okres urlopu rodzicielskiego",
                        type="checkbox",
                    ),
                    FormField(
                        key="for_paternity",
                        label_pl="Zasiłek za okres urlopu ojcowskiego",
                        type="checkbox",
                    ),
                    FormField(key="benefit_start", label_pl="Od dnia", type="date", required=True),
                    FormField(key="benefit_end", label_pl="Do dnia", type="date", required=True),
                    FormField(
                        key="full_leave",
                        label_pl="Zamierzam korzystać z pełnego wymiaru urlopu macierzyńskiego (na warunkach macierzyńskiego) "
                        "i rodzicielskiego, a co najmniej jeden dzień urlopu rodzicielskiego przypadnie w pierwszym roku "
                        "życia dziecka (stawka 81,5% – art. 30a UZ)",
                        type="checkbox",
                    ),
                    FormField(
                        key="part_info",
                        label_pl="Informacja o części urlopu rodzicielskiego lub ojcowskiego",
                        hint_pl="Np. „druga część urlopu rodzicielskiego”.",
                        when="for_parental",
                    ),
                    FormField(
                        key="hospital_from",
                        label_pl="Pobyt dziecka w szpitalu od",
                        type="date",
                        required=True,
                        when="for_supplementary",
                    ),
                    FormField(
                        key="hospital_to",
                        label_pl="Pobyt dziecka w szpitalu do",
                        type="date",
                        required=True,
                        when="for_supplementary",
                    ),
                ],
            ),
            FormStep(
                title_pl="Drugi rodzic i sytuacja matki",
                fields=[
                    FormField(
                        key="other_first_name",
                        label_pl="Drugi rodzic – pierwsze imię",
                        hint_pl="Gdy jego dane są potrzebne do rozpatrzenia wniosku.",
                    ),
                    FormField(key="other_last_name", label_pl="Drugi rodzic – nazwisko"),
                    FormField(key="other_pesel", label_pl="Drugi rodzic – PESEL"),
                    FormField(key="other_address", label_pl="Drugi rodzic – adres zamieszkania"),
                    FormField(
                        key="other_benefit",
                        label_pl="Drugi rodzic korzysta z zasiłku macierzyńskiego za okres urlopu rodzicielskiego lub uzupełniającego",
                        type="select",
                        required=True,
                        options=[("no", "nie"), ("yes", "tak (wpisz okres poniżej)")],
                    ),
                    FormField(
                        key="other_benefit_period",
                        label_pl="Okres zasiłku drugiego rodzica",
                        required=True,
                        when="other_benefit=yes",
                    ),
                    FormField(
                        key="mother_situation",
                        label_pl="Sytuacja matki dziecka mająca wpływ na prawo do zasiłku",
                        type="textarea",
                        hint_pl="Np. pobyt w szpitalu, rezygnacja z zasiłku, zgon, porzucenie dziecka. Zostaw puste, jeśli nie dotyczy.",
                    ),
                    FormField(
                        key="employer_event",
                        label_pl="Wniosek dotyczy sytuacji, gdy pracodawca",
                        type="select",
                        required=True,
                        options=[
                            ("none", "nie dotyczy"),
                            ("bankruptcy", "ogłosił upadłość"),
                            ("liquidation", "jest w likwidacji"),
                            ("unlawful", "rozwiązał umowę o pracę z naruszeniem przepisów prawa"),
                            ("death", "zmarł"),
                        ],
                    ),
                ],
            ),
            FormStep(
                title_pl="Wypłata",
                fields=[
                    FormField(
                        key="bank_account",
                        label_pl="Numer rachunku bankowego",
                        required=True,
                        hint_pl="26 cyfr",
                    ),
                    FormField(key="place", label_pl="Miejscowość", required=True),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Wnoszę o wypłatę zasiłku macierzyńskiego za okres od {benefit_start} do {benefit_end}. "
                "Wniosek dotyczy: {situation}."
            ),
            Paragraph(text_pl="Rodzaj okresu: urlop macierzyński.", when="for_maternity"),
            Paragraph(
                text_pl="Rodzaj okresu: urlop na warunkach urlopu macierzyńskiego.",
                when="for_taken_in",
            ),
            Paragraph(
                text_pl="Rodzaj okresu: uzupełniający urlop macierzyński.", when="for_supplementary"
            ),
            Paragraph(text_pl="Rodzaj okresu: urlop rodzicielski.", when="for_parental"),
            Paragraph(text_pl="Rodzaj okresu: urlop ojcowski.", when="for_paternity"),
            Paragraph(text_pl="Przewidywana data porodu: {due_date}.", when="due_date"),
            Paragraph(
                text_pl="Dziecko: {child_first_name} {child_last_name}, PESEL {child_pesel}, urodzone {child_birth_date} "
                "w miejscowości {birth_place}.",
                when="child_birth_date",
            ),
            Paragraph(
                text_pl="Oświadczam, że dziecko ma zaświadczenie z art. 4 ust. 3 ustawy „Za życiem”.",
                when="za_zyciem",
            ),
            Paragraph(
                text_pl="Zamierzam korzystać z pełnego wymiaru urlopu macierzyńskiego i rodzicielskiego; co najmniej jeden "
                "dzień urlopu rodzicielskiego przypadnie w pierwszym roku życia dziecka.",
                when="full_leave",
            ),
            Paragraph(text_pl="Część urlopu: {part_info}.", when="part_info"),
            Paragraph(
                text_pl="Pobyt dziecka w szpitalu: od {hospital_from} do {hospital_to}.",
                when="hospital_from",
            ),
            Paragraph(
                text_pl="Drugi rodzic: {other_first_name} {other_last_name}, PESEL {other_pesel}, {other_address}.",
                when="other_last_name",
            ),
            Paragraph(
                text_pl="Drugi rodzic korzysta z zasiłku za okres urlopu rodzicielskiego lub uzupełniającego: {other_benefit} {other_benefit_period}."
            ),
            Paragraph(
                text_pl="Sytuacja matki dziecka: {mother_situation}.", when="mother_situation"
            ),
            Paragraph(text_pl="Pracodawca: {employer_event}.", when="employer_event!=none"),
            Paragraph(text_pl="Zasiłek proszę przekazać na rachunek {bank_account}."),
        ],
        attachments=[
            Paragraph(
                text_pl="Zaświadczenie lekarskie wystawione na zwykłym druku określające przewidywaną datę porodu – za okres "
                "przed porodem (RZ § 13 ust. 1 pkt 1).",
                when="due_date",
            ),
            Paragraph(
                text_pl="Odpisu skróconego aktu urodzenia nie dołączasz – ZUS pobierze go z rejestru stanu cywilnego na "
                "podstawie danych dziecka (RZ § 13 ust. 2–3).",
                when="situation=birth",
            ),
            Paragraph(
                text_pl="Zaświadczenie sądu opiekuńczego o dacie wystąpienia o przysposobienie (z datą urodzenia dziecka) lub "
                "kopia wniosku z poświadczeniem sądu (RZ § 16 ust. 1).",
                when="situation=adoption",
            ),
            Paragraph(
                text_pl="Orzeczenie sądu o umieszczeniu dziecka w rodzinie zastępczej albo umowa ze starostą oraz dokument "
                "potwierdzający wiek dziecka (RZ § 16 ust. 2).",
                when="situation=foster",
            ),
            Paragraph(
                text_pl="Kopia prawomocnej decyzji o odroczeniu obowiązku szkolnego (RZ § 16 ust. 2 pkt 3).",
                when="school_deferred",
            ),
            Paragraph(
                text_pl="Kopia zaświadczenia z art. 4 ust. 3 ustawy „Za życiem”.", when="za_zyciem"
            ),
            Paragraph(
                text_pl="Zaświadczenie ze szpitala o pobycie dziecka.", when="for_supplementary"
            ),
        ],
        instructions_pl=[
            "ZUS wypłaca zasiłek na bieżąco po stwierdzeniu uprawnień, najpóźniej w ciągu 30 dni od wyjaśnienia ostatniej "
            "okoliczności potrzebnej do ustalenia prawa (art. 64 ust. 1 UZ).",
            "Jeśli masz zadłużenie składkowe powyżej 1% minimalnego wynagrodzenia, zasiłek przysługuje dopiero po spłacie "
            "całości; prawo przedawnia się, jeśli nie spłacisz go w ciągu 6 miesięcy (art. 2a UZ).",
            "Roszczenie o wypłatę zasiłku przedawnia się po 6 miesiącach od ostatniego dnia okresu, za który przysługuje "
            "(art. 67 UZ).",
            "Zasiłek macierzyński nie przysługuje za czas urlopu wychowawczego (Poradnik ZUS 2026).",
        ],
        sources_pl="Rozporządzenie w sprawie dokumentów do ustalenia prawa do zasiłków (RZ), § 12, § 13, § 16, załącznik nr 6",
    ),
    # --- Urząd stanu cywilnego (poza źródłami zadania – symulacja usługi gov.pl) --------------
    "civil_registry_extract": FormDefinition(
        code="civil_registry_extract",
        title_pl="Wniosek o odpis aktu urodzenia dziecka",
        description_pl="Odpis bywa potrzebny pracodawcy do wniosków o urlop (ZUS pobiera go sam). Składasz go w urzędzie "
        "stanu cywilnego, także online na gov.pl. To symulacja – wniosek nie trafi do urzędu.",
        submitted_to="registry",
        addressee_pl="Kierownik urzędu stanu cywilnego",
        legal_basis_pl="usługa „Odpis aktu urodzenia” na gov.pl (symulacja)",
        steps=[
            FormStep(
                title_pl="Wnioskodawca",
                fields=[
                    FormField(key="first_name", label_pl="Imię", required=True),
                    FormField(key="last_name", label_pl="Nazwisko", required=True),
                    FormField(key="pesel", label_pl="PESEL", required=True, hint_pl="11 cyfr"),
                    FormField(
                        key="applicant_role",
                        label_pl="Kim jesteś dla dziecka",
                        type="select",
                        required=True,
                        options=[("mother", "Matka"), ("father", "Ojciec")],
                    ),
                    FormField(key="place", label_pl="Miejscowość", required=True),
                ],
            ),
            FormStep(
                title_pl="Akt urodzenia",
                fields=[
                    *_child(),
                    FormField(key="birth_place", label_pl="Miejsce urodzenia", required=True),
                    FormField(
                        key="extract_type",
                        label_pl="Rodzaj odpisu",
                        type="select",
                        required=True,
                        options=[("short", "skrócony"), ("full", "zupełny")],
                    ),
                ],
            ),
        ],
        body=[
            Paragraph(
                text_pl="Wnoszę o wydanie odpisu {extract_type} aktu urodzenia dziecka {child_first_name} {child_last_name}, "
                "urodzonego {child_birth_date} w miejscowości {birth_place}."
            )
        ],
    ),
}


def _holds(condition: str | None, data: dict) -> bool:
    """`key`, `key=value` or `key!=value` against the form data."""
    if not condition:
        return True
    if "!=" in condition:
        key, value = condition.split("!=", 1)
        return str(data.get(key) or "") != value
    if "=" in condition:
        key, value = condition.split("=", 1)
        return str(data.get(key) or "") == value
    return data.get(condition) not in (None, "", False, 0)


def visible_fields(definition: FormDefinition, data: dict) -> list[FormField]:
    fields = [
        f
        for s in definition.steps
        if _holds(s.when, data)
        for f in s.fields
        if _holds(f.when, data)
    ]
    return [*fields, *definition.statements, TRUTH]


def missing_fields(definition: FormDefinition, data: dict) -> list[str]:
    """Keys of required visible fields that are empty (an unchecked required checkbox counts as empty)."""

    def empty(value: object) -> bool:
        return value is None or value == "" or value is False

    return [
        f.key for f in visible_fields(definition, data) if f.required and empty(data.get(f.key))
    ]


def role_of(definition: FormDefinition, data: dict) -> str | None:
    if len(definition.roles) == 1:
        return definition.roles[0]
    return data.get("applicant_role") or None
