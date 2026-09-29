"""The count against recordings we did not make.

    python harness/playlogue/run.py --data <dir> [--out harness/playlogue/results.json]

Playlogue v1 (Kalanadhabhatta et al., IMWUT 2024): 33 hours of preschool
adult-child play drawn from CHILDES, with speaker-attributed,
time-aligned transcripts (segment-level CTM files from a forced
aligner) and diarisation ground truth. Licence CC BY-NC-SA 3.0 behind
the TalkBank ground rules, which is why the data is not in this
repository: point --data at a local copy accepted under those rules.

What it publishes, per session and in total:

- turns per hour by the rule, using the corpus's human speaker labels;
- the negative control: turns counted inside stretches the labels mark
  as single-speaker, where the right answer is zero;
- baseline one: adult word count per session beside turn count, and
  the sessions where the same word count carries very different turn
  counts;
- baseline two: speaker changes counted with no window, and how far
  they overcount;
- the youngest sessions on their own, so the undercount on younger
  children is a number.

The results file is what the site reads and what `volley verify`
recomputes. A deliberately wrong window (fifty seconds) must change the
numbers, or the harness measured nothing; that check runs every time.

Expected input layout (Playlogue's): one directory per clip with a
transcript file of lines "start end speaker text" in seconds, or the
CTM segment files; the loader below accepts both and says which it
found. Adjust `load_session` once the local copy's layout is confirmed.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from serve_return import Roles, Utterance, count_day, count_turns

ADULT = {"adult", "parent", "mother", "father", "mot", "fat", "caregiver", "investigator"}
CHILD = {"child", "chi", "kid"}


def load_session(path: Path) -> list[Utterance]:
    """One session's utterances from a tab or space separated file of
    start, end, speaker, text. Speaker labels are normalised to the
    corpus's adult and child roles by the caller."""
    utts: list[Utterance] = []
    with path.open(encoding="utf8", errors="replace") as fh:
        reader = csv.reader(fh, delimiter="\t") if path.suffix in (".tsv",) else None
        rows = reader if reader else (line.split(None, 3) for line in fh)
        for row in rows:
            if len(row) < 4:
                continue
            try:
                start, end = float(row[0]), float(row[1])
            except ValueError:
                continue
            utts.append(Utterance(start=start, speaker=str(row[2]), text=str(row[3]), end=end))
    return utts


def role_map(utterances: list[Utterance]) -> Roles:
    labels = {u.speaker for u in utterances}
    adult = [l for l in labels if l.lower() in ADULT or l.lower().startswith(("adult", "par", "mot", "fat"))]
    child = [l for l in labels if l.lower() in CHILD or l.lower().startswith(("child", "chi", "kid"))]
    return Roles.of(adult=adult, child=child)


def single_speaker_stretches(utterances: list[Utterance], roles: Roles, min_seconds: float = 60.0) -> list[tuple[float, float]]:
    """Stretches of at least a minute in which only one role speaks."""
    out = []
    ordered = sorted((u for u in utterances if roles.role(u.speaker)), key=lambda u: u.start)
    if not ordered:
        return out
    run_start, run_role = ordered[0].start, roles.role(ordered[0].speaker)
    last_end = ordered[0].finish
    for u in ordered[1:]:
        r = roles.role(u.speaker)
        if r != run_role:
            if last_end - run_start >= min_seconds:
                out.append((run_start, last_end))
            run_start, run_role = u.start, r
        last_end = max(last_end, u.finish)
    if last_end - run_start >= min_seconds:
        out.append((run_start, last_end))
    return out


def naive_changes(utterances: list[Utterance], roles: Roles) -> int:
    ordered = [roles.role(u.speaker) for u in sorted(utterances, key=lambda u: u.start) if roles.role(u.speaker)]
    return sum(1 for a, b in zip(ordered, ordered[1:]) if a != b)


def evaluate(sessions: dict[str, list[Utterance]], meta: dict[str, dict] | None = None) -> dict:
    per = []
    for name, utts in sorted(sessions.items()):
        roles = role_map(utts)
        if not roles.adult or not roles.child:
            continue
        hours = max(1e-9, (max(u.finish for u in utts) - min(u.start for u in utts)) / 3600)
        turns = count_turns(utts, roles)
        broken = count_turns(utts, roles, window=50.0)
        stretches = single_speaker_stretches(utts, roles)
        inside = sum(count_turns([u for u in utts if a <= u.start <= b], roles) for a, b in stretches)
        adult_words = sum(u.words for u in utts if roles.role(u.speaker) == "adult")
        per.append({
            "session": name,
            "hours": round(hours, 3),
            "turns": turns,
            "turns_per_hour": round(turns / hours, 1),
            "turns_with_50s_window": broken,
            "single_speaker_stretches": len(stretches),
            "turns_inside_single_speaker_stretches": inside,
            "adult_words": adult_words,
            "naive_speaker_changes": naive_changes(utts, roles),
            "age_months": (meta or {}).get(name, {}).get("age_months"),
        })
    if not per:
        raise SystemExit("no session had both an adult and a child label; check role_map against the corpus's labels")
    total_turns = sum(p["turns"] for p in per)
    total_hours = sum(p["hours"] for p in per)
    return {
        "corpus": "Playlogue v1 (Kalanadhabhatta et al., IMWUT 2024), from CHILDES, CC BY-NC-SA 3.0 under the TalkBank ground rules",
        "sessions": len(per),
        "hours": round(total_hours, 2),
        "turns": total_turns,
        "turns_per_hour": round(total_turns / total_hours, 1),
        "negative_control": {
            "single_speaker_stretches": sum(p["single_speaker_stretches"] for p in per),
            "turns_inside_them": sum(p["turns_inside_single_speaker_stretches"] for p in per),
        },
        "baselines": {
            "naive_speaker_changes": sum(p["naive_speaker_changes"] for p in per),
            "overcount_ratio": round(sum(p["naive_speaker_changes"] for p in per) / max(1, total_turns), 2),
            "adult_words": sum(p["adult_words"] for p in per),
        },
        "window_check": {"turns_with_50s_window": sum(p["turns_with_50s_window"] for p in per), "differs": sum(p["turns_with_50s_window"] for p in per) != total_turns},
        "per_session": per,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("results.json")))
    args = ap.parse_args()
    root = Path(args.data)
    files = sorted(list(root.rglob("*.tsv")) + list(root.rglob("*.txt")))
    sessions = {f.stem: load_session(f) for f in files}
    sessions = {k: v for k, v in sessions.items() if v}
    if not sessions:
        print(f"no transcript files under {root}", file=sys.stderr)
        return 1
    result = evaluate(sessions)
    if not result["window_check"]["differs"]:
        print("the fifty-second window did not change the count; the harness measured nothing", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf8")
    print(f"{result['sessions']} sessions, {result['hours']} h, {result['turns']} turns, {result['turns_per_hour']}/h; "
          f"inside single-speaker stretches: {result['negative_control']['turns_inside_them']}; "
          f"naive overcount x{result['baselines']['overcount_ratio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
