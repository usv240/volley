"""The terminal camera: real commands, real output, rendered.

    python record_term.py capture      # run the commands for real, keep their output
    python record_term.py render       # type them out in a terminal frame and record it

Two steps on purpose. `capture` runs each command against the operator's
own Bee and saves exactly what came back, with the time it took. It can
only be run where the Bee is signed in, and it refuses to run if the
household is not set up, because the point is a real day. `render` opens
a terminal-styled page in the same 4K browser recorder the web beats
use, types each command at a human pace, prints its saved output, and
writes `build/tv.mp4` and `build/tv-timings.json`, the same contract the
assembler already reads for its second camera. The frame carries the
words "a real run, rendered" so nobody mistakes the typing for a live
session. Nothing is invented and nothing is sped up: the output is the
output, and the pauses are the pauses.

Why not screen-record a real terminal: a Windows console is a GDI window
at whatever size and font it has, and a capture of it in a 4K frame is
either tiny or blurry. A rendering of the same bytes at the right size
is more honest to the viewer's eye, and the capture step is what keeps
it honest to the facts.
"""

from __future__ import annotations

import html
import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from beats import BEATS, phrase_offset
from record import CLAP_MS, HEIGHT, WIDTH, find_clap

HERE = Path(__file__).parent
OUT = HERE / "build"
CAPTURE = OUT / "term-capture.json"

# The beats and the commands each shows. Output is captured once and
# rendered as many times as the cut needs.
# The session is the real one played to the band on 2026-10-19 (BEE_DAY.md).
# The reminder marker for that day is cleared first so the command writes
# the reminder again on camera, as it did the first time.
SHOTS = {
    "term-count": [
        ["volley", "today", "--conversation", "11418600"],
    ],
    "term-reminder": [
        ["bee", "todos", "list", "--limit", "2"],
    ],
    # The afternoon run. Captured separately with `capture --only term-nudge`
    # while the family's usual hour is on; it watches for up to forty minutes.
    "term-nudge": [
        ["volley", "live", "--nudge", "--say", "--seconds", "2400", "--record", "harness/live/nudge-2026-10-22.json"],
    ],
}


def _clear_reminder_marker() -> None:
    from volley_ingest.household import home

    marker = home() / "reminders" / "2026-10-19.written"
    if marker.exists():
        marker.unlink()


def capture() -> int:
    from volley_ingest.household import Household

    h = Household.load()
    if h is None or not h.ready:
        print("no household: run volley setup first, and only capture a real day", file=sys.stderr)
        return 2
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    OUT.mkdir(parents=True, exist_ok=True)
    record: dict = {"captured": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "shots": {}}
    if CAPTURE.exists():
        # Keep the shots not being retaken: the nudge is captured on its own afternoon.
        record["shots"] = json.loads(CAPTURE.read_text(encoding="utf8")).get("shots", {})
    for key, commands in SHOTS.items():
        if only and key != only:
            continue
        if not only and key == "term-nudge":
            continue
        if key == "term-count":
            _clear_reminder_marker()
        record["shots"][key] = []
        for argv in commands:
            t0 = time.perf_counter()
            # `volley` is the venv's console script; run it through this Python
            # so the capture works wherever the venv is, while the typed line
            # on screen stays the command a parent types.
            real = [sys.executable, "-m", "volley_ingest.cli", *argv[1:]] if argv[0] == "volley" else ["cmd", "/c", *argv]
            proc = subprocess.run(real, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3000, cwd=str(HERE.parent))
            out = (proc.stdout + proc.stderr).rstrip()
            # The parent's page link carries the household key in its fragment; never on camera.
            out = "\n".join((l.split("#")[0] + "#[your key]") if "/mine/#" in l else l for l in out.splitlines())
            record["shots"][key].append({"argv": argv, "output": out, "seconds": round(time.perf_counter() - t0, 2), "code": proc.returncode})
            print(f"  {' '.join(argv)}: {proc.returncode}, {len(out.splitlines())} lines")
    CAPTURE.write_text(json.dumps(record, indent=1), encoding="utf8")
    print(f"wrote {CAPTURE}")
    return 0


PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#12151b;color:#e8e6e1;font:{fs}px/1.5 'Cascadia Mono','Consolas',monospace;height:100%}}
.frame{{position:absolute;inset:{pad}px;background:#191d25;border:1px solid #2a303b;border-radius:{r}px;box-shadow:0 20px 60px rgba(0,0,0,.4);overflow:hidden}}
.cap{{position:absolute;left:{pad}px;right:{pad}px;bottom:{pad}px;padding:{pad2}px {pad2}px;background:#191d25;border:1px solid #2a303b;border-top:0;border-radius:0 0 {r}px {r}px;font-family:Inter,system-ui,sans-serif}}
.cap b{{display:block;font:600 {fs3}px/1.1 Inter,system-ui,sans-serif;letter-spacing:0.04em;color:#f3f1ec;min-height:{fs3}px;white-space:nowrap;overflow:hidden}}
.cap b .arrow{{color:#7aa2ff;margin:0 .35em}}
.cap i{{display:block;font-style:normal;font:400 {fs2}px/1.3 Inter,system-ui,sans-serif;color:#aeb3bd;margin-top:{pad3}px}}
.callout{{position:absolute;left:{pad2}px;right:{pad2}px;top:{callout_top}px;padding:{pad2}px;background:#f3f1ec;color:#12151b;border-radius:{r}px;font:500 {fs4}px/1.25 Fraunces,Georgia,serif;letter-spacing:-0.01em;opacity:0;transform:translateY(10px);transition:opacity 500ms ease,transform 500ms ease}}
.callout small{{display:block;font:500 {fs2}px/1.3 Inter,system-ui,sans-serif;color:#5b6170;margin-top:{pad3}px;letter-spacing:0.06em;text-transform:uppercase}}
.hl{{color:#f3f1ec;font-weight:700}}
.bar{{height:{bar}px;background:#222732;border-bottom:1px solid #2a303b;display:flex;align-items:center;padding:0 {pad2}px;color:#aeb3bd;font-size:{fs2}px}}
.bar span{{margin-left:auto;color:#7c828d}}
pre{{position:absolute;left:0;right:0;top:{bar}px;bottom:{cap_h}px;margin:0;padding:{pad2}px;white-space:pre-wrap;word-break:break-word;overflow:hidden}}
.p{{color:#7aa2ff}}.k{{color:#f3f1ec}}.d{{color:#aeb3bd}}
</style></head><body><div class="frame"><div class="bar"><b id="lbl">volley, on the builder's own Bee</b><span>a real run, rendered</span></div><pre id="t"></pre><div class="callout" id="co"></div></div><div class="cap"><b id="cap"></b><i id="sub"></i></div></body></html>"""


def render() -> int:
    if not CAPTURE.exists():
        print("no capture: run record_term.py capture on the machine with the Bee", file=sys.stderr)
        return 2
    rec = json.loads(CAPTURE.read_text(encoding="utf8"))
    narration = {n["key"]: n["seconds"] for n in json.loads((OUT / "narration.json").read_text(encoding="utf8"))}
    scale = WIDTH / 1920
    page_html = PAGE.format(fs=int(32 * scale), fs2=int(20 * scale), fs3=int(40 * scale), fs4=int(40 * scale), pad=int(56 * scale), pad2=int(28 * scale),
                            pad3=int(8 * scale), r=int(16 * scale), bar=int(56 * scale), callout_top=int(520 * scale), cap_h=int(132 * scale))
    (OUT / "term.html").write_text(page_html, encoding="utf8")
    raw_dir = OUT / "raw-term"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for stale in raw_dir.glob("*.webm"):
        stale.unlink()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1,
                                  record_video_dir=str(raw_dir), record_video_size={"width": WIDTH, "height": HEIGHT})
        page = ctx.new_page()
        page.goto((OUT / "term.html").as_uri())
        page.wait_for_timeout(800)
        page.evaluate("var k=document.createElement('div');k.id='__clap';k.style.cssText='position:fixed;left:0;top:0;width:160px;height:160px;z-index:9;background:#000';document.body.appendChild(k)")
        clap_at = time.monotonic()
        page.wait_for_timeout(CLAP_MS)
        page.evaluate("document.getElementById('__clap').remove()")
        page.wait_for_timeout(400)
        start = time.monotonic()
        clap_clock = clap_at - start
        marks: list[dict] = []

        def append(text: str, cls: str) -> None:
            page.evaluate("([t, c]) => { const el = document.getElementById('t'); const s = document.createElement('span'); s.className = c; s.textContent = t; el.appendChild(s); el.scrollTop = el.scrollHeight; }", [text, cls])

        def type_out(text: str) -> None:
            for ch in text:
                append(ch, "k")
                page.wait_for_timeout(45)

        # What each terminal beat is, said in the frame's own bar so the
        # viewer never mistakes a replay or a stand-in for something else.
        LABELS = {
            "term-count": "REAL BEE, A REPLAYED RESEARCH CONVERSATION",
            "term-reminder": "REAL BEE, THE REMINDER IT PLACED",
            "term-nudge": "LIVE BEE STREAM, A SPEAKER STANDING IN FOR AN ECHO",
        }
        # The three-word story under each terminal beat, one caption per
        # narrated phrase, and the source named plainly beneath it.
        CAPTIONS = {
            "term-count": [("One command", "REAL BEE DATA"), ("sixty-six", "66 TURNS DETECTED"), ("places one thing", "REMINDER CREATED")],
            "term-reminder": [("There it is", "IN THE BEE, DUE AT 3PM")],
            "term-nudge": [("watches", "LIVE BEE STREAM"), ("goes quiet", "QUIET HOUR"), ("reaches the Bee", "NUDGE PLACED IN THE BEE")],
        }
        SUBTITLES = {
            "term-count": "A research conversation replayed through a physical Bee; every word deleted on this computer",
            "term-reminder": "The reminder the command placed, read back from the Bee",
            "term-nudge": "This computer's speaker stands in for an Echo; the sentence goes into the Bee as a reminder",
        }
        HIGHLIGHT = ("turns with your child", "placed in your Bee", "0 kept", "alarm_at", "nudge at ", "placed in your Bee, due", "- text:")
        for beat in [b for b in BEATS if b.is_terminal]:
            shots = rec["shots"].get(beat.key, [])
            if not shots:
                print(f"  no capture for {beat.key}; the assembler will drop it")
                continue
            page.evaluate("t => { document.getElementById('lbl').textContent = t; }", LABELS.get(beat.key, "volley, on the builder's own Bee"))
            page.evaluate("t => { document.getElementById('sub').textContent = t; document.getElementById('cap').textContent = ''; "
                          "const c = document.getElementById('co'); c.style.opacity = '0'; c.innerHTML = ''; }", SUBTITLES.get(beat.key, ""))
            spoken = narration.get(beat.key, beat.speak_seconds)
            cues = []
            shown: list[str] = []
            for phrase, text in CAPTIONS.get(beat.key, []):
                shown.append(text)
                html_text = '<span class="arrow">&rarr;</span>'.join(html.escape(t) for t in shown)
                cues.append([int((beat.pause_before + phrase_offset(beat.say, spoken, phrase)) * 1000), html_text])
            page.evaluate("cues => { for (const [ms, t] of cues) setTimeout(() => { document.getElementById('cap').innerHTML = t; }, ms); }", cues)
            marks.append({"key": beat.key, "at": round(time.monotonic() - start, 3)})
            budget = max(beat.pause_before + narration.get(beat.key, beat.speak_seconds), beat.min_hold)
            deadline = time.monotonic() + budget
            for shot in shots:
                append("$ ", "p")
                type_out(" ".join(shot["argv"]))
                append("\n", "k")
                page.wait_for_timeout(int(min(1.5, shot["seconds"]) * 1000))
                for line in shot["output"].splitlines():
                    append(line + "\n", "hl" if any(k in line for k in HIGHLIGHT) else "d")
                    if line.strip().startswith("nudge at "):
                        said = line.split(":", 2)[-1].strip()
                        page.evaluate("t => { const c = document.getElementById('co'); c.innerHTML = t + '<small>said aloud in the room, and placed in the Bee</small>'; c.style.opacity = '1'; c.style.transform = 'none'; }", said)
                    page.wait_for_timeout(70)
                page.wait_for_timeout(600)
            remaining = deadline - time.monotonic()
            if remaining > 0:
                page.wait_for_timeout(int(remaining * 1000))
            page.evaluate("document.getElementById('t').textContent=''")
            page.wait_for_timeout(300)
        page.wait_for_timeout(1000)
        total = time.monotonic() - start
        video = page.video
        ctx.close()
        src = Path(video.path())
        browser.close()

    dest = OUT / "tv.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-r", "25", "-fps_mode", "cfr", "-c:v", "libx264", "-crf", "18",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-an", str(dest)], check=True)
    offset = find_clap(dest) - clap_clock
    for m in marks:
        m["at"] = round(m["at"] + offset, 3)
    length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dest)],
                                  check=True, capture_output=True, text=True).stdout.strip())
    (OUT / "tv-timings.json").write_text(json.dumps({"video": round(length, 3), "width": WIDTH, "height": HEIGHT,
                                                      "device": "a terminal, a real run rendered", "captured": rec["captured"],
                                                      "clockOffset": round(offset, 3), "beats": marks}, indent=1), encoding="utf8")
    print(f"wrote {dest.name} and tv-timings.json: {len(marks)} beats over {total:.1f}s")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("capture", "render"):
        print(__doc__)
        return 2
    return capture() if sys.argv[1] == "capture" else render()


if __name__ == "__main__":
    raise SystemExit(main())
