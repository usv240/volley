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

from .rule import DayCounts

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
                f"Tomorrow, at the same time, ask {who} about one thing they did today and wait for the answer.")
    return f"A first day counted. Wear the band tomorrow and {who} will show you the hours that matter."


_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_WORD = {w: i for i, w in enumerate(_UNITS)} | _TENS | {"dozen": 12, "hundred": 100}
# Words that name a number but are ordinary English in a note: "one" (one
# thing, one question) and "an hour" are not counts. They are read as
# numbers only when they stand next to another number word ("thirty one").
_SOFT = {"one"}


def _number_words(text: str) -> set[str]:
    """Numbers written as words, as digits: 'thirty eight' is 38,
    'forty-two' is 42, 'a dozen' is 12. A model that writes a number out
    must still match the fact."""
    words = re.findall(r"[a-z]+", text.lower().replace("-", " "))
    out: set[str] = set()
    i = 0
    while i < len(words):
        w = words[i]
        if w in _TENS and i + 1 < len(words) and words[i + 1] in _WORD and _WORD[words[i + 1]] < 10:
            out.add(str(_TENS[w] + _WORD[words[i + 1]]))
            i += 2
            continue
        if w in _WORD and w not in _SOFT:
            out.add(str(_WORD[w]))
        i += 1
    return out


def digits_in(text: str) -> set[str]:
    """Every number in the text, whether written in digits or in words."""
    return set(re.findall(r"\d+(?:\.\d+)?", text)) | _number_words(text)


def allowed_digits(fact: Fact) -> set[str]:
    out: set[str] = set()
    for v in (fact.value, fact.target):
        if v is not None:
            out.add(str(v))
            if isinstance(v, float) and v.is_integer():
                out.add(str(int(v)))
    if fact.hour is not None:
        out.add(str(fact.hour % 12 or 12))
        out.add(str(fact.hour % 24))
    return out


# A note names one thing to do. The floor always does; a phrasing that
# drops the action is refused like one that invents a number.
ACTION_WORDS = ("tomorrow", "try", "ask", "answer", "wait", "let ")


def has_action(text: str) -> bool:
    lower = text.lower()
    return any(w in lower for w in ACTION_WORDS)


def accept(text: str, fact: Fact) -> bool:
    """A phrasing is accepted only if every number in it came from the
    fact and no forbidden word is in it. Otherwise the template is used."""
    lower = text.lower()
    if any(w.lower() in lower for w in FORBIDDEN):
        return False
    if fact.kind != "first_day" and not has_action(text):
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
