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
        name = Path(fpath).stem
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
    if not result["window_check"]["differs"]:
        print("the fifty-second window did not change the count; the harness measured nothing", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf8")
    print(f"{result['sessions']} sessions, {result['hours']} h, {result['turns']} turns, {result['turns_per_hour']}/h; "
          f"inside single-speaker stretches: {result['negative_control']['turns_inside_them']}; "
          f"naive overcount x{result['baselines']['overcount_ratio']}; skipped {len(skipped)} untimed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
