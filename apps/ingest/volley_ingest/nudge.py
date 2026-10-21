"""Coaching in the moment: a nudge on the Bee while the hour is still yours.

The nightly note is about tomorrow. This is about now. From the days
already counted, Volley knows the hour this family usually talks most.
`volley live --nudge` watches the Bee's live stream; if that hour is a
third gone and has held a quarter of its usual turns or fewer, it puts
one sentence into the parent's Bee as a reminder due in a minute, and,
with `--say`, speaks it through a speaker in the room (a stand-in for an
Echo). Once a day at most, only with the reminder consent given in
setup, and the sentence carries no number and no judgement.

The rule is deliberately simple and written down: it can be wrong in
only two ways, a nudge on a day the family is out, which costs one
ignored reminder, or none on a day the count misreads, which costs
nothing. The words of the stream are counted and dropped as in
`volley live`; nothing here keeps them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .household import home

# A third of the hour gone, a quarter of the usual turns or fewer.
CHECK_AFTER_MINUTES = 20
QUIET_FRACTION = 0.25
# Below this many usual turns in the best hour, there is no habit to keep.
MIN_USUAL_TURNS = 4


@dataclass(frozen=True)
class Usual:
    hour: int
    turns: float
    days: int


def usual_best_hour(counts_dir: Path | None = None, days: int = 7) -> Usual | None:
    """The hour with the most turns on average over the last counted days,
    from the counts files `volley today` writes. Hours with no child are
    left out of the average rather than counted as zero."""
    d = counts_dir or home() / "counts"
    files = sorted(d.glob("*.json"))[-days:] if d.exists() else []
    totals: dict[int, list[int]] = {}
    for f in files:
        day = json.loads(f.read_text(encoding="utf8"))
        for h in day.get("hours", []):
            if h.get("utterances_child", 0) > 0:
                totals.setdefault(int(h["hour"]), []).append(int(h.get("turns", 0)))
    if not totals:
        return None
    hour, seen = max(totals.items(), key=lambda kv: (sum(kv[1]) / len(kv[1]), -kv[0]))
    return Usual(hour=hour, turns=round(sum(seen) / len(seen), 1), days=len(files))


def should_nudge(now_local: datetime, usual: Usual | None, turns_this_hour: int, already_today: bool) -> bool:
    if usual is None or already_today or usual.turns < MIN_USUAL_TURNS:
        return False
    if now_local.hour != usual.hour or now_local.minute < CHECK_AFTER_MINUTES:
        return False
    return turns_this_hour <= QUIET_FRACTION * usual.turns


def message(child: str | None) -> str:
    who = child or "your child"
    return f"This is usually your best hour with {who}. A question about their day would start one."


def nudged_today(date: str) -> bool:
    return (home() / "nudges" / f"{date}.sent").exists()


def mark_nudged(date: str) -> None:
    d = home() / "nudges"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{date}.sent").write_text("", encoding="utf8")


def due_in_a_minute(now_utc: datetime | None = None) -> str:
    now_utc = now_utc or datetime.now(timezone.utc)
    return (now_utc + timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def say(text: str) -> None:
    """Speak through this computer's speaker with Amazon Polly; the room
    hears what an Echo would say. Lazy imports: the tests never speak."""
    import os
    import platform
    import subprocess
    import tempfile
    import wave

    import boto3

    pcm = boto3.client("polly", region_name=os.environ.get("AWS_REGION", "us-east-1")).synthesize_speech(
        Text=text, OutputFormat="pcm", SampleRate="16000", VoiceId="Joanna", Engine="neural")["AudioStream"].read()
    path = Path(tempfile.gettempdir()) / "volley-nudge.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm)
    if platform.system() == "Windows":
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME)
    else:
        subprocess.run(["afplay" if platform.system() == "Darwin" else "aplay", str(path)], check=False)
