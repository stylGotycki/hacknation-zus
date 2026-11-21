"""Persona scenarios (E3): ready-made family profiles used by the examples page and the mocks."""

import json
from pathlib import Path

_DIR = Path(__file__).parent


def load_scenarios() -> list[dict]:
    """All scenario files S1..S12, sorted by their number."""
    files = sorted(_DIR.glob("S*.json"), key=lambda p: int(p.stem[1:]))
    return [json.loads(p.read_text(encoding="utf-8")) for p in files]
