"""Counting turns with no speaker labels, measured on held-out families.

    python harness/blind/run.py                    # score, write results.json
    python harness/blind/run.py --write-model      # also train on every family and ship the model

The CHILDES Gleason corpus labels every utterance with its speaker, so the
true turn count is known. This hides the labels, infers child and adult
from the transcript alone with serve_return.blind, counts turns with the
inferred roles, and compares with the count from the true labels.

Folds are by child: all of a child's sessions (with the mother, with the
father, at dinner) sit in one fold, so no family is scored by a model that
saw it. Results: per-utterance role accuracy, and per session the true and
blind turn counts and the error, with a naive baseline beside them (every
pause longer than half a second treated as a change of speaker).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "packages" / "serve-return"))

from serve_return import Roles, Utterance, count_turns  # noqa: E402
from serve_return.blind import RoleModel, infer_roles  # noqa: E402

FOLDS = 6
MODEL_PATH = REPO / "packages" / "serve-return" / "serve_return" / "models" / "childes_roles.json"
ROLES = Roles.of(adult=["adult"], child=["child"])


def childes():
    spec = importlib.util.spec_from_file_location("childes_run", REPO / "harness" / "childes" / "run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def role_of(speaker: str) -> str | None:
    if speaker == "CHI":
        return "child"
    if speaker.startswith("ADULT:"):
        return "adult"
    return None


def labelled(us: list[Utterance]) -> list[tuple[Utterance, str]]:
    return [(u, role_of(u.speaker)) for u in sorted(us, key=lambda u: u.start) if role_of(u.speaker)]


def naive_roles(us: list[Utterance]) -> list[str]:
    """The baseline: a pause over half a second is a change of speaker."""
    out, cur = [], "adult"
    for i, u in enumerate(us):
        if i and u.start - us[i - 1].finish > 0.5:
            cur = "child" if cur == "adult" else "adult"
        out.append(cur)
    return out


def turns(us: list[Utterance], roles: list[str]) -> int:
    return count_turns([Utterance(u.start, r, u.text, u.end) for u, r in zip(us, roles)], ROLES)


def evaluate(sessions: dict[str, list[Utterance]]) -> dict:
    children = sorted({name.split("/")[-1] for name in sessions})
    fold_of = {c: i % FOLDS for i, c in enumerate(children)}
    rows, right, total = [], 0, 0
    for k in range(FOLDS):
        model = RoleModel().fit([labelled(us) for n, us in sessions.items() if fold_of[n.split("/")[-1]] != k])
        for name, us in sessions.items():
            if fold_of[name.split("/")[-1]] != k:
                continue
            pairs = labelled(us)
            if len(pairs) < 10:
                continue
            kept = [u for u, _ in pairs]
            gold_roles = [r for _, r in pairs]
            blind_roles = infer_roles(kept, model)
            right += sum(1 for a, b in zip(gold_roles, blind_roles) if a == b)
            total += len(kept)
            gold, blind, naive = turns(kept, gold_roles), turns(kept, blind_roles), turns(kept, naive_roles(kept))
            hours = max(1e-9, (max(u.finish for u in kept) - min(u.start for u in kept)) / 3600)
            rows.append({"session": name, "gold": gold, "blind": blind, "naive": naive,
                         "error_pct": round(100 * (blind - gold) / gold, 1) if gold else None,
                         "naive_error_pct": round(100 * (naive - gold) / gold, 1) if gold else None,
                         "gold_per_hour": round(gold / hours, 1), "blind_per_hour": round(blind / hours, 1)})
    errs = [abs(r["error_pct"]) for r in rows if r["error_pct"] is not None]
    nerrs = [abs(r["naive_error_pct"]) for r in rows if r["naive_error_pct"] is not None]
    g, b = [r["gold_per_hour"] for r in rows], [r["blind_per_hour"] for r in rows]
    tg, tb, tn = sum(r["gold"] for r in rows), sum(r["blind"] for r in rows), sum(r["naive"] for r in rows)
    return {
        "sessions": len(rows),
        "utterances": total,
        "role_accuracy_pct": round(100 * right / total, 1),
        "turns_true": tg,
        "turns_blind": tb,
        "turns_naive": tn,
        "total_error_pct": round(100 * (tb - tg) / tg, 1),
        "naive_total_error_pct": round(100 * (tn - tg) / tg, 1),
        "median_abs_session_error_pct": round(statistics.median(errs), 1),
        "naive_median_abs_session_error_pct": round(statistics.median(nerrs), 1),
        "sessions_within_20pct": sum(1 for e in errs if e <= 20),
        "correlation_per_hour": round(statistics.correlation(g, b), 3),
        "per_session": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(REPO / "harness" / "childes" / "data" / "Gleason.zip"))
    ap.add_argument("--out", default=str(HERE / "results.json"))
    ap.add_argument("--write-model", action="store_true")
    args = ap.parse_args()
    sessions, _meta, _skipped = childes().load(Path(args.data))
    r = evaluate(sessions)
    print(f"held-out families: role accuracy {r['role_accuracy_pct']}% on {r['utterances']} utterances; "
          f"turns {r['turns_blind']} counted blind vs {r['turns_true']} true ({r['total_error_pct']:+}%), "
          f"median session error {r['median_abs_session_error_pct']}%, {r['sessions_within_20pct']}/{r['sessions']} sessions within 20%, "
          f"per-hour correlation {r['correlation_per_hour']}")
    print(f"naive baseline (pause = speaker change): {r['turns_naive']} ({r['naive_total_error_pct']:+}%), "
          f"median session error {r['naive_median_abs_session_error_pct']}%")
    out = {"corpus": "CHILDES Gleason, doi 10.21415/T5101R, TalkBank ground rules",
           "folds": f"{FOLDS} folds by child; no family is scored by a model that saw it",
           "model": "averaged perceptron, serve_return.blind", **r}
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {args.out}")
    if args.write_model:
        model = RoleModel().fit([labelled(us) for us in sessions.values()]).pruned()
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODEL_PATH.write_text(model.to_json(), encoding="utf-8")
        print(f"wrote {MODEL_PATH}: {len(model.weights)} weights, {MODEL_PATH.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
