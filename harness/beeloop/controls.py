"""Negative controls on the Bee: three stretches where the true count is zero.

    python harness/beeloop/controls.py make     # voice them with Polly
    python harness/beeloop/controls.py play     # play them to the band, about 9 minutes
    python harness/beeloop/controls.py score    # once the Bee has written the sessions down

A turn counter that finds turns everywhere is useless, and a label-free
one is most at risk of it: with every speaker "Unknown", two adults
talking can look like a parent and a child. So the band hears, in order:

  adults     the mother's and father's lines from a real CHILDES family
             dinner, the child's lines left out, voiced by two adult
             Polly voices at their original timing
  silence    three minutes of nothing
  one voice  a different family's father, every line back to back in one
             adult voice, the way a podcast plays to an empty room

No child speaks in any of them, so every adult-child turn Volley reports
is a false one. The scoring model is the one score.py uses: the same
training with every session of both families left out, so it never saw
these voices' words. Only counts are written (controls.json); the corpus
audio is not published.

Corpus: CHILDES Gleason (doi 10.21415/T5101R), used under the TalkBank
ground rules. No person is recorded.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "out"
sys.path.insert(0, str(REPO / "packages" / "serve-return"))
sys.path.insert(0, str(REPO / "apps" / "ingest"))

from serve_return import Roles, Utterance, count_turns  # noqa: E402

RATE = 16000
SECONDS = 180
SILENCE = 180
DINNER = "Dinner/charlie"
MONOLOGUE = "Father/susan"
ADULTS = {"ADULT:MOT": "Joanna", "ADULT:FAT": "Matthew"}
ROLES = Roles.of(adult=["adult"], child=["child"])


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def corpus():
    m = _load(REPO / "harness" / "childes" / "run.py", "childes_run")
    sessions, _meta, _skipped = m.load(REPO / "harness" / "childes" / "data" / "Gleason.zip")
    return sessions


def _pcm(polly, text: str, voice: str) -> bytes:
    res = polly.synthesize_speech(Text=text, OutputFormat="pcm", SampleRate=str(RATE), VoiceId=voice, Engine="neural")
    return res["AudioStream"].read()


def _write(name: str, pcm: bytes) -> None:
    with wave.open(str(OUT / f"{name}.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(pcm)


def make() -> int:
    import boto3

    sessions = corpus()
    polly = boto3.client("polly", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    OUT.mkdir(exist_ok=True)

    # Adults: the original timing, the child's lines simply absent.
    adults = [u for u in sessions[DINNER] if u.speaker in ADULTS]
    t0 = adults[0].start
    adults = [u for u in adults if u.start - t0 <= SECONDS]
    pcm, cursor = bytearray(), 0.0
    for u in adults:
        at = max(u.start - t0, cursor + 0.15)
        pad = int((at - len(pcm) / 2 / RATE) * RATE) * 2
        if pad > 0:
            pcm += b"\x00" * pad
        pcm += _pcm(polly, u.text, ADULTS[u.speaker])
        cursor = len(pcm) / 2 / RATE
    _write("adults", bytes(pcm))
    adults_s = cursor

    # One voice: back to back, as continuous as a person reading aloud.
    lines = [u for u in sessions[MONOLOGUE] if u.speaker == "ADULT:FAT"]
    pcm, cursor = bytearray(), 0.0
    for u in lines:
        if cursor >= SECONDS:
            break
        pcm += _pcm(polly, u.text, "Matthew") + b"\x00" * int(0.4 * RATE) * 2
        cursor = len(pcm) / 2 / RATE
    _write("onevoice", bytes(pcm))

    manifest = {"corpus": "CHILDES Gleason, doi 10.21415/T5101R",
                "segments": [{"name": "adults", "session": DINNER, "utterances": len(adults), "seconds": round(adults_s, 1)},
                             {"name": "silence", "seconds": SILENCE},
                             {"name": "onevoice", "session": MONOLOGUE, "seconds": round(cursor, 1)}]}
    (OUT / "controls.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"adults {adults_s:.0f} s ({len(adults)} lines), silence {SILENCE} s, one voice {cursor:.0f} s")
    return 0


def play() -> int:
    import winsound

    manifest = json.loads((OUT / "controls.json").read_text(encoding="utf-8"))
    for seg in manifest["segments"]:
        seg["played_at"] = round(time.time(), 3)
        print(f"{time.strftime('%H:%M:%S')} {seg['name']} ({seg['seconds']} s)", flush=True)
        if seg["name"] == "silence":
            time.sleep(seg["seconds"])
        else:
            winsound.PlaySound(str(OUT / f"{seg['name']}.wav"), winsound.SND_FILENAME)
    (OUT / "controls.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{time.strftime('%H:%M:%S')} done")
    return 0


def _bee(args: str) -> dict:
    out = subprocess.run("bee " + args, shell=True, capture_output=True).stdout.decode("utf-8", "replace")
    return json.loads(out)


def score() -> int:
    from serve_return.blind import RoleModel, relabel
    from volley_ingest.bee import normalize_conversation

    manifest = json.loads((OUT / "controls.json").read_text(encoding="utf-8"))
    segs = manifest["segments"]
    if "played_at" not in segs[0]:
        print("play them first: python harness/beeloop/controls.py play")
        return 2
    first, last = segs[0]["played_at"], segs[-1]["played_at"] + segs[-1]["seconds"]

    rows = _bee("conversations list --limit 15 --json")
    rows = rows.get("conversations", rows)
    utts, sessions = [], []
    for c in rows:
        s, e = c["start_time"] / 1000, (c.get("end_time") or c["start_time"]) / 1000
        if e < first - 60 or s > last + 60:
            continue
        raw = _bee(f"conversations get {c['id']} --json")
        sessions.append({"id": c["id"], "state": raw.get("conversation", raw).get("state")})
        for u in normalize_conversation(raw):
            if u.start_s is not None:
                utts.append(Utterance(u.start_s, "Unknown", u.text, u.end_s))
    utts.sort(key=lambda u: u.start)

    blind_run = _load(REPO / "harness" / "blind" / "run.py", "blind_run")
    full, _m, _s = blind_run.childes().load(REPO / "harness" / "childes" / "data" / "Gleason.zip")
    left_out = {DINNER.split("/")[-1], MONOLOGUE.split("/")[-1]}
    others = [n for n in full if n.split("/")[-1] not in left_out]
    model = RoleModel().fit([blind_run.labelled(full[n]) for n in others])
    model.turn_scale = blind_run.learn_scale(full, others)

    out = []
    for seg in segs:
        # The Bee's clock ran within two minutes of this one on the first
        # run; a minute either side keeps the three windows apart.
        a, b = seg["played_at"] - 30, seg["played_at"] + seg["seconds"] + 30
        inside = [u for u in utts if a <= u.start <= b]
        raw = count_turns(relabel(inside, model), ROLES) if inside else 0
        out.append({"name": seg["name"], "seconds": seg["seconds"], "turns_true": 0,
                    "utterances_bee": len(inside), "turns_blind_uncalibrated": raw,
                    "turns_blind": round(raw * model.turn_scale)})
    result = {"corpus": manifest["corpus"], "blind_model": f"trained on every Gleason family except {sorted(left_out)}",
              "turn_scale": model.turn_scale, "bee_sessions": sessions, "controls": out}
    (HERE / "controls.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for r in out:
        print(f"  {r['name']:9} {r['seconds']:6} s  Bee utterances {r['utterances_bee']:4}  false turns {r['turns_blind']}")
    print(f"wrote {HERE / 'controls.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["make", "play", "score"])
    return {"make": make, "play": play, "score": score}[ap.parse_args().step]()


if __name__ == "__main__":
    sys.exit(main())
