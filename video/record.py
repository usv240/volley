"""Drive the deployed site through every web beat and record it at 4K.

    python record.py

Reads build/narration.json for how long each line actually takes, then
holds each shot for exactly that long. Writes build/web.mp4 and
build/web-timings.json, which say where every beat landed so the
assembler can cut the narration to the picture rather than the other
way round.

4K
--
The frame is 3840x2160 and the viewport is set to exactly that, because
Playwright records the viewport and pads a larger record_video_size with
grey rather than upscaling. The page is zoomed so that type is the same
apparent size as it would be on a 1080p take at PAGE_ZOOM 1.35, which is
to say a third larger than the site at a desk. Every overlay drawn on the
page derives from SCALE so the cursor, the address bar and the lock icon
are not four times too small.

The take is not upscaled 1080p. It is rendered at 2160 lines by the
browser, so text is sharp at 4K and stays sharp when YouTube serves it
at 1080p to most people.

Sync
----
Beat actions point the cursor at things. A pointer that arrives while
the words are still describing something else is worse than no pointer,
so moves are scheduled against the sentence that mentions them rather
than a guessed offset. `on_phrase` waits for that sentence.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from beats import BEATS, phrase_offset

HERE = Path(__file__).parent
OUT = HERE / "build"
SITE = os.environ.get("VOLLEY_SITE", "https://da78ygi6ol1oi.cloudfront.net")
SITE_HOST = SITE.split("://", 1)[-1]

# The frame. Must equal the viewport.
WIDTH, HEIGHT = 3840, 2160
SCALE = 2

# The site, enlarged for a video rather than a desk. 1.35 at 1080p was a
# third larger than the desk; doubling the frame doubles it again so the
# apparent size on screen is unchanged.
PAGE_ZOOM = 1.35 * SCALE
URL_BAR_HEIGHT = 56 * SCALE
REST_Y = URL_BAR_HEIGHT + 150 * SCALE

ZOOM_JS = f"document.documentElement.style.zoom = '{PAGE_ZOOM}';"

# The site's own smooth scrolling fights the recorder's scroll_to, so it
# is turned off for the take. Nothing a viewer sees depends on it.
NATIVE_SCROLL_OFF_JS = (
    "var s=document.createElement('style');"
    "s.textContent='html{scroll-behavior:auto !important}';"
    "document.head.appendChild(s);"
)

# A visible cursor, because a headless browser draws none and a demo with
# no pointer reads as a screensaver.
#
# The root is zoomed, so every CSS pixel of this ring, including its
# left and top, is multiplied by PAGE_ZOOM when drawn, while the mouse
# reports plain viewport pixels. Take 4 was recorded with the ring set
# straight from clientX: it sat at 2.7 times the pointer, off the frame
# on every beat but one, and on that one it was a blue circle in the
# margin. Sizes below are in zoomed pixels for the same reason.
CURSOR_JS = f"""
var Z={PAGE_ZOOM};
var c=document.createElement('div');
c.id='__cursor';
c.style.cssText=['position:fixed','z-index:2147483647','pointer-events:none',
  'width:24px','height:24px','border-radius:50%',
  'border:2px solid #1f4fd8','background:rgba(31,79,216,0.18)',
  'box-shadow:0 0 0 1px rgba(255,255,255,0.9)',
  'left:-100px','top:-100px',
  'transform:translate(-50%,-50%)','transition:transform 80ms,opacity 300ms'].join(';');
document.body.appendChild(c);
document.addEventListener('mousemove',function(e){{c.style.left=(e.clientX/Z)+'px';c.style.top=(e.clientY/Z)+'px';}});
document.addEventListener('mousedown',function(){{c.style.transform='translate(-50%,-50%) scale(0.75)';}});
document.addEventListener('mouseup',function(){{c.style.transform='translate(-50%,-50%) scale(1)';}});
"""

# A faux address bar, so the frame reads as a real site at a real URL
# rather than a screenshot of a page with no context.
URL_BAR_JS = f"""
var H={URL_BAR_HEIGHT};
document.documentElement.style.setProperty('--__bar', H+'px');
var b=document.createElement('div');
b.style.cssText=['position:fixed','top:0','left:0','right:0','height:'+H+'px',
  'z-index:2147483646','background:#f3f1ec','border-bottom:1px solid #d9d3c7',
  'display:flex','align-items:center','padding:0 {18*SCALE}px','gap:{10*SCALE}px',
  'font:{14*SCALE}px/1 Inter,system-ui,sans-serif','color:#1c1a17'].join(';');
var lock=document.createElement('span');
lock.textContent='\\u{{1F512}}';
lock.style.cssText='font-size:{14*SCALE}px;line-height:1;opacity:0.85';
var url=document.createElement('span');
url.textContent='{SITE_HOST}';
url.style.cssText=['background:#fff','border:1px solid #d9d3c7','border-radius:{10*SCALE}px',
  'padding:{8*SCALE}px {14*SCALE}px','flex:1','max-width:{560*SCALE}px'].join(';');
b.appendChild(lock);b.appendChild(url);
document.body.appendChild(b);
document.body.style.paddingTop=H+'px';
"""


# The clapperboard. Playwright's picture starts some fraction of a second
# before the recorder's clock does, and the fraction is not knowable from
# the clock: measured with a flashing square it was a constant 1.82s
# across a take, with no drift, and a different day gives a different
# constant. Before that was measured, every cut began about two seconds
# before its own scroll had finished, and the last beat of take six was a
# blank page. So the take claps: a black square in the corner for a
# moment before the first beat, found again in the finished file, and
# every mark shifted by the difference.
CLAP_MS = 400
CLAP_JS = (
    "var k=document.createElement('div');k.id='__clap';"
    "k.style.cssText='position:fixed;left:0;top:0;width:160px;height:160px;"
    "z-index:2147483647;background:#000';document.body.appendChild(k);"
)


def find_clap(path: Path) -> float:
    """The second at which the corner first goes black in the file."""
    rate = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True).stdout.strip()
    num, den = (int(x) for x in rate.split("/"))
    fps = num / den
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-t", "12", "-i", str(path),
         "-vf", "crop=200:200:0:0,scale=1:1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        check=True, capture_output=True).stdout
    for k, level in enumerate(raw):
        if level < 60:
            return k / fps
    raise SystemExit("no clapperboard in the first twelve seconds of the take; the marks cannot be aligned")


def run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"{args[0]} failed:\n{proc.stderr[-1200:]}")


class Recorder:
    """The browser, plus the clock every beat is timed against."""

    def __init__(self, page: Page, start: float, narration: dict[str, float]):
        self.page = page
        self.start = start
        self.narration = narration
        self.marks: list[dict] = []
        self.current: str | None = None

    def mark(self, beat) -> None:
        at = time.monotonic() - self.start
        self.current = beat.key
        self.marks.append({"key": beat.key, "at": round(at, 3)})
        print(f"  {at:6.1f}s  {beat.key:10} {beat.action}")

    def spoken(self, key: str) -> float:
        beat = next(b for b in BEATS if b.key == key)
        return self.narration.get(key, beat.speak_seconds)

    def budget(self, key: str) -> float:
        beat = next(b for b in BEATS if b.key == key)
        return max(beat.pause_before + self.spoken(key), beat.min_hold)

    def hold_beat(self) -> None:
        assert self.current is not None
        began = next(m["at"] for m in self.marks if m["key"] == self.current)
        remaining = began + self.budget(self.current) - (time.monotonic() - self.start)
        if remaining > 0:
            self.page.wait_for_timeout(remaining * 1000)

    def on_phrase(self, text: str) -> None:
        assert self.current is not None
        key = self.current
        line = next(b.say for b in BEATS if b.key == key)
        try:
            offset = phrase_offset(line, self.spoken(key), text)
        except ValueError:
            raise SystemExit(
                f"beat {key!r} has no sentence containing {text!r}; "
                "the narration changed and this action did not"
            ) from None
        began = next(m["at"] for m in self.marks if m["key"] == key)
        target = began + next(b.pause_before for b in BEATS if b.key == key) + offset
        remaining = target - (time.monotonic() - self.start)
        if remaining > 0:
            self.page.wait_for_timeout(remaining * 1000)

    def park(self) -> None:
        """Rest the pointer in the right margin, off every word.

        A fixed ring keeps its place on the screen while the page moves
        under it, so without this the pointer sat on whatever the
        previous beat had put there: a stat tile's sentence, the address
        bar, a card it had no business on. Each gesture now starts from
        the same empty place.
        """
        self.page.mouse.move(WIDTH - 100 * SCALE, HEIGHT * 0.55, steps=12)

    def scroll_to(self, selector: str, rest: int = REST_Y) -> None:
        page = self.page
        page.wait_for_selector(selector, timeout=30_000)
        for _ in range(8):
            box = page.locator(selector).first.bounding_box()
            if box is None:
                raise SystemExit(f"{selector!r} is not on the page")
            delta = box["y"] - rest
            if abs(delta) < 12 * SCALE:
                break
            page.mouse.wheel(0, delta)
            page.wait_for_timeout(240)
        self.park()

    def point(self, selector: str, dx: int = 0, dy: int = 0) -> None:
        box = self.page.locator(selector).first.bounding_box()
        if box is None:
            raise SystemExit(f"cannot point at {selector!r}: not on the page")
        self.page.mouse.move(box["x"] + box["width"] / 2 + dx, box["y"] + box["height"] / 2 + dy, steps=22)
        self.page.wait_for_timeout(120)

    def click(self, selector: str) -> None:
        self.point(selector)
        self.page.mouse.down()
        self.page.wait_for_timeout(90)
        self.page.mouse.up()


# --------------------------------------------------------------------------
# Beat actions. Each yields once when the shot is composed; the driver marks
# the beat at that yield so narration starts against a settled screen.
# --------------------------------------------------------------------------

HERO = "h1"
HOW = "#how"
PLAY = "#how button:has-text('Play')"
DAY = "#day"
PLAN = "#day section:has(h3:has-text('plan'))"
EVIDENCE = "#evidence"
ALEXA = "#alexa"
ASK = "#alexa button:has-text('How was our talking today?')"
SITE_EVIDENCE = SITE.rstrip("/") + "/evidence/"
SITE_COACH = SITE.rstrip("/") + "/coach/"
AGENTS = "#agents"
COACH_LIST = "ul[aria-label]"
YOURS = "#yours"

# The black card the video opens on: the words, then the site under them.
HOOK_JS = """
(() => {
  const k = document.createElement('div'); k.id = '__hook';
  k.style.cssText = 'position:fixed;inset:0;z-index:2147483646;background:#12151b;display:flex;align-items:center;justify-content:center;' +
    'color:#f3f1ec;font:600 %dpx/1.1 Fraunces, Georgia, serif;letter-spacing:-0.02em;transition:opacity 700ms ease;text-align:center;padding:0 6%%';
  k.textContent = 'Steps. Sleep. Heartbeats.';
  document.body.appendChild(k);
})();
""" % (150,)


def hook(r: Recorder):
    r.page.evaluate(HOOK_JS)
    r.page.evaluate("document.getElementById('__cursor').style.opacity='0'")
    yield
    r.on_phrase("But what about")
    r.page.evaluate("document.getElementById('__hook').style.opacity='0'")
    r.page.wait_for_timeout(750)
    r.page.evaluate("document.getElementById('__hook').remove(); document.getElementById('__cursor').style.opacity='1'")
    r.park()
    r.on_phrase("Meet Volley")
    r.point(HERO, dy=-30 * SCALE)
    r.on_phrase("On the Bee you already wear")
    r.point("#top p.leading-relaxed.text-ink", dy=-20 * SCALE)
    r.on_phrase("The numbers, never the words")
    r.point("#top .card .display", dy=0)
    r.hold_beat()


def how(r: Recorder):
    r.scroll_to(HOW, rest=URL_BAR_HEIGHT + 120 * SCALE)
    yield
    r.on_phrase("Here is how")
    r.click(PLAY)
    r.on_phrase("reads who is talking")
    r.point("#how .display", dy=0)
    r.hold_beat()


def plan(r: Recorder):
    r.scroll_to(DAY, rest=URL_BAR_HEIGHT + 120 * SCALE)
    yield
    r.on_phrase("Over a week")
    r.point("#day ul li:nth-child(2)")
    r.on_phrase("Claude on Amazon Bedrock")
    r.scroll_to(PLAN, rest=URL_BAR_HEIGHT + 140 * SCALE)
    r.point(f"{PLAN} h3")
    r.on_phrase("keep the hour that works")
    r.point(f"{PLAN} li:nth-child(1)")
    r.on_phrase("one idea for the quiet one")
    r.point(f"{PLAN} li:nth-child(2)")
    r.on_phrase("one for the weekend")
    r.point(f"{PLAN} li:nth-child(3)")
    r.on_phrase("A gate in code")
    r.point(f"{PLAN} p:has-text('number gate')", dy=0)
    r.hold_beat()


STATS = [
    ("26.59 h", "of independent family recordings, 54 sessions"),
    ("20,344", "reference turns from the human speaker labels; without labels, a typical session lands within 9.6 percent"),
    ("66 of 75", "turns found on the physical Bee from a replayed research conversation"),
]
STATS_JS = """
(() => {
  const k = document.createElement('div'); k.id = '__stats';
  k.style.cssText = 'position:fixed;inset:0;z-index:2147483646;background:#12151b;color:#f3f1ec;display:grid;' +
    'align-content:center;gap:%dpx;padding:0 %dpx 80px;opacity:0;transition:opacity 500ms ease';
  k.innerHTML = %s.map(([n, l], i) =>
    '<div class="__stat" style="opacity:0;transform:translateY(12px);transition:opacity 500ms ease,transform 500ms ease;' +
    'display:grid;grid-template-columns:%dpx 1fr;align-items:baseline;gap:%dpx;border-top:1px solid #2a303b;padding-top:%dpx">' +
    '<div style="font:600 %dpx/1 Fraunces, Georgia, serif;letter-spacing:-0.02em;font-variant-numeric:tabular-nums">' + n + '</div>' +
    '<div style="font:400 %dpx/1.3 Inter, system-ui, sans-serif;color:#aeb3bd;max-width:28ch">' + l + '</div></div>').join('');
  document.body.appendChild(k);
  requestAnimationFrame(() => { k.style.opacity = '1'; });
  window.__stat = i => { const el = document.querySelectorAll('.__stat')[i]; el.style.opacity = '1'; el.style.transform = 'none'; };
})();
""" % (24, 160, json.dumps(STATS), 560, 48, 24, 112, 32)


CAP_JS = """
(() => {
  let k = document.getElementById('__cap');
  if (!k) {
    k = document.createElement('div'); k.id = '__cap';
    k.style.cssText = 'position:fixed;left:40px;right:40px;bottom:40px;z-index:2147483645;padding:18px 24px;background:#191d25;' +
      'border:1px solid #2a303b;border-radius:12px;font-family:Inter,system-ui,sans-serif;box-shadow:0 20px 60px rgba(0,0,0,.35);transition:opacity 300ms ease';
    k.innerHTML = '<b style="display:block;font:600 30px/1.1 Inter,system-ui,sans-serif;letter-spacing:0.04em;color:#f3f1ec;white-space:nowrap;overflow:hidden"></b>' +
      '<i style="display:block;font-style:normal;font:400 16px/1.3 Inter,system-ui,sans-serif;color:#aeb3bd;margin-top:6px"></i>';
    document.body.appendChild(k);
  }
  return k;
})();
"""


def proof(r: Recorder):
    r.scroll_to(EVIDENCE, rest=URL_BAR_HEIGHT + 100 * SCALE)
    r.page.evaluate("document.getElementById('__cursor').style.opacity='0'")
    r.page.evaluate(STATS_JS)
    yield
    r.on_phrase("Twenty-six hours")
    r.page.evaluate("window.__stat(0)")
    r.on_phrase("Twenty thousand reference turns")
    r.page.evaluate("window.__stat(1)")
    r.on_phrase("On the physical Bee")
    r.page.evaluate("window.__stat(2)")
    r.on_phrase("child-present check")
    r.page.evaluate("document.getElementById('__stats').style.opacity='0'")
    r.page.wait_for_timeout(550)
    r.page.evaluate("document.getElementById('__stats').remove(); document.getElementById('__cursor').style.opacity='1'")
    r.scroll_to("#evidence li.ev-row:nth-of-type(5)", rest=URL_BAR_HEIGHT + 200 * SCALE)
    r.point("#evidence li.ev-row:nth-of-type(5)")
    r.hold_beat()


ALEXA_SUB = "A browser stand-in for Alexa+'s voice; the MCP call to Volley's server is the real one, on the simulated family"


def alexa(r: Recorder):
    r.scroll_to(ALEXA, rest=URL_BAR_HEIGHT + 120 * SCALE)
    shown: list[str] = []

    def cap(text: str) -> None:
        shown.append(text)
        r.page.evaluate(CAP_JS)
        r.page.evaluate("([t, s]) => { const k = document.getElementById('__cap'); k.querySelector('b').innerHTML = t; k.querySelector('i').textContent = s; }",
                        ['<span style="color:#7aa2ff;margin:0 .35em">&rarr;</span>'.join(shown), ALEXA_SUB])

    yield
    r.on_phrase("Parents can ask out loud")
    r.scroll_to(ASK, rest=URL_BAR_HEIGHT + 520 * SCALE)
    r.on_phrase("the question")
    r.click(ASK)
    cap("QUESTION")
    r.page.wait_for_selector("#alexa dd:has-text('On the simulated family')", timeout=30_000)
    # The result block, enlarged, so the tool call line is read and not inferred.
    r.page.evaluate("const d = document.querySelector('#alexa dl.voice-result'); d.style.transition = 'transform 400ms ease'; d.style.transformOrigin = '0 0'; d.style.transform = 'scale(1.08)';")
    r.on_phrase("the tool")
    # The tool call line itself, enlarged in place: the one line that proves the call.
    r.page.evaluate("const d = [...document.querySelectorAll('#alexa dd')].find(e => e.textContent.includes('tools/call')); d.style.transition = 'transform 400ms ease'; d.style.transformOrigin = '0 50%'; d.style.transform = 'scale(1.45)'; d.style.background = '#fff7cc'; d.style.padding = '2px 6px'; d.style.borderRadius = '6px';")
    r.point("#alexa dd:has-text('tools/call')")
    cap("MCP TOOL CALLED")
    r.on_phrase("the counts back")
    # The tool line stays enlarged; the answer joins it, a little larger too.
    r.page.evaluate("const a = [...document.querySelectorAll('#alexa dd')].find(e => e.textContent.includes('On the simulated family')); a.style.transition = 'transform 400ms ease'; a.style.transformOrigin = '0 50%'; a.style.transform = 'scale(1.08)';")
    r.point("#alexa dd:has-text('On the simulated family')")
    cap("COUNTS BACK")
    r.on_phrase("the answer spoken")
    cap("SPOKEN")
    r.on_phrase("Two Strands agents")
    r.page.evaluate("document.getElementById('__cap').remove()")
    r.page.goto(SITE_EVIDENCE, wait_until="networkidle", timeout=90_000)
    r.page.wait_for_selector(AGENTS, timeout=60_000)
    r.scroll_to(AGENTS, rest=URL_BAR_HEIGHT + 120 * SCALE)
    r.point("#agents p:has-text('Simulated Bee')")
    r.on_phrase("one hosted on AgentCore")
    r.point("#agents blockquote:has-text('quietest')")
    r.hold_beat()


def beyond(r: Recorder):
    r.page.goto(SITE_COACH, wait_until="networkidle", timeout=90_000)
    r.page.wait_for_selector(COACH_LIST, timeout=60_000)
    r.page.wait_for_timeout(800)
    yield
    r.on_phrase("For families with a home visitor")
    r.point(f"{COACH_LIST} li:first-child", dy=-10 * SCALE)
    r.on_phrase("Open source on PyPI")
    r.page.goto(SITE, wait_until="networkidle", timeout=90_000)
    r.page.wait_for_selector(YOURS, timeout=60_000)
    r.scroll_to(YOURS, rest=URL_BAR_HEIGHT + 120 * SCALE)
    r.point("#yours li:first-child pre")
    r.hold_beat()


CLOSE_JS = """
(() => {
  const k = document.createElement('div'); k.id = '__close';
  k.style.cssText = 'position:fixed;inset:0;z-index:2147483646;background:#12151b;color:#f3f1ec;display:flex;flex-direction:column;' +
    'align-items:center;justify-content:center;text-align:center;padding:0 8%%;opacity:0;transition:opacity 900ms ease';
  k.innerHTML = '<div style="font:600 %dpx/1 Fraunces, Georgia, serif;letter-spacing:-0.02em">Volley</div>' +
    '<div style="font:400 %dpx/1.3 Fraunces, Georgia, serif;margin-top:%dpx;max-width:24ch">A step counter for conversations with your child.</div>' +
    '<div style="font:400 %dpx/1.4 Inter, system-ui, sans-serif;color:#aeb3bd;margin-top:%dpx;max-width:44ch">Because what matters is not how many words we say. It is the conversations we share.</div>' +
    '<div style="font:500 %dpx/1.3 Inter, system-ui, sans-serif;color:#7c828d;margin-top:%dpx;letter-spacing:0.08em;text-transform:uppercase">Built on Bee and AWS</div>';
  document.body.appendChild(k);
  requestAnimationFrame(() => { k.style.opacity = '1'; });
})();
""" % (160, 52, 36, 24, 48, 18, 40)


def close(r: Recorder):
    r.page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    r.page.wait_for_timeout(300)
    r.page.evaluate("document.getElementById('__cursor').style.opacity='0'")
    yield
    r.on_phrase("Because what matters")
    r.page.evaluate(CLOSE_JS)
    r.hold_beat()


ACTIONS = {f.__name__: f for f in (hook, how, plan, proof, alexa, beyond, close)}


def assert_full_frame(path: Path) -> None:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    w, h = (int(x) for x in out.split(",")[:2])
    if (w, h) != (WIDTH, HEIGHT):
        raise SystemExit(f"recorded {w}x{h} but the frame is {WIDTH}x{HEIGHT}; Playwright padded rather than filled")


def main() -> int:
    manifest = OUT / "narration.json"
    if not manifest.exists():
        raise SystemExit("no narration.json: run narrate.py first")
    narration = {n["key"]: n["seconds"] for n in json.loads(manifest.read_text(encoding="utf8"))}

    web = [b for b in BEATS if not b.is_tv]
    video_dir = OUT / "raw"
    video_dir.mkdir(parents=True, exist_ok=True)
    for stale in video_dir.glob("*.webm"):
        stale.unlink()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=["--force-color-profile=srgb", "--autoplay-policy=no-user-gesture-required"])
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
            color_scheme="light",
            record_video_dir=str(video_dir),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()
        page.add_init_script(
            "document.addEventListener('DOMContentLoaded', () => {" + ZOOM_JS + NATIVE_SCROLL_OFF_JS + CURSOR_JS + URL_BAR_JS + "});"
        )
        print(f"{WIDTH}x{HEIGHT} against {SITE}")
        page.goto(SITE, wait_until="networkidle", timeout=90_000)
        page.wait_for_selector(HERO, timeout=60_000)
        page.wait_for_timeout(1200)
        page.evaluate(CLAP_JS)
        clap_at = time.monotonic()
        page.wait_for_timeout(CLAP_MS)
        page.evaluate("document.getElementById('__clap').remove()")
        page.wait_for_timeout(400)
        r = Recorder(page, time.monotonic(), narration)
        clap_clock = clap_at - r.start  # before the clock began, so negative
        r.park()
        for beat in web:
            steps = ACTIONS[beat.action](r)
            next(steps, None)
            r.mark(beat)
            for _ in steps:
                pass

        total = time.monotonic() - r.start
        video = page.video
        context.close()
        src = Path(video.path())
        browser.close()

    dest = OUT / "web.mp4"
    run(["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-tune", "stillimage", "-pix_fmt", "yuv420p", "-an", str(dest)])
    assert_full_frame(dest)

    # Marks were taken on the clock; the file runs on its own time. The
    # clap is the one event seen by both.
    offset = find_clap(dest) - clap_clock
    # The offset is the first page's load before the clap; a slow CloudFront
    # morning has reached seven seconds. Beyond twelve the clap was misread.
    if not 0.0 <= offset <= 12.0:
        raise SystemExit(f"the picture is offset {offset:.2f}s from the clock, which is not credible")
    for m in r.marks:
        m["at"] = round(m["at"] + offset, 3)
    length = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dest)],
        check=True, capture_output=True, text=True).stdout.strip())

    (OUT / "web-timings.json").write_text(
        json.dumps({"video": round(length, 3), "width": WIDTH, "height": HEIGHT,
                    "clockOffset": round(offset, 3), "beats": r.marks}, indent=1),
        encoding="utf8",
    )
    print(f"\nwrote {dest.name} and web-timings.json")
    print(f"{len(r.marks)} web beats over {total:.1f}s; picture runs {offset:.2f}s ahead of the clock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
