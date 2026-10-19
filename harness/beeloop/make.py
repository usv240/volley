"""A real parent-child conversation, voiced, timed, and played to a Bee.

    python harness/beeloop/make.py --session Mother/<child> --seconds 180
    python harness/beeloop/make.py --play            # play it; the band records

Volley has to work on a Bee, and two things stand between a conversation
and a turn count there: the Bee labels every speaker "Unknown", and the
Bee decides where one utterance ends and the next begins. The first is
measured on CHILDES in harness/blind. The second can only be measured on
the device. So this takes a stretch of a real, labelled CHILDES session,
voices each utterance with Amazon Polly (an adult voice for the parent, a
child's voice for the child), places each at its original start time,
and plays it to the band. Nothing here involves a person: the words are a
research corpus's, the voices are synthetic, and only counts are kept.

The manifest records who spoke when, by this computer's clock, so the
true turn count of exactly what the band heard is known. harness/beeloop
/score.py then reads the Bee's own transcript of it and compares.

Corpus: CHILDES Gleason (doi 10.21415/T5101R), used under the TalkBank
ground rules; the audio made here is not published.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "out"
sys.path.insert(0, str(REPO / "packages" / "serve-return"))

from serve_return import Roles, Utterance, count_turns  # noqa: E402

RATE = 16000
VOICES = {"child": "Ivy", "ADULT:MOT": "Joanna", "ADULT:FAT": "Matthew"}
GAP_MIN = 0.15


def childes():
    spec = importlib.util.spec_from_file_location("childes_run", REPO / "harness" / "childes" / "run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pick(sessions: dict, name: str | None, seconds: float) -> tuple[str, list]:
    def stretch(us):
        us = [u for u in us if u.speaker == "CHI" or u.speaker in ("ADULT:MOT", "ADULT:FAT")]
        if not us:
            return []
        t0 = us[0].start
        return [u for u in us if u.start - t0 <= seconds]

    if name:
        return name, stretch(sessions[name])
    # The densest stretch of back-and-forth among the mother sessions.
    best = max((n for n in sessions if n.startswith("Mother/")),
               key=lambda n: count_turns(stretch(sessions[n]), Roles.of(adult=["ADULT:MOT", "ADULT:FAT"], child=["CHI"])))
    return best, stretch(sessions[best])


def synth(polly, text: str, voice: str) -> bytes:
    res = polly.synthesize_speech(Text=text, OutputFormat="pcm", SampleRate=str(RATE), VoiceId=voice, Engine="neural")
    return res["AudioStream"].read()


def make(name: str | None, seconds: float) -> int:
    import boto3

    sessions, _m, _s = childes().load(REPO / "harness" / "childes" / "data" / "Gleason.zip")
    name, us = pick(sessions, name, seconds)
    polly = boto3.client("polly", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    OUT.mkdir(exist_ok=True)
    t0 = us[0].start
    cursor = 0.0
    pcm = bytearray()
    rows = []
    for u in us:
        role = "child" if u.speaker == "CHI" else "adult"
        voice = VOICES["child"] if role == "child" else VOICES.get(u.speaker, "Joanna")
        audio = synth(polly, u.text, voice)
        at = max(u.start - t0, cursor + GAP_MIN)
        pad = int((at - len(pcm) / 2 / RATE) * RATE) * 2
        if pad > 0:
            pcm += b"\x00" * pad
        start = len(pcm) / 2 / RATE
        pcm += audio
        end = len(pcm) / 2 / RATE
        cursor = end
        rows.append({"role": role, "start": round(start, 3), "end": round(end, 3), "words": len(u.text.split())})
    with wave.open(str(OUT / "conversation.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(bytes(pcm))
    played = [Utterance(r["start"], r["role"], "x " * r["words"], r["end"]) for r in rows]
    gold = count_turns(played, Roles.of(adult=["adult"], child=["child"]))
    manifest = {"session": name, "corpus": "CHILDES Gleason, doi 10.21415/T5101R", "utterances": len(rows),
                "seconds": round(cursor, 1), "turns_true": gold, "rows": rows}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{name}: {len(rows)} utterances, {cursor:.0f} s, {gold} true turns; wrote {OUT / 'conversation.wav'}")
    return 0


def play() -> int:
    import winsound

    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    began = time.time()
    winsound.PlaySound(str(OUT / "conversation.wav"), winsound.SND_FILENAME)
    manifest["played_at"] = round(began, 3)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"played {manifest['seconds']} s at {time.strftime('%H:%M:%S', time.localtime(began))}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session")
    ap.add_argument("--seconds", type=float, default=180)
    ap.add_argument("--play", action="store_true")
    a = ap.parse_args()
    return play() if a.play else make(a.session, a.seconds)


if __name__ == "__main__":
    sys.exit(main())
