"""The rule, and the counts it yields.

Definition
----------
A conversational turn is one alternation between an adult and a child
within a five-second window: an adult utterance followed by a child
utterance whose start is within five seconds of the adult utterance's
end, or the reverse. Consecutive utterances by the same role merge into
one block first, so a parent who says three sentences in a row has
spoken once for the purposes of the count. A gap over five seconds ends
the exchange. This is the conversational turn count as the LENA system
defines it and as the studies that used it describe it (Gilkerson et
al., Pediatrics 2018; Romeo et al., Psychological Science 2018), and as
the manual comparison in Child Development (doi 10.1111/cdev.13495)
hand-counted it under "the 5-second pause rule". The window is a
constant so a test can pin it.

What "adult" and "child" are
----------------------------
Labels are the caller's. A Bee labels the wearer one way and other
voices another; a CHILDES transcript uses MOT, FAT, CHI. ``Roles`` maps
labels to the two roles; anything unmapped is ignored, which is what a
third adult in the room should be unless the caller says otherwise.

What comes out
--------------
Per hour of the day and for the day: turns, who served, responses
within the window, the median reply time, adult questions, the longest
exchange, minutes spoken by each role, and how many words were read and
discarded. No field can hold text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from statistics import median
from typing import Iterable, Sequence

WINDOW_SECONDS = 5.0

# Words per second used to estimate an utterance's length when the
# transcript carries a start and no end. Conversational English runs
# about 2.5 words a second; the estimate matters only for talk minutes.
_WORDS_PER_SECOND = 2.5
_MIN_UTTERANCE_SECONDS = 1.0

_WH = re.compile(r"^\s*(who|what|when|where|why|how|which|whose|do|does|did|can|could|would|will|is|are|was|were|shall|should)\b", re.I)


@dataclass(frozen=True)
class Utterance:
    """One thing one speaker said, with when.

    ``start`` and ``end`` are seconds since the epoch, UTC. ``end`` may be
    omitted, in which case the length is estimated from the word count.
    ``speaker`` is whatever label the source uses. ``text`` is used for
    the word count and the question test and is never stored.
    """

    start: float
    speaker: str
    text: str = ""
    end: float | None = None

    @staticmethod
    def from_iso(ts: str, speaker: str, text: str = "", end_ts: str | None = None) -> "Utterance":
        return Utterance(_iso_to_epoch(ts), speaker, text, _iso_to_epoch(end_ts) if end_ts else None)

    @property
    def words(self) -> int:
        return len(self.text.split())

    @property
    def finish(self) -> float:
        if self.end is not None and self.end >= self.start:
            return self.end
        return self.start + max(_MIN_UTTERANCE_SECONDS, self.words / _WORDS_PER_SECOND)


@dataclass(frozen=True)
class Roles:
    """Which labels are the adult and which are the child."""

    adult: frozenset[str]
    child: frozenset[str]

    @staticmethod
    def of(adult: Iterable[str], child: Iterable[str]) -> "Roles":
        return Roles(frozenset(_norm(a) for a in adult), frozenset(_norm(c) for c in child))

    def role(self, speaker: str) -> str | None:
        s = _norm(speaker)
        if s in self.adult:
            return "adult"
        if s in self.child:
            return "child"
        return None


@dataclass
class HourCounts:
    """One hour of the day, numbers only."""

    hour: int
    turns: int = 0
    serves_adult: int = 0
    serves_child: int = 0
    responses_within_window: int = 0
    response_latency_median_s: float | None = None
    questions_adult: int = 0
    longest_volley: int = 0
    talk_seconds_adult: float = 0.0
    talk_seconds_child: float = 0.0
    utterances_adult: int = 0
    utterances_child: int = 0
    words_discarded: int = 0
    _latencies: list[float] = field(default_factory=list, repr=False, compare=False)

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self) if not f.name.startswith("_")}


@dataclass
class DayCounts:
    """A day: its hours and their sum."""

    date: str
    hours: list[HourCounts]
    turns: int
    serves_adult: int
    serves_child: int
    responses_within_window: int
    response_latency_median_s: float | None
    questions_adult: int
    longest_volley: int
    talk_seconds_adult: float
    talk_seconds_child: float
    words_discarded: int
    best_hour: int | None
    quietest_hour_with_child: int | None

    def to_dict(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "hours"}
        d["hours"] = [h.to_dict() for h in self.hours]
        return d


@dataclass(frozen=True)
class _Block:
    role: str
    start: float
    end: float
    words: int
    question: bool


def _norm(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(label).strip().lower()).strip("_")


def _iso_to_epoch(ts: str) -> float:
    s = ts.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _blocks(utterances: Sequence[Utterance], roles: Roles, window: float) -> list[_Block]:
    """Role-labelled utterances in time order, same-role runs merged.

    A run merges only while the gap between its utterances is within the
    window. A parent who speaks at six o'clock and again at a quarter past
    has spoken twice, not once for fifteen minutes; merging across the
    gap would swallow the exchange that started the second time.
    """
    labelled = [(roles.role(u.speaker), u) for u in sorted(utterances, key=lambda u: u.start)]
    out: list[_Block] = []
    for role, u in labelled:
        if role is None or not u.text.strip():
            continue
        question = role == "adult" and (u.text.rstrip().endswith("?") or bool(_WH.match(u.text)))
        if out and out[-1].role == role and u.start - out[-1].end <= window:
            prev = out[-1]
            out[-1] = _Block(role, prev.start, max(prev.end, u.finish), prev.words + u.words, prev.question or question)
        else:
            out.append(_Block(role, u.start, u.finish, u.words, question))
    return out


def _is_turn(a: _Block, b: _Block, window: float) -> bool:
    return a.role != b.role and b.start - a.end <= window


def count_turns(utterances: Sequence[Utterance], roles: Roles, window: float = WINDOW_SECONDS) -> int:
    """The turn count alone, for callers who want one integer."""
    blocks = _blocks(utterances, roles, window)
    return sum(1 for a, b in zip(blocks, blocks[1:]) if _is_turn(a, b, window))


def count_day(
    utterances: Sequence[Utterance],
    roles: Roles,
    date: str | None = None,
    window: float = WINDOW_SECONDS,
    tz_offset_hours: float = 0.0,
) -> DayCounts:
    """Every count for one day. Hours are local by ``tz_offset_hours``.

    A turn is credited to the hour in which the answering block starts.
    """
    blocks = _blocks(utterances, roles, window)
    hours: dict[int, HourCounts] = {}

    def hour_of(t: float) -> int:
        return int(((t + tz_offset_hours * 3600) % 86400) // 3600)

    def hc(t: float) -> HourCounts:
        h = hour_of(t)
        if h not in hours:
            hours[h] = HourCounts(hour=h)
        return hours[h]

    for b in blocks:
        h = hc(b.start)
        seconds = max(0.0, b.end - b.start)
        if b.role == "adult":
            h.utterances_adult += 1
            h.talk_seconds_adult += seconds
            if b.question:
                h.questions_adult += 1
        else:
            h.utterances_child += 1
            h.talk_seconds_child += seconds
        h.words_discarded += b.words

    volley_len = 0
    for a, b in zip(blocks, blocks[1:]):
        gap = b.start - a.end
        if _is_turn(a, b, window):
            h = hc(b.start)
            h.turns += 1
            if volley_len == 0:
                # a is the serve: the block that opened this exchange
                if a.role == "adult":
                    h.serves_adult += 1
                else:
                    h.serves_child += 1
            volley_len += 1
            h.longest_volley = max(h.longest_volley, volley_len)
            if a.role == "child" and b.role == "adult":
                h.responses_within_window += 1
                h._latencies.append(max(0.0, gap))
        else:
            volley_len = 0

    for h in hours.values():
        h.response_latency_median_s = round(median(h._latencies), 2) if h._latencies else None

    ordered = [hours[k] for k in sorted(hours)]
    all_lat = [x for h in ordered for x in h._latencies]
    with_child = [h for h in ordered if h.utterances_child > 0]
    best = max(ordered, key=lambda h: h.turns).hour if ordered and any(h.turns for h in ordered) else None
    quiet = min(with_child, key=lambda h: h.turns).hour if with_child else None
    if date is None:
        date = datetime.fromtimestamp(blocks[0].start, tz=timezone.utc).date().isoformat() if blocks else "1970-01-01"
    return DayCounts(
        date=date,
        hours=ordered,
        turns=sum(h.turns for h in ordered),
        serves_adult=sum(h.serves_adult for h in ordered),
        serves_child=sum(h.serves_child for h in ordered),
        responses_within_window=sum(h.responses_within_window for h in ordered),
        response_latency_median_s=round(median(all_lat), 2) if all_lat else None,
        questions_adult=sum(h.questions_adult for h in ordered),
        longest_volley=max((h.longest_volley for h in ordered), default=0),
        talk_seconds_adult=round(sum(h.talk_seconds_adult for h in ordered), 1),
        talk_seconds_child=round(sum(h.talk_seconds_child for h in ordered), 1),
        words_discarded=sum(h.words_discarded for h in ordered),
        best_hour=best,
        quietest_hour_with_child=quiet,
    )
