"""Roles with no trained model: every line a new speaker, then scaled.

The bundled role model is trained on CHILDES and carries the corpus's
non-commercial licence. A programme that cannot use it can still count:
`volley setup --blind --role-model alternation` takes every line as a
change of speaker, which overcounts, and scales the day by the ratio
measured on the corpus (harness/blind/results.json,
alternating_scale_all_families). Held out by family it matched the total
(+0.3 percent) and was worse where a parent looks: 13.4 percent median
session error and 40 of 54 sessions within 20 percent, against 9.6 and
49 for the model. No corpus data ships with it, only one number.
"""

from __future__ import annotations

from serve_return import Utterance

# A test fails if the harness moves and this does not.
ALTERNATION_SCALE = 0.4896


def alternate(us: list[Utterance]) -> list[Utterance]:
    ordered = sorted(us, key=lambda u: u.start)
    return [Utterance(u.start, "adult" if i % 2 == 0 else "child", u.text, u.end) for i, u in enumerate(ordered)]


def scale_day(day, scale: float = ALTERNATION_SCALE):
    for h in day.hours:
        h.turns = round(h.turns * scale)
    day.turns = sum(h.turns for h in day.hours) if day.hours else round(day.turns * scale)
    return day
