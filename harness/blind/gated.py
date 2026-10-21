"""Could the child-present check be the default? Measured on families it never saw.

    python harness/blind/gated.py

The check (apps/ingest/volley_ingest/presence.py) sets aside three-minute
stretches with no line that sounds like a child. On its own it loses
about a sixth of true turns, which is why it shipped as an opt-in. But
Volley already corrects a steady loss with a scale learned from other
families. This learns that scale with the check switched on, on training
families only (four inner folds, as run.py does), and scores the held-out
families with the check on and the gated scale applied. Six folds by
child. Two questions, both answered here:

  1. On real sessions, with the check on, is the count still as close?
  2. On the same sessions with the child removed, how many false turns
     are left?

Only counts are written (gated.json).
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "apps" / "ingest"))

import run  # noqa: E402
from serve_return.blind import RoleModel, infer_roles  # noqa: E402
from volley_ingest.presence import THRESHOLD, with_child  # noqa: E402


def gated_turns(us, model) -> int:
    kept, _ = with_child(us, model, THRESHOLD)
    return run.turns(kept, infer_roles(kept, model)) if kept else 0


def gated_scale(sessions, names, inner: int = 4) -> float:
    kids = sorted({n.split("/")[-1] for n in names})
    fold = {c: i % inner for i, c in enumerate(kids)}
    g = h = 0
    for j in range(inner):
        m = RoleModel().fit([run.labelled(sessions[n]) for n in names if fold[n.split("/")[-1]] != j])
        for n in names:
            if fold[n.split("/")[-1]] != j:
                continue
            pairs = run.labelled(sessions[n])
            if len(pairs) < 10:
                continue
            us = [u for u, _ in pairs]
            g += run.turns(us, [r for _, r in pairs])
            h += gated_turns(us, m)
    return round(g / h, 4) if h else 1.0


def main() -> int:
    sessions, _meta, _skipped = run.childes().load(REPO / "harness" / "childes" / "data" / "Gleason.zip")
    children = sorted({n.split("/")[-1] for n in sessions})
    fold_of = {c: i % run.FOLDS for i, c in enumerate(children)}
    rows, scales = [], []
    for k in range(run.FOLDS):
        train = [n for n in sessions if fold_of[n.split("/")[-1]] != k]
        model = RoleModel().fit([run.labelled(sessions[n]) for n in train])
        scale = gated_scale(sessions, train)
        scales.append(scale)
        for name, us in sessions.items():
            if fold_of[name.split("/")[-1]] != k:
                continue
            pairs = run.labelled(us)
            adults = [u for u, r in pairs if r == "adult"]
            if len(pairs) < 10 or len(adults) < 10:
                continue
            kept = [u for u, _ in pairs]
            gold = run.turns(kept, [r for _, r in pairs])
            real = round(gated_turns(kept, model) * scale)
            false = round(gated_turns(adults, model) * scale)
            rows.append({"session": name, "gold": gold, "gated": real, "false_without_child": false,
                         "error_pct": round(100 * (real - gold) / gold, 1) if gold else None})
    errs = [abs(r["error_pct"]) for r in rows if r["error_pct"] is not None]
    tg, tr, tf = sum(r["gold"] for r in rows), sum(r["gated"] for r in rows), sum(r["false_without_child"] for r in rows)
    ungated = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    adults_only = json.loads((HERE / "adults_only.json").read_text(encoding="utf-8"))
    result = {
        "corpus": "CHILDES Gleason, doi 10.21415/T5101R",
        "what": "the child-present check on, with a turn scale learned with it on, held out by family",
        "folds": f"{run.FOLDS} folds by child; scale learned on training families by 4 inner folds",
        "gated_scale_by_fold": scales,
        "sessions": len(rows),
        "total_error_pct": round(100 * (tr - tg) / tg, 1),
        "median_abs_session_error_pct": round(statistics.median(errs), 1),
        "sessions_within_20pct": sum(1 for e in errs if e <= 20),
        "false_as_pct_of_real": round(100 * tf / tr, 1) if tr else None,
        "compare_check_off": {"total_error_pct": ungated["total_error_pct"],
                              "median_abs_session_error_pct": ungated["median_abs_session_error_pct"],
                              "sessions_within_20pct": ungated["sessions_within_20pct"],
                              "false_as_pct_of_real": adults_only["false_as_pct_of_real"]},
        "rows": rows,
    }
    (HERE / "gated.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
