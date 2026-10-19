"""The demo video as data, not prose.

One record per beat: the pause before it, what the recorder should do,
what is on screen, and the exact line Polly will say. Nothing else in
the pipeline may invent a timecode; every downstream step derives its
timing from here, and after recording, from where each beat actually
landed.

The human-readable script is docs/VIDEO_SCRIPT.md, and it is written by
this file: `python beats.py --script` regenerates it, and a test fails
if the two ever disagree.

Two cameras
-----------
Most beats are the deployed website driven by a real browser at 4K. Two
beats are a terminal: real commands run against the operator's own Bee,
their real output rendered in a terminal frame the same recorder
captures. `action` starting with `term_` means terminal footage, and the
script says on screen that it is a rendering of a real run. Those two
beats need the operator's own day, which needs the device's speaker
labels (Gate 1 in docs/planning/PLAN.md), so the assembler tolerates their
absence: the web take is cut on its own, and the terminal beats are
added when the day exists.

The hard constraint
-------------------
Three minutes, and judges are not required to watch past it. `python
beats.py` prints the estimate and exits non-zero if the plan is over.

What the order is for
---------------------
A judge who watches only the first fifteen seconds should leave with
one sentence: your child's brain is built in the back-and-forth, and a
parent has never been able to count it. Everything after is evidence in
the order a sceptic asks for it: the rule counting, the operator's own
day, what it refused to count, the transcript refused, the assistant,
the honesty, the line.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Polly's Joanna at the rate narrate.py asks for, measured on the sibling
# project's script: 152 words a minute. A gate before recording only.
WORDS_PER_MINUTE = 152
CEILING_SECONDS = 180


@dataclass
class Beat:
    key: str
    say: str
    action: str
    shows: str = ""
    pause_before: float = 0.0
    min_hold: float = 0.0

    @property
    def is_terminal(self) -> bool:
        return self.action.startswith("term_")

    # The assembler and recorder were written for a "tv" second camera;
    # the terminal is that camera here.
    @property
    def is_tv(self) -> bool:
        return self.is_terminal

    @property
    def speak_seconds(self) -> float:
        return len(self.say.split()) / WORDS_PER_MINUTE * 60

    @property
    def seconds(self) -> float:
        return max(self.pause_before + self.speak_seconds, self.min_hold)


BEATS: list[Beat] = [
    Beat(
        key="claim",
        action="hero",
        shows="The front page: the claim, the tagline, and a simulated family's day beside it.",
        pause_before=0.8,
        say=(
            "Your child's brain is built in the back-and-forth. "
            "Not in how many words they hear. In how often they say something and you answer within five seconds. "
            "That number predicted their vocabulary and IQ a decade later, and no parent has ever been able to count it."
        ),
    ),
    Beat(
        key="stakes",
        action="stats",
        shows="The three figures under the claim, pointed to in turn.",
        say=(
            "Fourteen to twenty-seven percent of the variance in IQ at age ten, after adjusting for income. "
            "Turns, not words, is what the brain's language area responded to. "
            "And it's coachable: parents shown their own recordings raised it, and the gain held to thirty months."
        ),
    ),
    Beat(
        key="rule",
        action="how",
        shows="The twenty-second exchange played, the five-second windows fading, the count ticking up.",
        min_hold=14,
        say=(
            "Here is the rule, counting. Each bar is something somebody said. "
            "A reply that starts inside the five-second window is a turn. Two adult bars close together merge. "
            "Six seconds of silence ends the exchange. Five turns in twenty seconds."
        ),
    ),
    Beat(
        key="term-today",
        action="term_today",
        shows="A terminal: volley today against the operator's own Bee, the day printed as bars, the words counted and thrown away.",
        min_hold=10,
        say=(
            "On my own Bee, this morning. One command reads the day, counts, and deletes the words. "
            "The only files it writes are the counts and a cursor."
        ),
    ),
    Beat(
        key="day",
        action="day",
        shows="The day like steps, the week beneath, and tomorrow's one thing beside it.",
        say=(
            "The day, an hour at a time. Hours with no child are away, not zero. "
            "And one thing for tomorrow, written from the counts and, with your consent, placed in your Bee as a reminder at that hour."
        ),
    ),
    Beat(
        key="term-reminder",
        action="term_reminder",
        shows="A terminal: the reminder appears in the Bee's todo list with its alarm, then the counter ticking during a live exchange.",
        min_hold=8,
        say=(
            "It landed in the Bee. And if you want to watch it work, it counts live as you talk."
        ),
    ),
    Beat(
        key="refused",
        action="privacy",
        shows="A transcript full of names sent to the live server; every text field dropped; the counts kept.",
        min_hold=9,
        say=(
            "The server never sees a word. Here a transcript with a name, a doctor, an address and an account number is sent to the real intake route. "
            "Every one of them is dropped at the door. The counts survive."
        ),
    ),
    Beat(
        key="agent",
        action="alexa",
        shows="A session held against the MCP server from the page, every request timed, the tool that returns no data.",
        min_hold=9,
        say=(
            "For Alexa Plus, an MCP server, held to a real session from this page. "
            "It can say how the talking went and what to try tomorrow, and it cannot repeat a word, because it never has one."
        ),
    ),
    Beat(
        key="honest",
        action="evidence",
        shows="The evidence section: what it refused, what it beat, what nobody has done yet, each stated as measured or not yet.",
        say=(
            "What is not yet measured says so on the front page, in the same size as the numbers. "
            "Nothing here is a test of a child. It is a count, like steps."
        ),
    ),
    Beat(
        key="close",
        action="close",
        shows="What it will never say.",
        min_hold=4,
        say=(
            "You already talk to your child. Now you can see it."
        ),
    ),
]


def sentences(line: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", line.strip()) if s]


def sentence_spans(line: str, total: float) -> list[tuple[float, float]]:
    """Where each sentence starts and ends, proportionally by word count."""
    parts = sentences(line)
    words = [len(s.split()) for s in parts]
    all_words = sum(words) or 1
    spans, at = [], 0.0
    for w in words:
        dur = total * w / all_words
        spans.append((at, at + dur))
        at += dur
    return spans


def script() -> str:
    """docs/VIDEO_SCRIPT.md, from the beats, so it cannot be stale."""
    out = [
        "# Demo video script",
        "",
        "Under three minutes, public, English. Judges are not required to watch",
        "past 3:00, so the strongest material is first and nothing is held back",
        "for a reveal.",
        "",
        "The one sentence this video has to land, in the first fifteen seconds:",
        "**your child's brain is built in the back-and-forth, and no parent has",
        "ever been able to count it.**",
        "",
        "This file is written by `python video/beats.py --script` from the same",
        "data the recorders and the assembler read, and a test fails if the two",
        "ever disagree. Edit `video/beats.py`, not this file.",
        "",
        "---",
        "",
        "## Shot list",
        "",
    ]
    at = 0.0
    for b in BEATS:
        cam = "a terminal, a real run rendered" if b.is_terminal else "the website, in a real browser"
        m, sec = divmod(int(at), 60)
        out += [f"**{m}:{sec:02d}, {b.key}, {cam}**", "", b.shows, "", "> " + b.say, ""]
        at += b.seconds
    m, sec = divmod(int(at), 60)
    out += [
        f"Estimated {m}:{sec:02d} of a 3:00 ceiling. The real narration decides the",
        "final cut, and `python video/beats.py` exits non-zero if the plan is",
        "over before a frame is recorded.",
        "",
        "---",
        "",
        "## The terminal beats",
        "",
        "Two beats show real commands against the operator's own Bee. They are",
        "recorded by `record_term.py`, which runs the commands for real, keeps",
        "their output, and renders it in a terminal frame the same 4K recorder",
        "captures, typed at a human pace; the frame says it is a rendering of a",
        "real run. Nothing is invented and nothing is sped up. They need the",
        "device's speaker labels (Gate 1 in planning/PLAN.md); until then the assembler",
        "cuts the web beats on their own and says which beats it dropped.",
        "",
        "## What not to do",
        "",
        "Do not name a condition, a percentile or a child's standing. Do not say",
        "the count predicts anything about this child. Do not show a word of",
        "any transcript, even the operator's own.",
        "",
    ]
    return "\n".join(out)


def main() -> int:
    if "--script" in sys.argv:
        dest = Path(__file__).parent.parent / "docs" / "VIDEO_SCRIPT.md"
        dest.write_text(script(), encoding="utf8")
        print(f"wrote {dest}")
        return 0
    total = 0.0
    for b in BEATS:
        cam = "term" if b.is_terminal else "web "
        print(f"  {b.key:14} {cam}  {b.seconds:5.1f}s  {b.say[:58]}...")
        total += b.seconds
    print(f"\nestimated {total:.0f}s of {CEILING_SECONDS}s, {CEILING_SECONDS - total:.0f}s headroom")
    return 0 if total <= CEILING_SECONDS else 1


if __name__ == "__main__":
    raise SystemExit(main())
