"""Generic rules runtime: definitions + parameters + facts -> values, periods and messages.

A rule has a kind:
  wartosc     – a named value (`expression`) other rules can read by its code;
  okres       – a period of leave / allowance: `start` (date), `expression` (days), `rate`,
                `work` (part of full time worked), `person`; other rules read
                `<code>.start`, `<code>.koniec`, `<code>.dni`, `<code>.aktywny`;
  swiadczenie – a benefit card: `status`, aggregated `periods`, `payer`, texts;
  dokument / termin / ryzyko / informacja / zalozenie – messages shown to the user
                (termin: `expression` is the date);
  walidacja   – when `condition` is true the plan breaks the law: the calculation stops
                with `text_pl` (HTTP 422).
Every rule may have a `condition`; when it is false the rule is inactive.

Dependencies are read from the expressions themselves, so the order of rules never matters:
the runtime sorts values and periods topologically and rejects cycles.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from app.engine.expressions import (
    Evaluator,
    ExpressionError,
    format_value,
    parameter_references,
    references,
)
from app.engine.facts import FACT_ROOTS

NODE_KINDS = ("wartosc", "okres")
MESSAGE_KINDS = ("dokument", "termin", "ryzyko", "informacja", "zalozenie")
KINDS = (*NODE_KINDS, "swiadczenie", *MESSAGE_KINDS, "walidacja")
PERSON_LITERALS = {"mama": "mother", "tata": "father", "rodzina": "family"}
TEMPLATE = re.compile(r"\{([^{}]+)\}")
EXPRESSION_FIELDS = ("condition", "expression", "start", "rate", "work", "status", "payer")


@dataclass
class RuleDef:
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
    periods: list[str] = field(default_factory=list)
    status: str | None = None
    payer: str | None = None
    apply_to_pl: str = ""
    deadline_kind: str | None = None
    legal_basis: str = ""
    source: str = ""
    description_pl: str = ""
    active: bool = True

    def expressions(self) -> list[tuple[str, str]]:
        """(field, source) of every expression in the rule, including {…} in texts."""
        out = [(f, getattr(self, f)) for f in EXPRESSION_FIELDS if getattr(self, f)]
        if self.person and self.person not in PERSON_LITERALS:
            out.append(("person", self.person))
        for f in ("title_pl", "text_pl", "apply_to_pl"):
            for m in TEMPLATE.finditer(getattr(self, f) or ""):
                out.append((f, m.group(1)))
        return out

    @property
    def is_node(self) -> bool:
        return self.kind in NODE_KINDS


class PlanViolation(ValueError):
    """The plan breaks a legal limit (raised by `walidacja` rules)."""


class RuleSetError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


# --- Static analysis -----------------------------------------------------------------------


def rule_references(rule: RuleDef) -> set[str]:
    refs: set[str] = set()
    for _, src in rule.expressions():
        refs |= references(src)
    refs |= set(rule.periods)
    return refs


def analyse(rules: Iterable[RuleDef], param_keys: Iterable[str] | None = None) -> list[str]:
    """All problems of a rule set: syntax, unknown names / parameters, cycles. Polish messages."""
    rules = [r for r in rules if r.active]
    errors: list[str] = []
    nodes = {r.code: r for r in rules if r.is_node}
    codes = [r.code for r in rules]
    for dup in {c for c in codes if codes.count(c) > 1}:
        errors.append(f"Kod reguły „{dup}” występuje więcej niż raz")
    keys = set(param_keys) if param_keys is not None else None
    known = FACT_ROOTS | set(nodes)
    for rule in rules:
        if rule.kind not in KINDS:
            errors.append(f"{rule.code}: nieznany rodzaj reguły „{rule.kind}”")
        if rule.kind in ("wartosc", "okres", "termin") and not rule.expression:
            errors.append(f"{rule.code}: brak wyrażenia")
        if rule.kind == "okres" and not rule.start:
            errors.append(f"{rule.code}: okres wymaga daty początku")
        for fld, src in rule.expressions():
            try:
                unknown = references(src) - known
                if unknown:
                    errors.append(
                        f"{rule.code} ({fld}): nieznane dane: {', '.join(sorted(unknown))}"
                    )
                if keys is not None:
                    missing = parameter_references(src) - keys
                    if missing:
                        errors.append(
                            f"{rule.code} ({fld}): brak parametru: {', '.join(sorted(missing))}"
                        )
            except ExpressionError as exc:
                errors.append(f"{rule.code} ({fld}): {exc}")
        for p in rule.periods:
            if p not in nodes or nodes[p].kind != "okres":
                errors.append(f"{rule.code}: „{p}” nie jest okresem")
    if not errors:
        try:
            topological_order(rules)
        except RuleSetError as exc:
            errors.extend(exc.errors)
    return errors


def required_parameters(rules: list[RuleDef]) -> set[str]:
    """Parameter keys used by the active rules."""
    keys: set[str] = set()
    for rule in rules:
        if not rule.active:
            continue
        for _, src in rule.expressions():
            try:
                keys |= parameter_references(src)
            except ExpressionError:
                pass
    return keys


def topological_order(rules: Iterable[RuleDef]) -> list[RuleDef]:
    nodes = {r.code: r for r in rules if r.active and r.is_node}
    deps = {code: rule_references(r) & set(nodes) - {code} for code, r in nodes.items()}
    self_refs = [code for code, r in nodes.items() if code in rule_references(r)]
    if self_refs:
        raise RuleSetError([f"Reguła {c} odwołuje się do samej siebie" for c in self_refs])
    order: list[RuleDef] = []
    ready = sorted(c for c, d in deps.items() if not d)
    remaining = {c: set(d) for c, d in deps.items() if d}
    while ready:
        code = ready.pop(0)
        order.append(nodes[code])
        for other, d in list(remaining.items()):
            d.discard(code)
            if not d:
                del remaining[other]
                ready.append(other)
        ready.sort()
    if remaining:
        raise RuleSetError([f"Zależność cykliczna: {', '.join(sorted(remaining))}"])
    return order


def dependents(rules: Iterable[RuleDef]) -> dict[str, list[str]]:
    """code -> codes of rules that read it (for the admin panel)."""
    rules = [r for r in rules if r.active]
    nodes = {r.code for r in rules if r.is_node}
    out: dict[str, list[str]] = {c: [] for c in nodes}
    for r in rules:
        try:
            for ref in rule_references(r) & nodes:
                if ref != r.code:
                    out[ref].append(r.code)
        except ExpressionError:
            continue
    return {k: sorted(v) for k, v in out.items()}


# --- Evaluation ----------------------------------------------------------------------------


@dataclass
class Message:
    rule: RuleDef
    person: str
    text: str
    title: str
    date: date | None = None


@dataclass
class RunResult:
    scope: dict[str, Any]
    periods: list[dict[str, Any]]
    benefits: list[dict[str, Any]]
    messages: list[Message]
    trace: dict[str, Any]
    errors: dict[str, str]


class Runtime:
    def __init__(self, rules: Iterable[RuleDef], params: Mapping[str, Any], today: date):
        self.rules = [r for r in rules if r.active]
        self.params = params
        self.today = today
        self.order = topological_order(self.rules)

    def _person(self, rule: RuleDef, ev: Evaluator) -> str | None:
        raw = rule.person or "rodzina"
        if raw in PERSON_LITERALS:
            return PERSON_LITERALS[raw]
        value = ev.eval(raw)
        return PERSON_LITERALS.get(str(value)) if value else None

    def _render(self, template: str, ev: Evaluator) -> str:
        return TEMPLATE.sub(lambda m: format_value(ev.eval(m.group(1))), template or "")

    def run(self, facts: Mapping[str, Any]) -> RunResult:
        scope: dict[str, Any] = dict(facts)
        ev = Evaluator(scope, self.params, self.today)
        trace: dict[str, Any] = {}
        errors: dict[str, str] = {}

        def active(rule: RuleDef) -> bool:
            return not rule.condition or bool(ev.eval(rule.condition))

        periods: list[dict[str, Any]] = []
        for rule in self.order:
            try:
                if rule.kind == "wartosc":
                    scope[rule.code] = ev.eval(rule.expression or "None") if active(rule) else None
                    trace[rule.code] = scope[rule.code]
                    continue
                inactive = {
                    "aktywny": False,
                    "dni": 0,
                    "start": None,
                    "koniec": None,
                    "osoba": None,
                    "stawka": None,
                    "praca": 0,
                }
                if not active(rule):
                    scope[rule.code] = inactive
                    trace[rule.code] = inactive
                    continue
                days = ev.eval(rule.expression or "0")
                start = ev.eval(rule.start or "None")
                if not days or days <= 0 or not isinstance(start, date):
                    scope[rule.code] = inactive
                    trace[rule.code] = inactive
                    continue
                days = int(round(days))
                period = {
                    "aktywny": True,
                    "dni": days,
                    "start": start,
                    "koniec": start + timedelta(days=days - 1),
                    "osoba": self._person(rule, ev),
                    "stawka": ev.eval(rule.rate) if rule.rate else None,
                    "praca": ev.eval(rule.work) if rule.work else 0,
                    "platnik": ev.eval(rule.payer) if rule.payer else None,
                    "tytul": self._render(rule.title_pl, ev),
                }
                scope[rule.code] = period
                trace[rule.code] = period
                periods.append({"rule": rule, **period})
            except (ExpressionError, TypeError, ValueError, ZeroDivisionError) as exc:
                errors[rule.code] = str(exc)
                scope[rule.code] = None if rule.kind == "wartosc" else {"aktywny": False, "dni": 0}
                trace[rule.code] = None

        violations: list[str] = []
        messages: list[Message] = []
        benefits: list[dict[str, Any]] = []
        others = sorted((r for r in self.rules if not r.is_node), key=lambda r: (r.order, r.code))
        for rule in others:
            try:
                if not active(rule):
                    continue
                if rule.kind == "walidacja":
                    violations.append(self._render(rule.text_pl, ev) or rule.title_pl)
                    continue
                if rule.kind == "swiadczenie":
                    status = ev.eval(rule.status) if rule.status else "informacja"
                    if not status:
                        continue
                    benefits.append(
                        {
                            "rule": rule,
                            "status": status,
                            "person": self._person(rule, ev) or "family",
                            "title": self._render(rule.title_pl, ev),
                            "summary": self._render(rule.text_pl, ev),
                            "apply_to": self._render(rule.apply_to_pl, ev),
                            "payer": ev.eval(rule.payer) if rule.payer else None,
                            "periods": [
                                scope[p] | {"code": p}
                                for p in rule.periods
                                if scope.get(p, {}).get("aktywny")
                            ],
                        }
                    )
                    continue
                when = ev.eval(rule.expression) if rule.kind == "termin" else None
                if rule.kind == "termin" and not isinstance(when, date):
                    continue
                messages.append(
                    Message(
                        rule=rule,
                        person=self._person(rule, ev) or "family",
                        text=self._render(rule.text_pl, ev),
                        title=self._render(rule.title_pl, ev),
                        date=when,
                    )
                )
            except (ExpressionError, TypeError, ValueError, ZeroDivisionError) as exc:
                errors[rule.code] = str(exc)
        if violations:
            raise PlanViolation("; ".join(violations))
        return RunResult(scope, periods, benefits, messages, trace, errors)
