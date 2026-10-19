"""Score what the Bee made of the played conversation.

    python harness/beeloop/score.py

Reads the manifest written by make.py --play (who spoke when, by this
computer's clock), finds the Bee's session covering that time, and
reports three counts:

  true       the turn count of exactly what was played, from the manifest
  bee+truth  the Bee's own utterances, each given the role that was
             really speaking during it: how many turns survive the
             device's segmentation, before any inference
  blind      the Bee's own utterances with roles read by serve_return.blind:
             what Volley would report on this device today

Only counts are written (harness/beeloop/results.json); no text.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "out"
sys.path.insert(0, str(REPO / "packages" / "serve-return"))
sys.path.insert(0, str(REPO / "apps" / "ingest"))

from serve_return import Roles, Utterance, count_turns  # noqa: E402
from serve_return.blind import relabel  # noqa: E402
from volley_ingest.bee import normalize_conversation  # noqa: E402

ROLES = Roles.of(adult=["adult"], child=["child"])


def bee(args: str) -> dict:
    out = subprocess.run("bee " + args, shell=True, capture_output=True).stdout.decode("utf-8", "replace")
    return json.loads(out)


def main() -> int:
    m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    t0 = m.get("played_at")
    if not t0:
        print("play it first: python harness/beeloop/make.py --play")
        return 2
    end = t0 + m["seconds"]
    rows = bee("conversations list --limit 10 --json")
    rows = rows.get("conversations", rows)
    utts = []
    sessions = []
    for c in rows:
        s, e = c["start_time"] / 1000, (c.get("end_time") or c["start_time"]) / 1000
        if e < t0 - 60 or s > end + 60:
            continue
        raw = bee(f"conversations get {c['id']} --json")
        sessions.append({"id": c["id"], "state": raw.get("conversation", raw).get("state")})
        for u in normalize_conversation(raw):
            if u.start_s is not None and t0 - 5 <= u.start_s <= end + 10:
                utts.append(Utterance(u.start_s, "Unknown", u.text, u.end_s))
    if not utts:
        print(f"no Bee utterances between {t0:.0f} and {end:.0f}; is the session written down yet?")
        return 1
    utts.sort(key=lambda u: u.start)

    # The device's clock against this computer's: the shift that best lines
    # its utterances up with what was played.
    played = [(t0 + r["start"], t0 + r["end"], r["role"]) for r in m["rows"]]

    def overlap_score(shift: float) -> float:
        tot = 0.0
        for u in utts:
            a, b = u.start + shift, u.finish + shift
            tot += sum(max(0.0, min(b, pe) - max(a, ps)) for ps, pe, _ in played)
        return tot

    shift = max((x / 4 for x in range(-40, 41)), key=overlap_score)

    def true_role(u: Utterance) -> str:
        a, b = u.start + shift, u.finish + shift
        by = {"adult": 0.0, "child": 0.0}
        for ps, pe, r in played:
            by[r] += max(0.0, min(b, pe) - max(a, ps))
        return max(by, key=by.get)

    truth_labelled = [Utterance(u.start, true_role(u), u.text, u.end) for u in utts]
    result = {
        "session": m["session"],
        "corpus": m["corpus"],
        "played_seconds": m["seconds"],
        "utterances_played": m["utterances"],
        "utterances_bee": len(utts),
        "clock_shift_s": shift,
        "bee_sessions": sessions,
        "turns_true": m["turns_true"],
        "turns_bee_with_true_roles": count_turns(truth_labelled, ROLES),
        "turns_blind": count_turns(relabel(utts), ROLES),
        "role_accuracy_on_bee_utterances_pct": round(100 * sum(
            1 for a, b in zip(relabel(utts), sorted(truth_labelled, key=lambda u: u.start)) if a.speaker == b.speaker) / len(utts), 1),
    }
    (HERE / "results.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for k, v in result.items():
        if k not in ("bee_sessions",):
            print(f"  {k}: {v}")
    print(f"wrote {HERE / 'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
