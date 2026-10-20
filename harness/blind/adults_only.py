"""The corpus version of the device's negative control: no child present.

    python harness/blind/adults_only.py

Every Gleason session, with the child's lines removed, leaves adults
talking to each other with the original timing. The true adult-child
count of that is zero, so whatever the label-free count finds is false.
It is set beside the same session's real count, by the same model, so
the false rate reads as a share of a real day. Six folds by child, as in
run.py: no family is scored by a model that saw it.

On the device (harness/beeloop/controls.py) two adults from one family
dinner gave 21 false turns in three minutes. This asks whether that one
session is typical. Only counts are written (adults_only.json).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run  # noqa: E402
from serve_return.blind import RoleModel, infer_roles  # noqa: E402


def main() -> int:
    sessions, _meta, _skipped = run.childes().load(HERE.parent / "childes" / "data" / "Gleason.zip")
    children = sorted({n.split("/")[-1] for n in sessions})
    fold_of = {c: i % run.FOLDS for i, c in enumerate(children)}
    rows = []
    for k in range(run.FOLDS):
        train = [n for n in sessions if fold_of[n.split("/")[-1]] != k]
        model = RoleModel().fit([run.labelled(sessions[n]) for n in train])
        scale = run.learn_scale(sessions, train)
        for name, us in sessions.items():
            if fold_of[name.split("/")[-1]] != k:
                continue
            pairs = run.labelled(us)
            adults = [u for u, r in pairs if r == "adult"]
            if len(pairs) < 10 or len(adults) < 10:
                continue
            kept = [u for u, _ in pairs]
            real = round(run.turns(kept, infer_roles(kept, model)) * scale)
            false = round(run.turns(adults, infer_roles(adults, model)) * scale)
            rows.append({"session": name, "turns_true": run.turns(kept, [r for _, r in pairs]),
                         "turns_blind": real, "false_turns_without_child": false})
    tr = sum(r["turns_blind"] for r in rows)
    tf = sum(r["false_turns_without_child"] for r in rows)
    by = {}
    for setting in ("Dinner", "Father", "Mother"):
        rs = [r for r in rows if r["session"].startswith(setting + "/")]
        a, b = sum(r["false_turns_without_child"] for r in rs), sum(r["turns_blind"] for r in rs)
        by[setting] = {"sessions": len(rs), "false_as_pct_of_real": round(100 * a / b, 1) if b else None}
    result = {"corpus": "CHILDES Gleason, doi 10.21415/T5101R",
              "what": "each session with the child's lines removed; every adult-child turn counted is false",
              "folds": f"{run.FOLDS} folds by child", "sessions": len(rows),
              "false_as_pct_of_real": round(100 * tf / tr, 1), "by_setting": by, "rows": rows}
    (HERE / "adults_only.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"{len(rows)} sessions: false turns with no child = {result['false_as_pct_of_real']} percent of the real count")
    for s, v in by.items():
        print(f"  {s:7} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
