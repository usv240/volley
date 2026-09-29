"""A simulated family, labelled as one everywhere it appears.

Until the operator's own day replaces it, the live site shows this
household: fourteen days of counts generated deterministically from a
seed, shaped like a real week (quiet mornings, an "away" stretch in the
middle of the day, a busy hour before bed) so the day view has
something honest to draw. Every response that touches it says
``simulated: true``.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from serve_return import HourCounts

DEMO_HOUSEHOLD = "demo-family"
DEMO_NAME = "A simulated family"
DEMO_CHILD = "Asha"


def simulated_days(days: int = 14, seed: int = 7, end: date | None = None) -> list[dict]:
    rng = random.Random(seed)
    end = end or date(2026, 9, 28)
    out = []
    for i in range(days):
        d = end - timedelta(days=days - 1 - i)
        weekend = d.weekday() >= 5
        hours: list[HourCounts] = []
        for h in range(7, 21):
            if 9 <= h <= 15 and not weekend:
                hours.append(HourCounts(hour=h))  # away: no child speech
                continue
            base = {7: 14, 8: 18, 16: 12, 17: 22, 18: 34, 19: 40, 20: 26}.get(h, 16 if weekend else 8)
            turns = max(0, int(rng.gauss(base, base * 0.25)))
            child_utts = max(turns // 2 + rng.randint(0, 3), 1 if turns else 0)
            adult_utts = max(turns // 2 + rng.randint(0, 3), 1 if turns else 0)
            hc = HourCounts(
                hour=h,
                turns=turns,
                serves_adult=int(turns * rng.uniform(0.4, 0.6)) if turns else 0,
                serves_child=0,
                responses_within_window=int(turns * rng.uniform(0.35, 0.5)) if turns else 0,
                response_latency_median_s=round(rng.uniform(1.0, 3.5), 2) if turns else None,
                questions_adult=int(turns * rng.uniform(0.1, 0.3)) if turns else 0,
                longest_volley=min(turns, rng.randint(2, 9)) if turns else 0,
                talk_seconds_adult=round(adult_utts * rng.uniform(2.0, 4.0), 1),
                talk_seconds_child=round(child_utts * rng.uniform(1.0, 2.5), 1),
                utterances_adult=adult_utts,
                utterances_child=child_utts,
                words_discarded=int((adult_utts + child_utts) * rng.uniform(4, 9)),
            )
            hc.serves_child = max(0, hc.turns - hc.serves_adult - rng.randint(0, 2)) if hc.turns else 0
            hours.append(hc)
        with_child = [h for h in hours if h.utterances_child]
        row = {
            "date": d.isoformat(),
            "hours": [h.to_dict() for h in hours],
            "turns": sum(h.turns for h in hours),
            "serves_adult": sum(h.serves_adult for h in hours),
            "serves_child": sum(h.serves_child for h in hours),
            "responses_within_window": sum(h.responses_within_window for h in hours),
            "response_latency_median_s": round(sum(h.response_latency_median_s for h in with_child) / len(with_child), 2) if with_child else None,
            "questions_adult": sum(h.questions_adult for h in hours),
            "longest_volley": max((h.longest_volley for h in hours), default=0),
            "talk_seconds_adult": round(sum(h.talk_seconds_adult for h in hours), 1),
            "talk_seconds_child": round(sum(h.talk_seconds_child for h in hours), 1),
            "words_discarded": sum(h.words_discarded for h in hours),
            "best_hour": max(hours, key=lambda h: h.turns).hour if any(h.turns for h in hours) else None,
            "quietest_hour_with_child": min(with_child, key=lambda h: h.turns).hour if with_child else None,
        }
        out.append(row)
    return out
