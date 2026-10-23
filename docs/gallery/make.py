"""The Devpost gallery: the product, not the proof. 3:2, from the live site.

    python docs/gallery/make.py

Each image is one thing a parent or a coach gets, photographed from the
deployed site at 2x. Anything simulated says so in its own caption on
the page; nothing is retouched.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = "https://da78ygi6ol1oi.cloudfront.net"
OUT = Path(__file__).resolve().parent
W, H = 1440, 960

SHOTS = [
    ("1-the-day.png", "/", None, "The hero: the claim and a day, an hour at a time"),
    ("2-coaching-in-the-moment.png", "/", "text=Coaching in the moment", "The nudge when the best hour goes quiet"),
    ("3-ask-out-loud.png", "/", "text=By voice, in this browser", "Ask out loud: the live MCP answer, read aloud"),
    ("4-measured.png", "/", "#evidence", "Every result and its verdict, the opt-in check included"),
    ("5-families-you-follow.png", "/coach/", None, "The coach's view of the families who shared"),
    ("6-how-it-counts.png", "/", "#how", "How it counts: a reply inside five seconds is one turn"),
    ("7-the-weeks-plan.png", "/", "#day section:has(h3:has-text('plan'))", "The week's plan, written by Claude on Amazon Bedrock behind the number gate"),
    ("8-two-agents.png", "/evidence/", "#agents", "Two Strands agents that may only say what a tool returned"),
    ("9-your-own-day.png", "/", "#yours", "Your own day in ten minutes: six steps with a Bee"),
]


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, color_scheme="light")
        page = ctx.new_page()
        for name, path, anchor, caption in SHOTS:
            page.goto(SITE + path)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1200)
            if anchor:
                el = page.locator(anchor).first
                el.scroll_into_view_if_needed()
                box = el.bounding_box()
                page.evaluate("y => window.scrollBy(0, y - 90)", box["y"] if box else 0)
                page.wait_for_timeout(500)
            if name.startswith("6-"):
                play = page.locator("#how button", has_text="Play").first
                if play.count():
                    play.click()
                    page.wait_for_timeout(9000)
            if name.startswith("3-"):
                chip = page.locator("button", has_text="How was our talking today?").first
                if chip.count():
                    chip.click()
                    page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / name))
            print(f"{name}: {caption}")
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
