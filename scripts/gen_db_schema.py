"""Generates docs/baza-danych.md – the database schema (ER diagram in Mermaid + table catalogue).

The tables are read from the SQLAlchemy models, so the document cannot drift from the code.
Usage: python scripts/gen_db_schema.py   (run from the repository root; needs backend deps).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import app.models  # noqa: E402,F401  (registers the models)
from app.core.db import Base  # noqa: E402

TABLES_PL = {
    "family": "Rodzina i jej profil – jedno konto (mObywatel) = jedna rodzina. Zapisany stan kalkulatora i kontakty rodziców.",
    "application_draft": "Wersja robocza wniosku (krok i wpisane dane) – wraca po ponownym zalogowaniu.",
    "application": "Złożony wniosek z historią statusów i migawką parametrów prawnych z dnia złożenia.",
    "legal_parameter": "Stała prawna (tygodnie, stawki, progi) z okresem obowiązywania – prawo ma wersje w czasie.",
    "rule": "Reguła silnika (wartość, okres, świadczenie, dokument, termin, ryzyko…) edytowana w panelu admina.",
    "rule_history": "Poprzednie wersje reguł (ślad zmian z panelu administratora).",
}

COLUMNS_PL = {
    ("family", "owner_id"): "identyfikator konta mObywatel (mock) lub gościa",
    ("family", "profile"): "JSON: guide_state, calculated_on, contacts (patrz niżej)",
    ("application_draft", "form_code"): "kod formularza, dla dwóch ról `kod:rola`",
    ("application_draft", "step"): "numer kroku, na którym użytkownik skończył",
    ("application_draft", "data"): "JSON: wpisane pola formularza",
    ("application", "form_code"): "kod formularza (np. zam, leave_parental)",
    ("application", "status"): "submitted → in_progress → decided",
    ("application", "data"): "JSON: dane wniosku",
    ("application", "submitted_to"): "adresat: employer / zus / registry",
    ("application", "history"): "JSON: lista {at, status, note}",
    ("application", "params_snapshot"): "JSON: parametry prawne z dnia złożenia",
    ("application", "rules_version"): "wersja zestawu reguł (czas ostatniej zmiany)",
    ("legal_parameter", "key"): "klucz techniczny, np. maternity_weeks",
    ("legal_parameter", "value"): "JSON: liczba, tekst albo tabela wartości",
    ("legal_parameter", "valid_from"): "początek obowiązywania",
    ("legal_parameter", "valid_to"): "koniec obowiązywania (NULL = obowiązuje)",
    ("legal_parameter", "unit"): "jednostka w panelu: number, percent, pln, weeks, days…",
    ("rule", "code"): "unikalny kod reguły; zależności czytane z wyrażeń",
    ("rule", "kind"): "wartosc / okres / swiadczenie / dokument / termin / ryzyko / informacja / zalozenie / walidacja",
    ("rule", "expression"): "wyrażenie w języku reguł",
    ("rule", "late_text_pl"): "porada po upływie terminu (tylko reguły `termin`)",
    ("rule", "modified"): "TRUE – zmieniona w panelu, seed jej nie nadpisuje",
    ("rule_history", "code"): "kod reguły (powiązanie logiczne z rule.code, bez klucza obcego)",
    ("rule_history", "data"): "JSON: pełna poprzednia wersja reguły",
}

JSON_SHAPES = """\
### Kształt kolumn JSON

**`family.profile`**
```json
{
  "guide_state": { "form": {...}, "step": 6, "profile": { "child": {...}, "mother": {...}, "father": {...}, "plan": {...} } },
  "calculated_on": "2026-11-18",
  "contacts": {
    "mother": { "first_name": "…", "last_name": "…", "pesel": "…", "address": "…", "employer_name": "…", "employer_address": "…", "place": "…" },
    "father": { "…": "to samo – dane drugiego rodzica wpisane we wniosku" }
  }
}
```

**`application.history`**
```json
[ { "at": "2026-11-03T10:00:00+01:00", "status": "submitted", "note": "Wniosek złożony" },
  { "at": "2026-11-10T10:00:00+01:00", "status": "decided",   "note": "Sprawa rozpatrzona – świadczenie przyznane" } ]
```
"""


def mermaid_type(col) -> str:
    name = col.type.__class__.__name__.upper()
    return {"JSON": "json", "STRING": "string", "TEXT": "text", "INTEGER": "int", "BOOLEAN": "bool",
            "DATETIME": "datetime", "DATE": "date"}.get(name, name.lower())


def keys(table, col) -> str:
    out = []
    if col.primary_key:
        out.append("PK")
    if col.foreign_keys:
        out.append("FK")
    if col.unique:
        out.append("UK")
    return ",".join(out)


def er_diagram() -> str:
    lines = ["erDiagram"]
    for t in Base.metadata.sorted_tables:
        lines.append(f"    {t.name} {{")
        for c in t.columns:
            k = keys(t, c)
            lines.append(f"        {mermaid_type(c)} {c.name}{(' ' + k) if k else ''}")
        lines.append("    }")
    for t in Base.metadata.sorted_tables:
        for c in t.columns:
            for fk in c.foreign_keys:
                lines.append(f'    {fk.column.table.name} ||--o{{ {t.name} : "{c.name}"')
    lines.append('    rule ||..o{ rule_history : "code (logicznie)"')
    return "\n".join(lines)


def catalogue() -> str:
    out = []
    for t in Base.metadata.sorted_tables:
        out.append(f"### `{t.name}`\n\n{TABLES_PL.get(t.name, '')}\n")
        out.append("| Kolumna | Typ | Null | Domyślnie | Klucze / uwagi |")
        out.append("|---|---|---|---|---|")
        for c in t.columns:
            kind = c.type.compile(dialect=__import__("sqlalchemy.dialects.postgresql", fromlist=["x"]).dialect())
            default = ""
            if c.server_default is not None:
                default = f"`{c.server_default.arg}`" if hasattr(c.server_default, "arg") else "serwer"
            elif c.default is not None and getattr(c.default, "is_scalar", False):
                default = f"`{c.default.arg!r}`"
            notes = []
            if c.primary_key:
                notes.append("**PK**")
            for fk in c.foreign_keys:
                notes.append(f"**FK** → `{fk.column.table.name}.{fk.column.name}` (ON DELETE {fk.ondelete or 'NO ACTION'})")
            if c.unique:
                notes.append("unikalna")
            desc = COLUMNS_PL.get((t.name, c.name))
            if desc:
                notes.append(desc)
            out.append(f"| `{c.name}` | {kind} | {'tak' if c.nullable else 'nie'} | {default} | {'; '.join(notes)} |")
        extra = []
        for idx in sorted(t.indexes, key=lambda i: i.name or ""):
            cols = ", ".join(c.name for c in idx.columns)
            extra.append(f"indeks `{idx.name}` ({cols})")
        from sqlalchemy import UniqueConstraint

        for cons in t.constraints:
            if isinstance(cons, UniqueConstraint) and cons.name:
                extra.append(f"ograniczenie unikalności `{cons.name}` ({', '.join(c.name for c in cons.columns)})")
        if extra:
            out.append("\nIndeksy i ograniczenia: " + "; ".join(extra) + ".")
        out.append("")
    return "\n".join(out)


def main() -> None:
    doc = f"""# Schemat bazy danych

Plik generowany przez `scripts/gen_db_schema.py` z modeli SQLAlchemy (`backend/app/models/`).
Produkcyjnie PostgreSQL 16 (kolumny JSON jako `JSONB`), w testach i demo SQLite.
Schemat powstaje z modeli (`create_all` + dodawanie brakujących kolumn), bez migracji.

![Schemat bazy danych](diagramy/6-schemat-bazy.png)

```mermaid
{er_diagram()}
```

## Zasady projektu

- **Stan i dane użytkownika** (`family`, `application_draft`, `application`) są powiązane kluczami obcymi
  z `ON DELETE CASCADE`: usunięcie rodziny usuwa jej wersje robocze i wnioski.
- **Konto = rodzina.** `family.owner_id` to identyfikator z logowania mObywatel (mock) albo losowy identyfikator gościa;
  nie ma osobnej tabeli użytkowników, bo tożsamość pochodzi z zewnętrznego systemu.
- **Prawo jest w danych, nie w kodzie.** `legal_parameter` (stałe z okresem obowiązywania) i `rule` (reguły) edytuje
  administrator; `rule_history` przechowuje poprzednie wersje reguł.
- **Złożony wniosek jest niezmienny wobec zmian prawa.** `application.params_snapshot` i `rules_version` utrwalają
  parametry z dnia złożenia, więc zmiana w panelu dotyczy tylko nowych wniosków.
- **Elastyczne dane w JSON.** Profil rodziny, dane formularzy i historia statusów są w kolumnach JSON(B); ich kształt
  waliduje warstwa aplikacji (Pydantic, definicje formularzy), a nie baza.
- **Związki logiczne bez klucza obcego:** `rule_history.code → rule.code` (historia przeżywa usunięcie reguły),
  `application*.form_code → definicje formularzy` (w kodzie: `backend/app/forms/definitions.py`).

## Tabele

{catalogue()}
{JSON_SHAPES}"""
    (ROOT / "docs" / "baza-danych.md").write_text(doc, encoding="utf-8")
    print("docs/baza-danych.md")


if __name__ == "__main__":
    main()
