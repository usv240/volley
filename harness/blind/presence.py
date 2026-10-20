"""Could the label-free count tell when no child is there? Measured, not shipped.

    python harness/blind/presence.py

adults_only.py shows that with the child removed, adults talking still
produce false turns at about four in ten of the real count. The obvious
fix is to count a stretch only if something in it sounds like a child:
here, the mean of the top tenth of the role model's child-scores in each
three-minute window, about the length of a short Bee session.

Held out by family, with each threshold picked on training families
alone, it refuses about seven in ten adults-only windows and drops about
one real window in five. That trades one error for another, so Volley
does not ship it; a speaker label from the Bee would remove both.
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run  # noqa: E402
from serve_return.blind import RoleModel, _gaps, context_features  # noqa: E402
S, _, _ = run.childes().load(HERE.parent / "childes" / "data" / "Gleason.zip")
kids = sorted({n.split("/")[-1] for n in S}); fold = {c: i % 6 for i, c in enumerate(kids)}
W = 180
def windows(us):
    us = sorted(us, key=lambda u: u.start); out, cur, t0 = [], [], None
    for u in us:
        if t0 is None: t0 = u.start
        if u.start - t0 > W: out.append(cur); cur, t0 = [], u.start
        cur.append(u)
    out.append(cur); return [w for w in out if len(w) >= 15]
def top(us, m):
    us = sorted(us, key=lambda u: u.start); t, g = [u.text for u in us], _gaps(us)
    sc = sorted((m.score(context_features(t, g, i)) for i in range(len(us))), reverse=True)
    return statistics.mean(sc[:max(1, len(sc)//10)])
def scored(names, m):
    R, A = [], []
    for n in names:
        p = run.labelled(S[n])
        for w in windows([u for u, _ in p]):
            lab = {id(u): r for u, r in p}
            R.append((top(w, m), run.turns(w, [lab[id(u)] for u in w])))
            a = [u for u in w if lab[id(u)] == "adult"]
            if len(a) >= 15: A.append(top(a, m))
    return R, A
def pick(R, A):
    return max(((sum(s > t for s, _ in R)/len(R) + sum(s <= t for s in A)/len(A)) / 2, t) for t in [s for s, _ in R] + A)[1]
kept = lost = tot = refused = na = nr = 0; ths = []
for k in range(6):
    train = [n for n in S if fold[n.split("/")[-1]] != k]
    tk = sorted({n.split("/")[-1] for n in train}); inner = {c: i % 4 for i, c in enumerate(tk)}
    IR, IA = [], []
    for j in range(4):
        mi = RoleModel().fit([run.labelled(S[n]) for n in train if inner[n.split("/")[-1]] != j])
        r, a = scored([n for n in train if inner[n.split("/")[-1]] == j], mi); IR += r; IA += a
    th = pick(IR, IA); ths.append(round(th, 2))
    m = RoleModel().fit([run.labelled(S[n]) for n in train])
    R, A = scored([n for n in S if fold[n.split("/")[-1]] == k], m)
    nr += len(R); kept += sum(s > th for s, _ in R); tot += sum(t for _, t in R); lost += sum(t for s, t in R if s <= th)
    na += len(A); refused += sum(s <= th for s in A)
result = {"corpus": "CHILDES Gleason, doi 10.21415/T5101R", "window_seconds": W,
          "statistic": "mean of the top tenth of utterance child-scores in the window",
          "folds": "6 by child; each threshold chosen on its training families by 4 inner folds",
          "thresholds": ths,
          "real_windows": nr, "real_windows_kept_pct": round(100 * kept / nr, 1), "true_turns_lost_pct": round(100 * lost / tot, 1),
          "adult_only_windows": na, "adult_only_windows_refused_pct": round(100 * refused / na, 1),
          "shipped": False,
          "why_not": "it trades false turns for lost true ones; one speaker label from the Bee would remove both"}
(HERE / "presence.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "thresholds"}, indent=1))
