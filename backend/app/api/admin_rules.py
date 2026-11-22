"""Admin panel: rules of the guide (list, edit with validation, dependencies, test run)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.admin import require_admin
from app.core.db import DbSession
from app.engine.expressions import (
    FUNCTIONS,
    RUNTIME_FUNCTIONS,
    ExpressionError,
    parameter_references,
)
from app.engine.facts import FACT_FIELDS, FACT_ROOTS
from app.engine.runtime import (
    KINDS,
    PERSON_LITERALS,
    PlanViolation,
    RuleDef,
    analyse,
    dependents,
    rule_references,
)
from app.engine.service import evaluate_profile
from app.engine.store import RULE_FIELDS, load_params, load_rules, rule_dict, rules_version, to_def
from app.models import LegalParameter, Rule, RuleHistory
from app.rules import FamilyProfile
from app.seed.rules_2026 import all_rules

router = APIRouter(prefix="/admin/rules", tags=["admin"], dependencies=[Depends(require_admin)])

CODE = re.compile(r"^[a-z][a-z0-9_]{1,79}$")

KIND_INFO = {
    "wartosc": "Wartość – nazwana liczba, data, tekst albo tak/nie; inne reguły czytają ją po kodzie.",
    "okres": "Okres – urlop lub zasiłek na osi czasu: początek (data), wyrażenie = liczba dni, stawka, praca, osoba, płatnik. "
    "Inne reguły czytają kod.start, kod.koniec, kod.dni, kod.aktywny.",
    "swiadczenie": "Świadczenie – karta wyniku: status (przysluguje / warunkowo / nie_przysluguje / informacja), opis, okresy.",
    "dokument": "Dokument – co dołączyć do wniosku (przypisany do świadczenia).",
    "termin": "Termin – wyrażenie = data; rodzaj: apply (złożyć do) albo use_by (wykorzystać do).",
    "ryzyko": "Ryzyko – ostrzeżenie (high / medium / info).",
    "informacja": "Informacja – wskazówka pokazywana w wyniku.",
    "zalozenie": "Założenie obliczeń – jak liczone są kwoty.",
    "walidacja": "Walidacja planu – gdy warunek jest prawdziwy, plan jest odrzucany z podanym komunikatem.",
}
PERIOD_KINDS = {
    "maternity": "urlop macierzyński / na warunkach urlopu macierzyńskiego",
    "supplementary": "uzupełniający urlop macierzyński",
    "parental": "urlop rodzicielski",
    "paternity": "urlop ojcowski",
    "pregnancy_sickness": "zwolnienie lekarskie w ciąży",
    "maternity_equivalent": "zasiłek w wysokości zasiłku macierzyńskiego",
}
SOURCES = {
    "KP": "Kodeks pracy (dział VIII)",
    "UZ": "Ustawa o świadczeniach pieniężnych z ubezpieczenia społecznego w razie choroby i macierzyństwa",
    "RZ": "Rozporządzenie w sprawie dokumentów do ustalenia prawa do zasiłków",
    "RW": "Rozporządzenie w sprawie wniosków i dokumentów dotyczących uprawnień rodzicielskich",
    "PR": "Poradnik ZUS 2026 – zasiłki dla rodziców",
    "ZAL": "Załącznik do zadania – zasady wyliczania podstawy",
}


class RuleIn(BaseModel):
    code: str
    kind: str
    title_pl: str = ""
    group_pl: str = ""
    order: int = 0
    condition: str | None = None
    expression: str | None = None
    start: str | None = None
    rate: str | None = None
    work: str | None = None
    person: str | None = None
    period_kind: str | None = None
    text_pl: str = ""
    severity: str | None = None
    benefit: str | None = None
    periods: list[str] = Field(default_factory=list)
    status: str | None = None
    payer: str | None = None
    apply_to_pl: str = ""
    deadline_kind: str | None = None
    late_text_pl: str = ""
    legal_basis: str = ""
    source: str = ""
    description_pl: str = ""
    active: bool = True
    note: str = ""  # why the rule was changed (stored in the history)


class RuleOut(RuleIn):
    modified: bool = False
    in_seed: bool = False
    uses: list[str] = []  # rules this one reads
    used_by: list[str] = []  # rules that read this one
    facts: list[str] = []  # facts this one reads
    parameters: list[str] = []
    errors: list[str] = []


def _clean(body: RuleIn) -> dict[str, Any]:
    data = body.model_dump(exclude={"note"})
    for key, value in data.items():
        if isinstance(value, str) and key not in ("code", "kind"):
            data[key] = value.strip()
    for key in (
        "condition",
        "expression",
        "start",
        "rate",
        "work",
        "person",
        "period_kind",
        "severity",
        "benefit",
        "status",
        "payer",
        "deadline_kind",
    ):
        if not data.get(key):
            data[key] = None
    return data


def _check_fields(data: dict[str, Any]) -> list[str]:
    errors = []
    if not CODE.match(data["code"]):
        errors.append(
            "Kod: małe litery, cyfry i podkreślenia, zaczyna się od litery (np. moja_regula)"
        )
    if data["code"] in FACT_ROOTS or data["code"] in FUNCTIONS or data["code"] in RUNTIME_FUNCTIONS:
        errors.append(f"Kod „{data['code']}” jest zarezerwowany (dane lub funkcja)")
    if data["kind"] not in KINDS:
        errors.append(f"Rodzaj musi być jednym z: {', '.join(KINDS)}")
    if data["kind"] == "okres" and data.get("period_kind") not in PERIOD_KINDS:
        errors.append(f"Rodzaj okresu musi być jednym z: {', '.join(PERIOD_KINDS)}")
    if data["kind"] == "ryzyko" and data.get("severity") not in ("high", "medium", "info"):
        errors.append("Waga ryzyka: high, medium albo info")
    if data["kind"] == "termin" and data.get("deadline_kind") not in ("apply", "use_by"):
        errors.append("Rodzaj terminu: apply albo use_by")
    return errors


def _param_keys(db: DbSession) -> set[str]:
    return set(db.scalars(select(LegalParameter.key).distinct()))


def _rule_errors(errors: list[str], code: str) -> list[str]:
    return [
        e
        for e in errors
        if e.startswith(f"{code} ")
        or e.startswith(f"{code}:")
        or f"„{code}”" in e
        or (e.startswith("Zależność cykliczna") and code in e)
    ]


def _out(
    row: Rule | dict[str, Any],
    rules: list[RuleDef],
    used_by: dict[str, list[str]],
    errors: list[str],
    seed_codes: set[str],
) -> RuleOut:
    data = rule_dict(row) if isinstance(row, Rule) else row
    rule = to_def(data)
    node_codes = {r.code for r in rules if r.is_node}
    try:
        refs = rule_references(rule)
        params = sorted(set().union(*(parameter_references(src) for _, src in rule.expressions())))
    except ExpressionError:
        refs, params = set(), []
    return RuleOut(
        **data,
        modified=bool(getattr(row, "modified", False)),
        in_seed=data["code"] in seed_codes,
        uses=sorted(refs & node_codes - {rule.code}),
        used_by=used_by.get(rule.code, []),
        facts=sorted(refs & FACT_ROOTS),
        parameters=params,
        errors=_rule_errors(errors, rule.code),
    )


@router.get("", response_model=list[RuleOut])
def list_rules(db: DbSession) -> list[RuleOut]:
    rows = list(db.scalars(select(Rule).order_by(Rule.kind, Rule.order, Rule.code)))
    rules = [to_def(r) for r in rows]
    errors = analyse(rules, _param_keys(db))
    used_by = dependents(rules)
    seed_codes = {r["code"] for r in all_rules()}
    return [_out(r, rules, used_by, errors, seed_codes) for r in rows]


class Dictionary(BaseModel):
    kinds: dict[str, str]
    period_kinds: dict[str, str]
    sources: dict[str, str]
    persons: list[str]
    facts: list[dict[str, str]]
    functions: list[dict[str, str]]
    parameters: list[dict[str, Any]]
    rules: list[dict[str, str]]
    version: str | None


@router.get("/dictionary", response_model=Dictionary)
def dictionary(db: DbSession) -> Dictionary:
    """Everything an expression can use: facts, functions, parameters and other rules."""
    params = load_params(db, date.today())
    labels = {
        p.key: p.label_pl or p.description_pl
        for p in db.scalars(select(LegalParameter).order_by(LegalParameter.key))
    }
    functions = [{"name": n, "description": d} for n, (_, d) in FUNCTIONS.items()]
    functions += [
        {"name": "param", "description": "wartość parametru prawnego: param('rate_parental')"},
        {
            "name": "tabela",
            "description": "pole parametru-tabeli: tabela('parental_leave_weeks', 'single')",
        },
        {"name": "dzis", "description": "dzisiejsza data"},
        {
            "name": "jesli",
            "description": "jesli(warunek, gdy_tak, gdy_nie) – liczy tylko potrzebną gałąź",
        },
    ]
    rules = load_rules(db)
    return Dictionary(
        kinds=KIND_INFO,
        period_kinds=PERIOD_KINDS,
        sources=SOURCES,
        persons=[*PERSON_LITERALS, "(albo wyrażenie zwracające 'mama' / 'tata')"],
        facts=[{"path": p, "type": t, "description": d} for p, t, d in FACT_FIELDS],
        functions=functions,
        parameters=[
            {"key": k, "label": labels.get(k, ""), "value": v} for k, v in sorted(params.items())
        ],
        rules=[{"code": r.code, "kind": r.kind, "title": r.title_pl} for r in rules if r.is_node],
        version=rules_version(db),
    )


class ValidateOut(BaseModel):
    ok: bool
    errors: list[str]


def _candidate_set(db: DbSession, data: dict[str, Any], replace: str | None) -> list[RuleDef]:
    rules = [r for r in load_rules(db) if r.code != (replace or data["code"])]
    return [*rules, to_def(data)]


@router.post("/validate", response_model=ValidateOut)
def validate(body: RuleIn, db: DbSession, replace: str | None = None) -> ValidateOut:
    """Checks a draft rule against the whole rule set without saving it."""
    data = _clean(body)
    errors = _check_fields(data) or analyse(_candidate_set(db, data, replace), _param_keys(db))
    return ValidateOut(ok=not errors, errors=errors)


def _save(db: DbSession, row: Rule, data: dict[str, Any], note: str) -> None:
    errors = _check_fields(data) or analyse(_candidate_set(db, data, row.code), _param_keys(db))
    if errors:
        raise HTTPException(422, {"message": "Reguła ma błędy – nie zapisano", "errors": errors})
    if row.id is not None:
        db.add(RuleHistory(code=row.code, data=jsonable_encoder(rule_dict(row)), note=note))
    for key in RULE_FIELDS:
        if key != "code":
            setattr(row, key, data[key])
    row.modified = True
    db.commit()


def _response(db: DbSession, code: str) -> RuleOut:
    return next(r for r in list_rules(db) if r.code == code)


@router.post("", response_model=RuleOut, status_code=201)
def create_rule(body: RuleIn, db: DbSession) -> RuleOut:
    data = _clean(body)
    if db.scalar(select(Rule).where(Rule.code == data["code"])) is not None:
        raise HTTPException(409, f"Reguła „{data['code']}” już istnieje")
    row = Rule(code=data["code"])
    _check = _check_fields(data) or analyse(_candidate_set(db, data, None), _param_keys(db))
    if _check:
        raise HTTPException(422, {"message": "Reguła ma błędy – nie zapisano", "errors": _check})
    db.add(row)
    _save(db, row, data, body.note or "Nowa reguła")
    return _response(db, row.code)


def _get(db: DbSession, code: str) -> Rule:
    row = db.scalar(select(Rule).where(Rule.code == code))
    if row is None:
        raise HTTPException(404, f"Nie ma reguły „{code}”")
    return row


@router.put("/{code}", response_model=RuleOut)
def update_rule(code: str, body: RuleIn, db: DbSession) -> RuleOut:
    """Saves a changed rule. The whole rule set must stay valid (names, parameters, no cycles).

    Applies to calculations from now on; submitted applications keep the rules version they had.
    """
    row = _get(db, code)
    data = _clean(body)
    if data["code"] != code:
        raise HTTPException(422, "Kodu reguły nie można zmienić – utwórz nową regułę")
    _save(db, row, data, body.note or "Zmiana w panelu")
    return _response(db, code)


@router.delete("/{code}", status_code=204)
def delete_rule(code: str, db: DbSession) -> None:
    """Deletes a rule added in the panel. Seed rules can only be switched off (active = false)."""
    row = _get(db, code)
    if code in {r["code"] for r in all_rules()}:
        raise HTTPException(409, "Reguły z bazowego zestawu nie można usunąć – możesz ją wyłączyć")
    rules = [r for r in load_rules(db) if r.code != code]
    errors = analyse(rules, _param_keys(db))
    if errors:
        raise HTTPException(
            422, {"message": "Inne reguły korzystają z tej reguły", "errors": errors}
        )
    db.add(RuleHistory(code=code, data=jsonable_encoder(rule_dict(row)), note="Usunięta"))
    db.delete(row)
    db.commit()


@router.post("/{code}/reset", response_model=RuleOut)
def reset_rule(code: str, db: DbSession) -> RuleOut:
    """Restores the version from the six sources (seed)."""
    row = _get(db, code)
    seed = next((r for r in all_rules() if r["code"] == code), None)
    if seed is None:
        raise HTTPException(409, "Reguła nie pochodzi z bazowego zestawu")
    data = {f: seed.get(f) for f in RULE_FIELDS}
    data = _clean(RuleIn(**{k: v for k, v in data.items() if v is not None}))
    _save(db, row, data, "Przywrócono wersję bazową")
    row.modified = False
    db.commit()
    return _response(db, code)


class HistoryOut(BaseModel):
    changed_at: str | None
    note: str
    data: dict[str, Any]


@router.get("/{code}/history", response_model=list[HistoryOut])
def history(code: str, db: DbSession) -> list[HistoryOut]:
    rows = db.scalars(
        select(RuleHistory).where(RuleHistory.code == code).order_by(RuleHistory.id.desc())
    )
    return [
        HistoryOut(
            changed_at=r.changed_at.isoformat() if r.changed_at else None, note=r.note, data=r.data
        )
        for r in rows
    ]


class TestIn(BaseModel):
    profile: FamilyProfile
    draft: RuleIn | None = None  # optional: try a rule before saving it
    on: date | None = None


class TestOut(BaseModel):
    ok: bool
    violation: str | None = None
    result: dict[str, Any] | None = None
    values: dict[str, Any] = {}
    errors: dict[str, str] = {}


@router.post("/test", response_model=TestOut)
def test_run(body: TestIn, db: DbSession) -> TestOut:
    """Runs the rules (with an optional draft) for a profile and returns every computed value."""
    rules = load_rules(db)
    if body.draft is not None:
        data = _clean(body.draft)
        problems = _check_fields(data) or analyse(
            _candidate_set(db, data, data["code"]), _param_keys(db)
        )
        if problems:
            raise HTTPException(422, {"message": "Reguła ma błędy", "errors": problems})
        rules = _candidate_set(db, data, data["code"])
    on = body.on or date.today()
    try:
        result, run = evaluate_profile(
            body.profile,
            rules,
            load_params(db, on),
            date.today(),
            params_date=on,
            with_comparison=False,
        )
    except PlanViolation as exc:
        return TestOut(ok=False, violation=str(exc))
    return TestOut(
        ok=True,
        result=jsonable_encoder(result),
        values=jsonable_encoder(run.trace),
        errors=run.errors,
    )


class GraphOut(BaseModel):
    nodes: list[dict[str, str]]
    edges: list[list[str]]


@router.get("/graph", response_model=GraphOut)
def graph(db: DbSession) -> GraphOut:
    """Dependency graph: an edge [a, b] means rule b reads rule a."""
    rules = [r for r in load_rules(db) if r.active]
    used_by = dependents(rules)
    nodes = [
        {"code": r.code, "kind": r.kind, "group": r.group_pl, "title": r.title_pl} for r in rules
    ]
    edges = [[a, b] for a, readers in used_by.items() for b in readers]
    return GraphOut(nodes=nodes, edges=edges)
