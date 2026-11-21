"""Check that the route table is identical in all three places that define it.

1. frontend/src/lib/routes.ts          PUBLIC_PATHS: English route -> public (Polish) URL
2. infra/nginx/default.conf            map $frontend_uri (public -> English) and
                                       map $canonical_uri (English -> public)
3. frontend/src/app/<route>/page.tsx   one folder per English route

Usage: python scripts/check_routes.py   (or `make check-routes`). Exits 1 on any mismatch.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTES_TS = ROOT / "frontend/src/lib/routes.ts"
NGINX_CONF = ROOT / "infra/nginx/default.conf"
APP_DIR = ROOT / "frontend/src/app"


def read_public_paths() -> dict[str, str]:
    """Parse the PUBLIC_PATHS object literal from routes.ts."""
    text = ROUTES_TS.read_text(encoding="utf-8")
    body = re.search(r"PUBLIC_PATHS\s*=\s*\{(.*?)\}\s*as const", text, re.S)
    if body is None:
        sys.exit(f"Cannot find PUBLIC_PATHS in {ROUTES_TS}")
    return dict(re.findall(r'(\w+):\s*"(/[^"]*)"', body.group(1)))


def read_nginx_map(name: str) -> dict[str, str]:
    """Parse one `map $request_uri $<name> { ... }` block into {source segment: target segment}."""
    text = NGINX_CONF.read_text(encoding="utf-8")
    block = re.search(rf"map \$request_uri \${name}\s*\{{(.*?)\n\}}", text, re.S)
    if block is None:
        sys.exit(f"Cannot find map ${name} in {NGINX_CONF}")
    rows = re.findall(r"~\^/([\w-]+)\(\?<rest>\[/\?\]\.\*\)\?\$\s+/([\w-]+)\$rest;", block.group(1))
    return dict(rows)


def main() -> int:
    public = read_public_paths()  # {"calculator": "/kalkulator", ...}
    # Routes whose public URL equals the English one need no nginx entry (e.g. /admin).
    translated = {route: url.lstrip("/") for route, url in public.items() if url != f"/{route}"}

    expected_to_english = {pl: en for en, pl in translated.items()}  # kalkulator -> calculator
    expected_to_public = {en: pl for en, pl in translated.items()}  # calculator -> kalkulator

    errors: list[str] = []

    def compare(label: str, expected: dict[str, str], actual: dict[str, str]) -> None:
        for key in sorted(expected.keys() - actual.keys()):
            errors.append(f"{label}: missing row for '{key}'")
        for key in sorted(actual.keys() - expected.keys()):
            errors.append(f"{label}: unexpected row for '{key}' (not in routes.ts)")
        for key in sorted(expected.keys() & actual.keys()):
            if expected[key] != actual[key]:
                errors.append(f"{label}: '{key}' maps to '{actual[key]}', routes.ts says '{expected[key]}'")

    compare("nginx $frontend_uri", expected_to_english, read_nginx_map("frontend_uri"))
    compare("nginx $canonical_uri", expected_to_public, read_nginx_map("canonical_uri"))

    # Every route needs a page, and every page needs a route.
    page_folders = {p.parent.name for p in APP_DIR.glob("*/page.tsx")}
    for route in sorted(public.keys() - page_folders):
        errors.append(f"routes.ts: '{route}' has no folder frontend/src/app/{route}/page.tsx")
    for folder in sorted(page_folders - public.keys()):
        errors.append(f"frontend/src/app/{folder}/ has a page but is not in PUBLIC_PATHS")

    if errors:
        print("Route table mismatch:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Route table OK: {len(public)} routes ({len(translated)} translated by nginx).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
