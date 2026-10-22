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
Most beats are the deployed website driven by a real browser at 4K. Three
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
one sentence: the words were not the point, the back-and-forth was,
and Volley counts it on a band parents already wear. Everything after is evidence in
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
        key="hook",
        action="hook",
        shows="Black, the words thirty million words, then the first screen under them; the headline pointed to on the back-and-forth.",
        pause_before=0.6,
        min_hold=15,
        say=(
            "You have heard of the thirty-million-word gap. For years, parents were told: talk more. Then researchers looked inside children's brains, and the words were not the point. The back-and-forth was."
        ),
    ),
    Beat(
        key="volley",
        action="what",
        shows="The first screen: the day card's number, then the lede, then a hold on the day card.",
        say=(
            "Meet Volley: a step counter for conversations with your child. On the Bee you already wear, it counts the exchanges, shows the hour they happen, and nudges you when your best hour goes quiet. The numbers, never the words."
        ),
    ),
    Beat(
        key="how",
        action="how",
        shows="How it counts, in twenty seconds: Play pressed, the bars appearing, replies inside five seconds lit, the count reaching five.",
        min_hold=14,
        say=(
            "Here is how. A parent speaks. A child answers inside five seconds. That is one turn. Volley reads who is talking from the words and the pauses, and keeps only the count."
        ),
    ),
    Beat(
        key="term-count",
        action="term_count",
        shows="A terminal, labelled real Bee, a replayed research conversation: volley today on the builder's own Bee; the bar, sixty-six turns, the words thrown away, the reminder placed.",
        min_hold=14,
        say=(
            "Now Volley on my actual Bee. We played a real family's recorded conversation to the band. One command reads it, finds sixty-six turns, deletes every word on my own computer, and places one thing to try tomorrow into the Bee itself."
        ),
    ),
    Beat(
        key="term-reminder",
        action="term_reminder",
        shows="A terminal: the reminder in the Bee's todo list, with its alarm at three the next afternoon and its sentence.",
        min_hold=9,
        say="There it is, in the Bee, for three in the afternoon, with something to do.",
    ),
    Beat(
        key="term-nudge",
        action="term_nudge",
        shows="A terminal, labelled live Bee stream, a speaker standing in for an Echo: volley live watching the usual hour, the hour going quiet, the nudge printed and placed in the Bee. The real run.",
        min_hold=12,
        say=(
            "But Volley does not only count yesterday. During the hour we usually talk most, it watches the Bee's live stream, and if that hour goes quiet, a nudge reaches the Bee right then. A speaker in the room says it, the way an Echo could. While there is still time to connect."
        ),
    ),
    Beat(
        key="plan",
        action="plan",
        shows="The day, an hour at a time; then the week's plan, written by Claude on Amazon Bedrock, the three lines pointed to in turn.",
        say=(
            "Over a week, patterns appear: a busy evening, a quiet afternoon with the child right there. Claude on Amazon Bedrock turns them into a plan the way a home visitor would: keep the hour that works, one idea for the quiet one, one for the weekend. A gate in code refuses any number the counts did not hold."
        ),
    ),
    Beat(
        key="proof",
        action="proof",
        shows="The evidence table: the corpus row, the Bee row, then the child-present row where two adults count as zero beside the real conversation's sixty-six.",
        say=(
            "Does it hold up? On twenty-six hours of independent family recordings: twenty thousand turns, and none where one person was talking alone. On the Bee, sixty-six of seventy-five. And with the child-present check on, two adults talking with no child in the room count as zero, while a real conversation keeps all sixty-six."
        ),
    ),
    Beat(
        key="ecosystem",
        action="alexa",
        shows="Ask out loud: a question tapped, the tool call, the answer read aloud. Then the agents section on the evidence page, simulated Bee data labelled first.",
        min_hold=15,
        say=(
            "Parents can ask out loud. Volley's MCP server answers Alexa Plus from the counts alone; it never had a word to repeat. Two Strands agents on Bedrock, one hosted on AgentCore, explain a quiet day from the Bee's own summary. This one runs on simulated Bee data."
        ),
    ),
    Beat(
        key="beyond",
        action="beyond",
        shows="The coach's list of families; then the install line and the cost.",
        min_hold=6,
        say=(
            "For families with a home visitor, a read-only view carries the coaching between visits. The counter is open source on PyPI. Four cents a family a month, on a band they already wear."
        ),
    ),
    Beat(
        key="close",
        action="close",
        shows="The first screen again, resting on the headline; the pointer hidden; the last line held.",
        min_hold=11,
        say=(
            "Volley is not about counting every word. It is about making room for the conversations that matter. You already talk to your child. Now you can see it."
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
        "**the words were not the point; the back-and-forth was, and Volley",
        "counts it on the Bee you already wear.**",
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
        "Three beats show real commands against the builder's own Bee. They are",
        "recorded by `record_term.py`, which runs the commands for real, keeps",
        "their output, and renders it in a terminal frame the same 4K recorder",
        "captures, typed at a human pace; the frame says it is a rendering of a",
        "real run. Nothing is invented and nothing is sped up. The nudge beat is",
        "the real afternoon run, captured when the family's usual hour comes;",
        "until it exists the assembler cuts without it and says so.",
        "",
        "## What not to do",
        "",
        "Do not name a condition, a percentile or a child's standing. Do not say",
        "the count predicts anything about this child. Do not show a word of",
        "any transcript, even the builder's own. Do not present anything as a",
        "problem, a bug or a limit: the video shows what works; the written",
        "feedback carries the findings.",
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
