"""Typed read access to legal parameters for the rules engine.

The engine never reads the database. The API layer loads `legal_parameter` rows valid on a
given date (`parameters_valid_on`) and wraps them in `Params`; tests build `Params` from plain
dicts. A missing key is a configuration error, so it raises loudly instead of guessing.
"""

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any, Protocol


class MissingParameterError(KeyError):
    """A legal parameter needed by the engine is not defined for the requested date."""


class _Row(Protocol):
    key: str
    value: Any


class Params:
    def __init__(self, values: Mapping[str, Any], on: date):
        self._values = dict(values)
        self.on = on

    @classmethod
    def from_rows(cls, rows: Iterable[_Row], on: date) -> "Params":
        return cls({row.key: row.value for row in rows}, on)

    def get(self, key: str) -> Any:
        try:
            return self._values[key]
        except KeyError:
            raise MissingParameterError(
                f"Legal parameter '{key}' is not valid on {self.on}"
            ) from None

    def number(self, key: str) -> float:
        return float(self.get(key))

    def integer(self, key: str) -> int:
        return int(self.get(key))

    def table(self, key: str) -> dict[str, Any]:
        value = self.get(key)
        if not isinstance(value, dict):
            raise TypeError(f"Legal parameter '{key}' is not a table")
        return value

    def lookup(self, key: str, field: str) -> Any:
        """One field of a table parameter, e.g. ('parental_leave_weeks', 'single')."""
        table = self.table(key)
        if field not in table:
            raise MissingParameterError(f"Legal parameter '{key}' has no field '{field}'")
        return table[field]

    def by_count(self, key: str, count: int) -> Any:
        """Value from a table keyed by number of children; the highest key covers 'and more'."""
        table = self.table(key)
        top = max(int(k) for k in table)
        return table[str(min(max(count, 1), top))]
