"""One thing for tomorrow.

Two layers, so the wording can be warm and the facts cannot be wrong.
The rules here pick the fact from the day's counts; a model, when one
is configured, phrases it; a template is the floor. Every digit in the
final sentence must come from the fact, and a test extracts the digits
and checks. Never a comparison with another family, never a percentile
for a child, never the words a parent would hear as a verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from serve_return import DayCounts

FORBIDDEN = ("delay", "delayed", "behind", "risk", "at risk", "deficit", "disorder", "diagnos", "percentile", "IQ")

# LENA's published figure, stated as theirs wherever it appears.
TARGET_TURNS_PER_HOUR = 40


@dataclass(frozen=True)
class Fact:
    kind: str          # quiet_hour | slow_replies | few_questions | best_hour | first_day
    hour: int | None
    value: float | int | None
    target: float | int | None


def _clock(hour: int | None) -> str:
    if hour is None:
        return "today"
    h = hour % 24
    if h == 0:
        return "midnight"
    if h == 12:
        return "noon"
    return f"{h % 12} in the {'morning' if h < 12 else 'afternoon' if h < 17 else 'evening'}"


def pick(day: DayCounts) -> Fact:
    """The one fact worth a sentence, in priority order."""
    with_child = [h for h in day.hours if h.utterances_child > 0]
    if not with_child:
        return Fact("first_day", None, None, None)
    quiet = min(with_child, key=lambda h: h.turns)
    if quiet.turns < 5 and len(with_child) > 1:
        return Fact("quiet_hour", quiet.hour, quiet.turns, TARGET_TURNS_PER_HOUR)
    if day.response_latency_median_s is not None and day.response_latency_median_s > 5.0 and day.responses_within_window >= 3:
        return Fact("slow_replies", None, day.response_latency_median_s, 5)
    if day.turns >= 10 and day.questions_adult * 10 < day.turns:
        return Fact("few_questions", None, day.questions_adult, max(1, day.turns // 10))
    return Fact("best_hour", day.best_hour, max(h.turns for h in with_child), None)


def template(fact: Fact, child: str | None = None) -> str:
    """The floor: a plain sentence that is always available."""
    who = child or "your child"
    if fact.kind == "quiet_hour":
        return (f"Around {_clock(fact.hour)} you and {who} were in the same room and traded {fact.value} turns. "
                f"Tomorrow, ask one question then and wait for the answer.")
    if fact.kind == "slow_replies":
        return (f"Today your replies to {who} took about {fact.value} seconds. "
                f"Tomorrow, answer within a breath, even with a word; the exchange is the point, not the sentence.")
    if fact.kind == "few_questions":
        return (f"Today you asked {fact.value} questions across the day. "
                f"Tomorrow, try one more at dinner and let {who} finish.")
    if fact.kind == "best_hour":
        return (f"Your best hour with {who} was around {_clock(fact.hour)}, with {fact.value} turns. "
                f"Keep that one exactly as it is.")
    return f"A first day counted. Wear the band tomorrow and {who} will show you the hours that matter."


def digits_in(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def allowed_digits(fact: Fact) -> set[str]:
    out: set[str] = set()
    for v in (fact.value, fact.target):
        if v is not None:
            out.add(str(v))
            if isinstance(v, float) and v.is_integer():
                out.add(str(int(v)))
    if fact.hour is not None:
        out.add(str(fact.hour % 12 or 12))
    return out


def accept(text: str, fact: Fact) -> bool:
    """A phrasing is accepted only if every number in it came from the
    fact and no forbidden word is in it. Otherwise the template is used."""
    lower = text.lower()
    if any(w.lower() in lower for w in FORBIDDEN):
        return False
    return digits_in(text) <= allowed_digits(fact)


def note(day: DayCounts, child: str | None = None, phrase=None) -> tuple[str, Fact, str]:
    """The note, the fact it came from, and which layer wrote it."""
    fact = pick(day)
    floor = template(fact, child)
    if phrase is not None:
        try:
            candidate = phrase(fact, floor)
        except Exception:  # noqa: BLE001
            candidate = None
        if candidate and accept(candidate, fact):
            return candidate.strip(), fact, "model"
    return floor, fact, "template"
