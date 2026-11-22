"""Records the product demo (about 2.5 minutes) as a video with on-screen captions.

Needs the stack running (default http://localhost:3000, the backend behind it) and Playwright:

    pip install playwright && playwright install chromium
    python scripts/demo/record_demo.py                 # -> scripts/demo/out/demo.webm (+ demo.mp4 if ffmpeg exists)
    BASE_URL=http://localhost python scripts/demo/record_demo.py

Captions are drawn into the page (a bar at the bottom) and a dot follows the mouse, so the video needs no editing.
Every scene is `say(caption, seconds)` plus the actions; the pacing is in one place (PACE) for easy tuning.
The same text is in docs/film/scenariusz.md (narration script for a voice-over).
"""

import asyncio
import os
import re
import shutil
import subprocess
from pathlib import Path

from playwright.async_api import Page, async_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:3000")
CHROME = os.environ.get("CHROME_PATH")  # optional: path to a system Chrome
OUT = Path(__file__).parent / "out"
PACE = float(os.environ.get("PACE", "1.16"))  # >1 = slower
SIZE = {"width": 1280, "height": 720}

OVERLAY_JS = """
(() => {
  if (window.__demoInit) return; window.__demoInit = true;
  const add = () => {
    if (document.getElementById('demo-cap')) return;
    const cap = document.createElement('div'); cap.id = 'demo-cap';
    cap.style.cssText = 'position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:1100px;z-index:2147483647;' +
      'background:rgba(0,40,70,.94);color:#fff;font:600 22px/1.3 Lato,Arial,sans-serif;padding:10px 22px;border-radius:6px;' +
      'text-align:center;box-shadow:0 2px 12px rgba(0,0,0,.35);display:none;pointer-events:none';
    document.body.appendChild(cap);
    const dot = document.createElement('div'); dot.id = 'demo-dot';
    dot.style.cssText = 'position:fixed;width:22px;height:22px;border-radius:50%;background:rgba(250,184,86,.85);' +
      'border:2px solid #fff;z-index:2147483647;pointer-events:none;left:-50px;top:-50px;transform:translate(-50%,-50%)';
    document.body.appendChild(dot);
    window.addEventListener('mousemove', e => { dot.style.left = e.clientX + 'px'; dot.style.top = e.clientY + 'px'; }, true);
  };
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
  window.__caption = t => { add(); const c = document.getElementById('demo-cap'); c.textContent = t; c.style.display = t ? 'block' : 'none'; };
})();
"""


async def say(page: Page, text: str, seconds: float) -> None:
    """Shows a caption and waits, so the viewer has time to read and look."""
    await page.evaluate("t => window.__caption && window.__caption(t)", text)
    await page.wait_for_timeout(int(seconds * 1000 * PACE))


async def click(page: Page, locator, pause: float = 0.6) -> None:
    """Moves the mouse to the element first, so the viewer sees where the click lands."""
    await locator.scroll_into_view_if_needed()
    box = await locator.bounding_box()
    if box:
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=18)
    await page.wait_for_timeout(int(250 * PACE))
    await locator.click()
    await page.wait_for_timeout(int(pause * 1000 * PACE))


async def show(page: Page, locator, above: int = 140) -> None:
    """Scrolls so the element sits near the top of the viewport (the caption bar stays free below)."""
    await locator.first.wait_for(state="visible", timeout=15000)
    await locator.first.evaluate("(e, d) => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - d)", above)
    await page.wait_for_timeout(int(500 * PACE))


async def fill_form_quick(page: Page) -> None:
    """Fills every step of an application with plausible values and stops on the summary."""
    for _ in range(10):
        fields = page.locator("main input:not([type=checkbox]):not([type=radio]), main select")
        for i in range(await fields.count()):
            el = fields.nth(i)
            if not await el.is_visible() or await el.input_value():
                continue
            tag = await el.evaluate("e => e.tagName")
            if tag == "SELECT":
                values = await el.evaluate("e => [...e.options].map(o => o.value).filter(Boolean)")
                if values:
                    await el.select_option(value=values[0])
            else:
                kind = await el.get_attribute("type") or "text"
                await el.fill({"date": "2026-12-01", "number": "1", "tel": "600100200"}.get(kind, "Przykład"))
        await show(page, page.locator("main h2").first, above=110)
        await page.wait_for_timeout(int(1200 * PACE))
        summary = page.get_by_role("button", name="Przejdź do podsumowania")
        if await summary.count():
            await click(page, summary)
            await show(page, page.locator("main h2").first, above=110)
            return
        await click(page, page.get_by_role("button", name="Dalej"), pause=0.5)


async def run(page: Page) -> None:
    # 1. Start page
    await page.goto(BASE + "/")
    await say(page, "Przewodnik rodzica: jedno miejsce na urlopy, zasiłki i wnioski dla świeżych rodziców", 6)
    await say(page, "Wersja demonstracyjna: dane są symulowane, aplikacja nie ma AI ani OCR", 4)

    # 2. Demo entry from the footer
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await say(page, "W stopce jest wejście do dema z gotowymi kontami", 2.5)
    await click(page, page.get_by_role("link", name="Wejście do dema aplikacji"))
    await say(page, "Można zalogować się własnym PESEL-em albo wybrać konto demonstracyjne", 5)
    await click(page, page.locator("main button").filter(has_text="Karolina"))
    await say(page, "Symulacja mObywatela: potwierdzamy logowanie", 2)
    await click(page, page.get_by_role("button", name="Potwierdź w aplikacji mObywatel"), pause=0)
    await page.wait_for_url("**/dane-zus", timeout=15000)
    await page.wait_for_timeout(800)

    # 3. ZUS data -> calculation
    await say(page, "Dane o ubezpieczeniu pobieramy z (symulowanego) ZUS – nic nie trzeba przepisywać", 3.5)
    await click(page, page.get_by_role("button", name="Pobierz dane z ZUS"), pause=2)
    await say(page, "Poświadczenie ubezpieczenia, podstawa wymiaru z 12 miesięcy, e-ZLA", 4)
    await click(page, page.get_by_role("button", name="Policz uprawnienia z danych ZUS"), pause=2.5)
    await page.get_by_text("Zasiłki razem (brutto)").scroll_into_view_if_needed()
    await say(page, "Silnik reguł liczy uprawnienia i kwoty według przepisów z dnia wyliczenia", 5)

    # 4. Timeline with the "today" line
    await click(page, page.get_by_role("link", name="Plan urlopów – oś czasu").first)
    await page.wait_for_timeout(1500)
    today = page.get_by_label("Dziś,", exact=False).first
    await today.scroll_into_view_if_needed()
    await page.evaluate("window.scrollBy(0, -260)")
    await say(page, "Oś czasu: pomarańczowa linia pokazuje dziś, to co minęło jest wyszarzone", 5)
    await click(page, page.get_by_role("button", name="Szczegóły").nth(2), pause=1)
    await say(page, "Każdy punkt ma szczegóły: kwoty, płatnika, dokumenty i podstawę prawną", 5)

    # 5. My leaves and benefits
    await click(page, page.get_by_role("link", name="Moje urlopy i zasiłki").first)
    await page.wait_for_timeout(1500)
    await say(page, "Moje urlopy i zasiłki: co zrobić teraz i do kiedy", 5)
    await page.evaluate("window.scrollBy(0, 560)")
    await say(page, "Ile pieniędzy już wypłacono, a ile jeszcze będzie", 4)
    await page.evaluate("window.scrollBy(0, 560)")
    await say(page, "Dla każdego urlopu: ile dni wykorzystano, ile zostało i do kiedy", 5)

    # 6. Applications
    await click(page, page.get_by_role("link", name="Wnioski").first)
    await page.wait_for_timeout(1500)
    await say(page, "Wnioski: system podpowiada, co złożyć, do kogo i w jakim terminie", 5)
    fill = page.get_by_role("button", name=re.compile("Wypełnij wniosek|Kontynuuj wniosek"))
    if await fill.count():
        await click(page, fill.first, pause=1)
        await show(page, page.locator("main h2").first, above=110)
        await say(page, "Formularz zgodny ze wzorem, wstępnie wypełniony danymi z wyniku", 4)
        await fill_form_quick(page)
        await say(page, "Podsumowanie przed wysłaniem: podgląd dokumentu i oświadczenie o prawdziwości", 5)
        await page.get_by_label("Oświadczam, że dane zawarte we wniosku są zgodne z prawdą").check()
        send = page.get_by_role("button", name="Wyślij do pracodawcy")
        if not await send.count():
            send = page.get_by_role("button", name="Wyślij do ZUS")
        await click(page, send, pause=2)
        await show(page, page.get_by_role("heading", name="Złożone wnioski"), above=110)
        await say(page, "Wniosek ma status i historię – widać go też na osi czasu", 4)

    # 7. Admin
    await page.goto(BASE + "/admin")
    await page.locator("input").first.fill("admin")
    await click(page, page.get_by_role("button", name="Zaloguj"), pause=1.5)
    await page.get_by_label("Szukaj parametru").wait_for(timeout=15000)
    await say(page, "Panel administratora: liczby z przepisów i reguły to dane, nie kod", 5)
    await page.get_by_label("Szukaj parametru").fill("becikowe")
    await page.wait_for_timeout(1000)
    await say(page, "Zmiana przepisu to zmiana parametru – bez programisty i bez wdrożenia", 5)
    await click(page, page.get_by_role("tab", name="Reguły"), pause=0.5)
    await page.get_by_text("reguł ze źródeł").wait_for(timeout=15000)
    await say(page, "Reguły ma własny język, historię zmian i test na profilu", 5)

    # 8. Closing
    await page.goto(BASE + "/")
    await say(page, "Przewodnik rodzica – od pierwszego pytania do złożonego wniosku. Dziękujemy!", 5)


async def main() -> None:
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        launch = {"args": ["--no-sandbox", "--no-proxy-server"]}
        if CHROME:
            launch["executable_path"] = CHROME
        browser = await p.chromium.launch(**launch)
        context = await browser.new_context(
            viewport=SIZE, record_video_dir=str(OUT), record_video_size=SIZE, locale="pl-PL"
        )
        await context.add_init_script(OVERLAY_JS)
        page = await context.new_page()
        await run(page)
        video = page.video
        await context.close()
        path = Path(await video.path())
        target = OUT / "demo.webm"
        path.replace(target)
        await browser.close()
    if shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(target), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "23", "-pix_fmt", "yuv420p", str(OUT / "demo.mp4")],
            check=True,
        )
    print("Done:", OUT)


if __name__ == "__main__":
    asyncio.run(main())
