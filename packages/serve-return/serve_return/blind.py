"""Who said it, when the device does not say.

The Bee labels every speaker "Unknown" (1,004 of 1,004 utterances on the
builder's account, 2026-10-19), and a turn counter needs to know which
utterances are the child's and which the adult's. Speech to and from a
two-to-five-year-old differs in the words and in the rhythm: children's
utterances are shorter and draw on a small early vocabulary; adults'
speech to them is full of questions, names and praise; an answer follows
a question. So the roles can be read from the transcript itself.

``RoleModel`` is an averaged perceptron over each utterance's words, word
pairs and length, the words of the utterances either side of it, and the
pauses before and after. It is small, dependency-free and inspectable:
its parameters are one weight per feature, and a positive score means
child. ``childes_model()`` loads one trained on every family in the
CHILDES Gleason corpus; ``harness/blind`` trains on all but one family at
a time and scores on the one held out, so the published accuracy is for
families the model never saw.

``infer_roles`` returns a role per utterance; ``relabel`` turns a list of
unlabelled utterances into adult and child ones the turn rule can count.
Nothing here stores a word: the model holds feature weights, the output
is a role per utterance.
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from importlib import resources
from typing import Iterable, Sequence

from .rule import Utterance

_TOKEN = re.compile(r"[a-z']+")
CONTEXT_FEATURES = 12


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(str(text).lower())


def features(text: str) -> list[str]:
    """Words, word pairs, a length bucket, and a question mark."""
    w = tokens(text)
    n = len(w)
    bucket = "len:1" if n <= 1 else "len:2-3" if n <= 3 else "len:4-6" if n <= 6 else "len:7-10" if n <= 10 else "len:11+"
    feats = [bucket] + w + [f"{a}_{b}" for a, b in zip(w, w[1:])]
    if str(text).rstrip().endswith("?"):
        feats.append("q:?")
    return feats


def _gap(seconds: float) -> str:
    return "<0.5" if seconds < 0.5 else "<2" if seconds < 2 else "<5" if seconds < 5 else "5+"


def context_features(texts: Sequence[str], gaps_before: Sequence[float], i: int) -> list[str]:
    f = ["c:" + x for x in features(texts[i])]
    f += (["p:" + x for x in features(texts[i - 1])][:CONTEXT_FEATURES] if i > 0 else ["p:START"])
    f += (["n:" + x for x in features(texts[i + 1])][:CONTEXT_FEATURES] if i + 1 < len(texts) else ["n:END"])
    f.append("gp:" + _gap(gaps_before[i]))
    f.append("gn:" + _gap(gaps_before[i + 1] if i + 1 < len(texts) else 99.0))
    f.append("bias")
    return f


def _gaps(utterances: Sequence[Utterance]) -> list[float]:
    return [99.0] + [max(0.0, b.start - a.finish) for a, b in zip(utterances, utterances[1:])]


@dataclass
class RoleModel:
    weights: dict[str, float] = field(default_factory=dict)

    def score(self, feats: Iterable[str]) -> float:
        w = self.weights
        return sum(w.get(x, 0.0) for x in feats)

    def fit(self, sessions: Iterable[Sequence[tuple[Utterance, str]]], epochs: int = 6, seed: int = 7) -> "RoleModel":
        """Averaged perceptron. ``sessions`` is a list of sessions, each a
        time-ordered list of (utterance, "adult" or "child")."""
        rows: list[tuple[list[str], int]] = []
        for session in sessions:
            us = [u for u, _ in session]
            texts, gaps = [u.text for u in us], _gaps(us)
            for i, (_, role) in enumerate(session):
                rows.append((context_features(texts, gaps, i), 1 if role == "child" else -1))
        w: dict[str, float] = defaultdict(float)
        acc: dict[str, float] = defaultdict(float)
        stamp: dict[str, int] = defaultdict(int)
        step = 1
        rnd = random.Random(seed)
        for _ in range(epochs):
            rnd.shuffle(rows)
            for f, y in rows:
                if y * sum(w[x] for x in f) <= 0:
                    for x in f:
                        acc[x] += (step - stamp[x]) * w[x]
                        stamp[x] = step
                        w[x] += y
                step += 1
        self.weights = {x: (acc[x] + (step - stamp[x]) * w[x]) / step for x in w}
        return self

    def pruned(self, floor: float = 0.02, places: int = 3) -> "RoleModel":
        return RoleModel({x: round(v, places) for x, v in self.weights.items() if abs(v) >= floor})

    def to_json(self) -> str:
        return json.dumps({"kind": "averaged-perceptron", "positive": "child", "weights": self.weights}, separators=(",", ":"))

    @staticmethod
    def from_json(s: str) -> "RoleModel":
        return RoleModel(json.loads(s)["weights"])


def childes_model() -> RoleModel:
    """The model trained on the whole CHILDES Gleason corpus, shipped with
    the package. Built by harness/blind/run.py --write-model."""
    return RoleModel.from_json(resources.files("serve_return").joinpath("models/childes_roles.json").read_text(encoding="utf-8"))


def infer_roles(utterances: Sequence[Utterance], model: RoleModel | None = None) -> list[str]:
    """A role per utterance, in the order given (sort by start first)."""
    model = model or childes_model()
    us = list(utterances)
    texts, gaps = [u.text for u in us], _gaps(us)
    return ["child" if model.score(context_features(texts, gaps, i)) > 0 else "adult" for i in range(len(us))]


def relabel(utterances: Sequence[Utterance], model: RoleModel | None = None) -> list[Utterance]:
    """The same utterances with speaker set to "adult" or "child", ready
    for count_day with Roles.of(adult=["adult"], child=["child"])."""
    us = sorted(utterances, key=lambda u: u.start)
    roles = infer_roles(us, model)
    return [Utterance(u.start, r, u.text, u.end) for u, r in zip(us, roles)]
