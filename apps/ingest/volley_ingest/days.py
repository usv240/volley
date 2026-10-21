"""From the Bee's utterances to a day of counts, and nothing else.

This is the line the whole product is built on. Utterances come in
with their words; `count_days` hands them to the rule, groups the
result by date, and returns numbers. The words are in scope for the
duration of this function and are gone when it returns. A test feeds a
transcript of names through the command and asserts that the only
files on disk afterwards are a cursor and counts.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from serve_return import DayCounts, Roles, count_day
from serve_return import Utterance as RuleUtterance

from .bee import Utterance
from .household import Household


def roles_for(h: Household) -> Roles:
    if h.blind:
        return Roles.of(adult=["adult"], child=["child"])
    return Roles.of(adult=h.parent_labels, child=h.child_labels)


def local_date(start_s: float, tz_offset_hours: float) -> str:
    return (datetime.fromtimestamp(start_s, tz=timezone.utc) + timedelta(hours=tz_offset_hours)).date().isoformat()


def to_rule(u: Utterance) -> RuleUtterance | None:
    if u.start_s is None:
        return None
    return RuleUtterance(start=u.start_s, speaker=u.speaker or "", text=u.text, end=u.end_s)


def count_days(utterances: list[Utterance], h: Household, report: dict | None = None) -> list[DayCounts]:
    """One DayCounts per local date that had any mapped speech, in order.
    ``report``, if given, receives how many stretches were set aside."""
    roles = roles_for(h)
    by_day: dict[str, list[RuleUtterance]] = {}
    for u in utterances:
        r = to_rule(u)
        if r is None:
            continue
        by_day.setdefault(local_date(r.start, h.tz_offset_hours), []).append(r)
    if h.blind:
        # No labels from the device: read the roles from the words and the
        # pauses, one day at a time, then count as usual. Measured on
        # held-out CHILDES families in harness/blind.
        from serve_return.blind import relabel

        from serve_return.blind import calibrate_day

        if h.only_with_child:
            from .presence import with_child

            set_aside = 0
            for d in list(by_day):
                kept, dropped = with_child(by_day[d])
                set_aside += dropped
                by_day[d] = kept
            by_day = {d: us for d, us in by_day.items() if us}
            if report is not None:
                report["stretches_set_aside"] = set_aside
        by_day = {d: relabel(us) for d, us in by_day.items()}
        return [calibrate_day(count_day(by_day[d], roles, date=d, tz_offset_hours=h.tz_offset_hours)) for d in sorted(by_day)]
    return [count_day(by_day[d], roles, date=d, tz_offset_hours=h.tz_offset_hours) for d in sorted(by_day)]


def words_in(utterances: list[Utterance]) -> int:
    return sum(len(u.text.split()) for u in utterances)
