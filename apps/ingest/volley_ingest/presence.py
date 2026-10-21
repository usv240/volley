"""Count only the stretches where a child seems to be there. Opt-in.

With every speaker "Unknown", two adults talking count as turns: 21 false
turns in three minutes on the Bee, and on the corpus, with the child
removed, false turns at 43 percent of a real day's rate
(harness/beeloop/controls.py, harness/blind/adults_only.py). A parent who
spends their evenings with other adults can ask Volley to set those
stretches aside.

The rule is the one measured in harness/blind/presence.py: cut the day
into three-minute stretches; in each, score every utterance with the role
model and take the mean of the top tenth; a stretch with no line that
sounds enough like a child is set aside. Held out by family, it refused
70.6 percent of adults-only stretches and lost 15.7 percent of true
turns. That trade is why it is a choice and not the default: the parent
picks which error they would rather have.

Only scores and times are used here; the words stay where they were.
"""

from __future__ import annotations

import json
from pathlib import Path

from serve_return import Utterance
from serve_return.blind import RoleModel, childes_model, context_features

WINDOW_SECONDS = 180

# The median of the six held-out thresholds in harness/blind/presence.json.
# A test fails if the harness moves and this does not.
THRESHOLD = 9.91


def _score_top_tenth(us: list[Utterance], model: RoleModel) -> float:
    texts = [u.text for u in us]
    gaps = [99.0] + [max(0.0, b.start - a.finish) for a, b in zip(us, us[1:])]
    scores = sorted((model.score(context_features(texts, gaps, i)) for i in range(len(us))), reverse=True)
    top = scores[: max(1, len(scores) // 10)]
    return sum(top) / len(top)


def stretches(us: list[Utterance], seconds: float = WINDOW_SECONDS) -> list[list[Utterance]]:
    """Consecutive three-minute stretches, each starting at its first utterance."""
    out: list[list[Utterance]] = []
    for u in sorted(us, key=lambda x: x.start):
        if out and u.start - out[-1][0].start <= seconds:
            out[-1].append(u)
        else:
            out.append([u])
    return out


def with_child(us: list[Utterance], model: RoleModel | None = None, threshold: float = THRESHOLD) -> tuple[list[Utterance], int]:
    """The utterances in stretches that sound like a child is there, and how
    many stretches were set aside."""
    model = model or childes_model()
    kept: list[Utterance] = []
    dropped = 0
    for w in stretches(us):
        if _score_top_tenth(w, model) > threshold:
            kept.extend(w)
        else:
            dropped += 1
    return kept, dropped


def harness_threshold(repo: Path) -> float:
    ts = sorted(json.loads((repo / "harness" / "blind" / "presence.json").read_text(encoding="utf-8"))["thresholds"])
    mid = len(ts) // 2
    return round((ts[mid - 1] + ts[mid]) / 2 if len(ts) % 2 == 0 else ts[mid], 2)
