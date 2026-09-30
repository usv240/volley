"""The count on any media-linked CHILDES corpus, in CHAT format.

    python harness/childes/run.py --data Gleason.zip [--out harness/childes/results.json]

TalkBank moved every corpus download behind a free login on or before
2026-09-30, so no corpus is fetched here; point --data at a zip or a
directory of .cha files accepted under the TalkBank ground rules. Any
corpus whose utterances carry time bullets works; the ones that do not
are skipped and named, because the five-second rule needs the clock.

Why CHAT and not only Playlogue: Playlogue is one gated dataset on one
site. CHAT is the format of the whole database, and corpora such as
Gleason (24 families, children aged 2;1 to 5;2, mother-child,
father-child and dinner, audio-linked) sit inside Volley's talking-age
range where Playlogue's preschool play does. The evaluation is the one
the Playlogue harness defines, unchanged, so the two publish the same
numbers in the same shape: turns per hour by the corpus's human speaker
labels; zero inside single-speaker stretches; the naive speaker-change
count and the adult word count beside it; and the fifty-second window
check that proves the harness measured something.

Roles: CHI is the child. Every other participant with a caregiver role
in the header (Mother, Father, Grandmother, Adult, Investigator and so
on) is an adult. Siblings and other children are neither, which is the
same choice the count makes on the device: only the two mapped people
count. Ages are read from the header when present.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from pylangacq import CHAT

from serve_return import Roles, Utterance


def playlogue_harness():
    """The Playlogue harness, loaded by path so the two scripts can share
    a filename without sharing a module name."""
    spec = importlib.util.spec_from_file_location("playlogue_run", Path(__file__).resolve().parents[1] / "playlogue" / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ADULT_ROLES = {"mother", "father", "grandmother", "grandfather", "adult", "investigator", "teacher", "caregiver", "aunt", "uncle", "babysitter", "parent", "nurse"}
CHILD_CODES = {"CHI"}


def load(path: Path) -> tuple[dict[str, list[Utterance]], dict[str, dict], list[str]]:
    """Sessions keyed by file, with age metadata and the files skipped for
    having no time marks."""
    reader = CHAT.from_zip(str(path), strict=False) if path.suffix == ".zip" else CHAT.from_dir(str(path), strict=False)
    sessions: dict[str, list[Utterance]] = {}
    meta: dict[str, dict] = {}
    skipped: list[str] = []
    files = reader.file_paths
    per_file = reader.utterances(by_file=True)
    headers = reader.headers()
    ages = reader.ages()
    for fpath, utts, header, age in zip(files, per_file, headers, ages):
        # The same child appears under Mother, Father and Dinner, so the
        # directory is part of the name or two sessions in three are lost.
        name = "/".join(Path(fpath).parts[-2:]).removesuffix(".cha")
        roles_by_code = {p.code: (p.role or "").lower() for p in (header.participants or [])}
        rows: list[Utterance] = []
        for u in utts:
            if not u.time_marks:
                continue
            start_ms, end_ms = u.time_marks
            words = [t.word for t in u.tokens if t.word and t.word[0].isalnum()]
            if not words:
                continue
            code = u.participant
            if code in CHILD_CODES:
                speaker = "CHI"
            elif roles_by_code.get(code, "") in ADULT_ROLES or code in ("MOT", "FAT", "ADU", "INV"):
                speaker = "ADULT:" + code
            else:
                speaker = "OTHER:" + code
            rows.append(Utterance(start=start_ms / 1000.0, speaker=speaker, text=" ".join(words), end=end_ms / 1000.0))
        if not rows:
            skipped.append(name)
            continue
        sessions[name] = rows
        meta[name] = {"age_months": round(age.in_months(), 1) if age is not None else None}
    return sessions, meta, skipped


def roles_for(utts: list[Utterance]) -> Roles:
    labels = {u.speaker for u in utts}
    return Roles.of(adult=[l for l in labels if l.startswith("ADULT:")], child=[l for l in labels if l == "CHI"])


def reply_gaps(sessions: dict[str, list[Utterance]]) -> list[float]:
    """Seconds from one role finishing to the other starting, at every
    labelled alternation. The window's work is visible only here."""
    gaps: list[float] = []
    for utts in sessions.values():
        roles = roles_for(utts)
        if not roles.adult or not roles.child:
            continue
        ordered = sorted((u for u in utts if roles.role(u.speaker)), key=lambda u: u.start)
        for a, b in zip(ordered, ordered[1:]):
            if roles.role(a.speaker) != roles.role(b.speaker):
                gaps.append(round(b.start - a.finish, 3))
    return sorted(gaps)


def spearman(a: list[float], b: list[float]) -> float:
    ra = {v: i for i, v in enumerate(sorted(a))}
    rb = {v: i for i, v in enumerate(sorted(b))}
    n = len(a)
    d = sum((ra[x] - rb[y]) ** 2 for x, y in zip(a, b))
    return 1 - 6 * d / (n * (n * n - 1))


def summarise(result: dict) -> dict:
    """The numbers the site prints, derived from the results file alone so
    a test can re-derive them and refuse a stale page."""
    import statistics

    per = result["per_session"]
    tph = sorted(p["turns_per_hour"] for p in per)
    by_situation = {}
    for p in per:
        by_situation.setdefault(p["session"].split("/")[0], []).append(p)
    young = [p for p in per if p["age_months"] and p["age_months"] < 36]
    older = [p for p in per if p["age_months"] and p["age_months"] >= 36]

    def rate(group):
        return round(sum(x["turns"] for x in group) / max(1e-9, sum(x["hours"] for x in group)), 1)

    pair = None
    for a in per:
        for b in per:
            if a is b or not a["adult_words"]:
                continue
            if abs(a["adult_words"] - b["adult_words"]) / a["adult_words"] < 0.05 and a["turns"] > b["turns"]:
                ratio = a["turns"] / max(1, b["turns"])
                if pair is None or ratio > pair["ratio"]:
                    pair = {"ratio": round(ratio, 2), "more": {"session": a["session"], "adult_words": a["adult_words"], "turns": a["turns"]},
                            "fewer": {"session": b["session"], "adult_words": b["adult_words"], "turns": b["turns"]}}
    gaps = result.get("reply_gaps") or {}
    return {
        "corpus": result["corpus"],
        "sessions": result["sessions"],
        "hours": result["hours"],
        "turns": result["turns"],
        "turns_per_hour": result["turns_per_hour"],
        "turns_per_hour_min": tph[0],
        "turns_per_hour_median": round(statistics.median(tph), 1),
        "turns_per_hour_max": tph[-1],
        "by_situation": {k: {"sessions": len(v), "hours": round(sum(x["hours"] for x in v), 2), "turns_per_hour": rate(v)} for k, v in sorted(by_situation.items())},
        "under_36_months": {"sessions": len(young), "turns_per_hour": rate(young)},
        "from_36_months": {"sessions": len(older), "turns_per_hour": rate(older)},
        "single_speaker_stretches": result["negative_control"]["single_speaker_stretches"],
        "turns_inside_them": result["negative_control"]["turns_inside_them"],
        "naive_speaker_changes": result["baselines"]["naive_speaker_changes"],
        "alternations_within_window_percent": gaps.get("within_window_percent"),
        "median_gap_seconds": gaps.get("median_seconds"),
        "turns_with_50s_window": result["window_check"]["turns_with_50s_window"],
        "adult_words": result["baselines"]["adult_words"],
        "spearman_adult_words_vs_turns": round(spearman([p["adult_words"] for p in per], [p["turns"] for p in per]), 2),
        "same_words_different_turns": pair,
        "files_without_time_marks": len(result.get("files_without_time_marks", [])),
    }


SITE_COPY = Path(__file__).resolve().parents[2] / "apps" / "web" / "src" / "data" / "corpus.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--corpus", default=None, help="how to name the corpus in the results; defaults to the file or directory name")
    ap.add_argument("--out", default=str(Path(__file__).with_name("results.json")))
    args = ap.parse_args()
    src = Path(args.data)
    sessions, meta, skipped = load(src)
    if not sessions:
        print(f"no timed utterances under {src}; {len(skipped)} files had no time marks", file=sys.stderr)
        return 1
    playlogue = playlogue_harness()
    playlogue.role_map = roles_for  # the corpus's codes, not Playlogue's labels
    result = playlogue.evaluate(sessions, meta)
    result["corpus"] = args.corpus or f"CHILDES {src.stem}, CHAT format, under the TalkBank ground rules"
    result["files_without_time_marks"] = skipped
    gaps = reply_gaps(sessions)
    within = sum(1 for g in gaps if g <= 5.0)
    result["reply_gaps"] = {
        "alternations": len(gaps),
        "within_window": within,
        "within_window_percent": round(100 * within / max(1, len(gaps)), 1),
        "median_seconds": gaps[len(gaps) // 2] if gaps else None,
        "p90_seconds": gaps[int(0.9 * len(gaps))] if gaps else None,
        "note": "Forced-aligner timing is contiguous, so most gaps are zero by construction; this corpus tests the labels and the alternation, not the window.",
    }
    if not result["window_check"]["differs"]:
        print("the fifty-second window did not change the count; the harness measured nothing", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf8")
    SITE_COPY.write_text(json.dumps(summarise(result), indent=1), encoding="utf8")
    print(f"{result['sessions']} sessions, {result['hours']} h, {result['turns']} turns, {result['turns_per_hour']}/h; "
          f"inside single-speaker stretches: {result['negative_control']['turns_inside_them']}; "
          f"naive overcount x{result['baselines']['overcount_ratio']}; skipped {len(skipped)} untimed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
