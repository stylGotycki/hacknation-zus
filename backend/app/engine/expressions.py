"""A small, safe expression language for rules edited in the admin panel.

Syntax is a subset of Python: numbers, 'texts', True/False, None, names with dots
(`mama.zatrudnienie`), arithmetic (+ - * / //), comparisons, `and` / `or` / `not`,
`x if warunek else y`, `in [..]` and calls of whitelisted functions (see FUNCTIONS).
Nothing else is allowed: no attribute access on objects, no imports, no lambdas.

Missing data is `None`: arithmetic with None gives None, comparisons with None are False.
`jesli(warunek, a, b)` is evaluated lazily, like `a if warunek else b`.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Callable, Mapping
from datetime import date, timedelta
from functools import lru_cache
from typing import Any


class ExpressionError(ValueError):
    """Syntax error or a forbidden construct in a rule expression."""


def format_value(value: Any) -> str:
    """Polish formatting of a value inside texts: dates dd.mm.rrrr, decimal comma, tak/nie."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "tak" if value else "nie"
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}".replace(",", " ")
        return f"{value:,.2f}".replace(",", " ").replace(".", ",").rstrip("0").rstrip(",")
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


# --- Functions available in expressions ----------------------------------------------------


def _add_months(d: date | None, months: int | None) -> date | None:
    if d is None or months is None:
        return None
    month0 = d.month - 1 + int(months)
    year = d.year + month0 // 12
    month = month0 % 12 + 1
    last = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ][month - 1]
    return date(year, month, min(d.day, last))


def _add_days(d: date | None, days: float | None) -> date | None:
    if d is None or days is None:
        return None
    return d + timedelta(days=int(days))


def _days_between(a: date | None, b: date | None) -> int | None:
    """Number of days from a to b (b - a)."""
    if a is None or b is None:
        return None
    return (b - a).days


def _end_of_year(d: date | None, plus_years: int = 0) -> date | None:
    if d is None:
        return None
    return date(d.year + int(plus_years), 12, 31)


def _weeks(n: float | None) -> int | None:
    return None if n is None else int(round(n * 7))


def _ceil(x: float | None) -> int | None:
    return None if x is None else math.ceil(x)


def _safe(fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapped(*args: Any) -> Any:
        if any(a is None for a in args):
            return None
        return fn(*args)

    return wrapped


def _mean(values: list[float] | None) -> float | None:
    vals = [v for v in (values or []) if v is not None]
    return sum(vals) / len(vals) if vals else None


def _count_key(n: int | None) -> str | None:
    """Key of a "by number of children" table: '1' … '5' (5 = five and more)."""
    return None if n is None else str(max(1, min(int(n), 5)))


def _overlap(a: Any, b: Any) -> bool:
    """Two periods (rule values of kind okres) share at least one day."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    if not (a.get("aktywny") and b.get("aktywny")):
        return False
    return a["start"] <= b["koniec"] and b["start"] <= a["koniec"]


def _latest(*values: Any) -> Any:
    vals = [v for v in values if v is not None]
    return max(vals) if vals else None


def _earliest(*values: Any) -> Any:
    vals = [v for v in values if v is not None]
    return min(vals) if vals else None


# name -> (callable, description shown in the admin panel)
FUNCTIONS: dict[str, tuple[Callable[..., Any], str]] = {
    "min": (_safe(min), "najmniejsza z wartości"),
    "max": (_safe(max), "największa z wartości"),
    "abs": (_safe(abs), "wartość bezwzględna"),
    "zaokr": (_safe(lambda x, n=2: round(x, int(n))), "zaokrąglenie: zaokr(x, 2)"),
    "zaokr_gora": (_ceil, "zaokrąglenie w górę do liczby całkowitej"),
    "tygodnie": (_weeks, "liczba dni w n tygodniach (tydzień = 7 dni kalendarzowych)"),
    "dodaj_dni": (_add_days, "data przesunięta o n dni: dodaj_dni(data, n)"),
    "dodaj_mies": (_add_months, "data przesunięta o n miesięcy"),
    "dni_miedzy": (_days_between, "liczba dni od daty a do daty b"),
    "koniec_roku": (_end_of_year, "31 grudnia roku daty (+ n lat): koniec_roku(data, 6)"),
    "najpozniej": (
        _latest,
        "największa z podanych wartości, pomija brakujące (np. najpóźniejsza data)",
    ),
    "najwczesniej": (_earliest, "najmniejsza z podanych wartości, pomija brakujące"),
    "naklada": (_overlap, "czy dwa okresy (reguły typu okres) mają wspólny dzień"),
    "srednia": (_mean, "średnia z listy liczb"),
    "klucz_dzieci": (_count_key, "klucz tabeli wg liczby dzieci: '1'…'5' (5 = pięcioro i więcej)"),
    "jest": (lambda x: x is not None and x != "", "czy wartość jest podana"),
    "brak": (lambda x: x is None or x == "", "czy wartości brak"),
}
# Provided by the runtime (need the parameters / context): param, tabela, dzis, jesli.
RUNTIME_FUNCTIONS = {
    "param": "wartość parametru prawnego: param('rate_parental')",
    "tabela": "pole parametru-tabeli: tabela('maternity_leave_weeks', klucz_dzieci(2))",
    "dzis": "data obliczenia",
    "jesli": "jesli(warunek, gdy_tak, gdy_nie) – liczone leniwie",
}

_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.IfExp,
    ast.Call,
    ast.Name,
    ast.Attribute,
    ast.Load,
    ast.Constant,
    ast.List,
    ast.Tuple,
)


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


@lru_cache(maxsize=4096)
def parse(source: str) -> ast.Expression:
    """Parses and checks an expression. Raises ExpressionError with a Polish message."""
    text = (source or "").strip()
    if not text:
        raise ExpressionError("Puste wyrażenie")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Błąd składni w kolumnie {exc.offset}: {exc.msg}") from exc
    known = set(FUNCTIONS) | set(RUNTIME_FUNCTIONS)
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(f"Niedozwolona konstrukcja: {type(node).__name__}")
        if isinstance(node, ast.Name | ast.Attribute):
            name = node.id if isinstance(node, ast.Name) else node.attr
            if name.startswith("_"):
                raise ExpressionError("Nazwy zaczynające się od podkreślenia są niedozwolone")
        if isinstance(node, ast.Attribute) and _dotted(node) is None:
            raise ExpressionError(
                "Kropka jest dozwolona tylko w nazwach danych (np. mama.zatrudnienie)"
            )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in known:
                name = _dotted(node.func) or "?"
                raise ExpressionError(f"Nieznana funkcja: {name}")
            if node.keywords:
                raise ExpressionError("Argumenty nazwane nie są dozwolone")
    return tree


def references(source: str) -> set[str]:
    """Names the expression reads (first segment of dotted names; function names excluded)."""
    tree = parse(source)
    refs: set[str] = set()
    funcs = set(FUNCTIONS) | set(RUNTIME_FUNCTIONS)

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            for arg in node.args:
                visit(arg)
            return
        if isinstance(node, ast.Attribute | ast.Name):
            name = _dotted(node)
            if name and name.split(".")[0] not in funcs:
                refs.add(name.split(".")[0])
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return refs


def parameter_references(source: str) -> set[str]:
    """Parameter keys used through param('…') / tabela('…', …)."""
    keys: set[str] = set()
    for node in ast.walk(parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("param", "tabela")
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            keys.add(str(node.args[0].value))
    return keys


class Evaluator:
    """Evaluates parsed expressions against a mapping of names (facts, values, periods)."""

    def __init__(
        self,
        scope: Mapping[str, Any],
        params: Mapping[str, Any],
        today: date,
    ) -> None:
        self.scope = scope
        self.params = params
        self.today = today

    # -- public -----------------------------------------------------------------------------
    def eval(self, source: str) -> Any:
        return self._eval(parse(source).body)

    # -- helpers ----------------------------------------------------------------------------
    def _lookup(self, dotted: str) -> Any:
        parts = dotted.split(".")
        value: Any = self.scope.get(parts[0])
        for part in parts[1:]:
            if isinstance(value, Mapping):
                value = value.get(part)
            else:
                return None
        return value

    def _param(self, key: str) -> Any:
        if key not in self.params:
            raise ExpressionError(f"Brak parametru: {key}")
        return self.params[key]

    def _table(self, key: str, field: Any) -> Any:
        table = self._param(key)
        if field is None:
            return None
        if not isinstance(table, Mapping):
            raise ExpressionError(f"Parametr {key} nie jest tabelą")
        if str(field) not in table:
            raise ExpressionError(f"Parametr {key} nie ma pola {field}")
        return table[str(field)]

    def _eval(self, node: ast.AST) -> Any:  # noqa: C901 – one switch over node types
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name | ast.Attribute):
            return self._lookup(_dotted(node) or "")
        if isinstance(node, ast.List | ast.Tuple):
            return [self._eval(e) for e in node.elts]
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result: Any = True
                for value in node.values:
                    result = self._eval(value)
                    if not result:
                        return result
                return result
            for value in node.values:
                result = self._eval(value)
                if result:
                    return result
            return result
        if isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            if operand is None:
                return None
            return -operand if isinstance(node.op, ast.USub) else +operand
        if isinstance(node, ast.BinOp):
            left, right = self._eval(node.left), self._eval(node.right)
            if left is None or right is None:
                return None
            op = node.op
            if isinstance(op, ast.Add):
                if isinstance(left, str) or isinstance(right, str):
                    return format_value(left) + format_value(right)
                return left + right
            if isinstance(op, ast.Sub):
                return left - right
            if isinstance(op, ast.Mult):
                return left * right
            if isinstance(op, ast.Div):
                return None if right == 0 else left / right
            if isinstance(op, ast.FloorDiv):
                return None if right == 0 else left // right
            return None if right == 0 else left % right
        if isinstance(node, ast.Compare):
            left = self._eval(node.left)
            for op, comp in zip(node.ops, node.comparators, strict=True):
                right = self._eval(comp)
                if isinstance(op, ast.In | ast.NotIn):
                    ok = left in (right or [])
                    ok = ok if isinstance(op, ast.In) else not ok
                elif isinstance(op, ast.Eq):
                    ok = left == right
                elif isinstance(op, ast.NotEq):
                    ok = left != right
                elif left is None or right is None:
                    return False
                elif isinstance(op, ast.Lt):
                    ok = left < right
                elif isinstance(op, ast.LtE):
                    ok = left <= right
                elif isinstance(op, ast.Gt):
                    ok = left > right
                else:
                    ok = left >= right
                if not ok:
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self._eval(node.body) if self._eval(node.test) else self._eval(node.orelse)
        if isinstance(node, ast.Call):
            name = node.func.id  # type: ignore[attr-defined] – checked in parse()
            if name == "jesli":
                if len(node.args) != 3:
                    raise ExpressionError("jesli() wymaga 3 argumentów")
                test, yes, no = node.args
                return self._eval(yes) if self._eval(test) else self._eval(no)
            args = [self._eval(a) for a in node.args]
            if name == "dzis":
                return self.today
            if name == "param":
                return self._param(str(args[0]))
            if name == "tabela":
                return self._table(str(args[0]), args[1])
            fn = FUNCTIONS[name][0]
            try:
                return fn(*args)
            except TypeError as exc:
                raise ExpressionError(f"Złe argumenty funkcji {name}: {exc}") from exc
        raise ExpressionError(f"Niedozwolona konstrukcja: {type(node).__name__}")
