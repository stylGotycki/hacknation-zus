"""Generates docs/reguly.md – the catalogue of seed rules (code, kind, expression, legal basis).

Usage: python scripts/gen_rules_doc.py   (run from the repository root; needs backend deps).
"""

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.seed.rules import all_rules  # noqa: E402

KIND = {
    "wartosc": "Wartość", "okres": "Okres", "swiadczenie": "Świadczenie", "dokument": "Dokument",
    "termin": "Termin", "ryzyko": "Ryzyko", "informacja": "Informacja", "zalozenie": "Założenie",
    "walidacja": "Walidacja",
}
SOURCE = {"KP": "Kodeks pracy", "UZ": "Ustawa zasiłkowa", "RZ": "Rozp. – dokumenty", "RW": "Rozp. – wnioski",
          "PR": "Poradnik ZUS 2026", "ZAL": "Załącznik"}


def cell(text: str | None) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def main() -> None:
    rules = all_rules()
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rules:
        groups[r.get("group_pl") or "Inne"].append(r)
    lines = [
        "# Katalog reguł (seed)",
        "",
        f"{len(rules)} reguł ze źródeł: " + ", ".join(f"{k} – {v}" for k, v in SOURCE.items()) + ".",
        "Plik generowany: `python scripts/gen_rules_doc.py`. Aktualne reguły (po zmianach w panelu) są w bazie.",
        "",
    ]
    for group, items in groups.items():
        lines += [f"## {group}", "", "| Kod | Rodzaj | Opis | Wyrażenie / warunek | Podstawa |", "|---|---|---|---|---|"]
        for r in items:
            expr = r.get("expression") or ""
            if r["kind"] == "okres":
                expr = f"start: {r.get('start')}; dni: {expr}; stawka: {r.get('rate')}"
            cond = r.get("condition")
            if cond:
                expr = f"{expr} **gdy** {cond}" if expr else f"**gdy** {cond}"
            lines.append(
                f"| `{r['code']}` | {KIND[r['kind']]} | {cell(r.get('title_pl'))} | `{cell(expr)}` | "
                f"{r['source']}: {cell(r.get('legal_basis'))} |"
            )
        lines.append("")
    (ROOT / "docs/reguly.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"docs/reguly.md: {len(rules)} rules")


if __name__ == "__main__":
    main()
