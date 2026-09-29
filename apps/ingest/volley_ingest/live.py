"""Count turns as they happen.

`bee stream --json` emits one JSON object per line; `new-utterance`
events carry the speaker and the text. This keeps a five-second window
of role-labelled blocks in memory and prints one line per turn, with the
count so far and never the words. It is the terminal shot in the video
and the thing a parent runs once to see that it is real.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

from serve_return import WINDOW_SECONDS

from .bee import BeeCli, speaker_label
from .days import roles_for
from .household import Household


def _utterance_from_event(event: dict) -> tuple[str | None, str, float] | None:
    if event.get("type") not in (None, "new-utterance") and event.get("event") not in (None, "new-utterance"):
        return None
    payload = event.get("utterance") or event.get("data", {}).get("utterance") or event.get("payload", {}).get("utterance")
    if not isinstance(payload, dict):
        return None
    text = str(payload.get("text") or "").strip()
    if not text:
        return None
    spoken = payload.get("spoken_at")
    when = spoken / 1000.0 if isinstance(spoken, (int, float)) and spoken > 1e11 else time.time()
    return speaker_label(payload.get("speaker")), text, when


def run(cli: BeeCli, h: Household, seconds: int = 600, lines=None) -> int:
    roles = roles_for(h)
    proc = None
    if lines is None:
        proc = subprocess.Popen(cli._argv("stream", "--json"), stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        lines = proc.stdout
    print(f"counting turns with {h.child_name or 'your child'} for {seconds}s; words are not printed")
    last_role, last_end, turns = None, None, 0
    deadline = time.monotonic() + seconds
    try:
        for line in lines:
            if time.monotonic() > deadline:
                break
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            got = _utterance_from_event(event)
            if not got:
                continue
            speaker, text, when = got
            role = roles.role(speaker or "")
            if role is None:
                continue
            words = len(text.split())
            end = when + max(1.0, words / 2.5)
            if last_role and role != last_role and last_end is not None and when - last_end <= WINDOW_SECONDS:
                turns += 1
                print(f"  turn {turns}: {last_role} then {role}, {when - last_end:.1f}s later")
            last_role, last_end = role, end
    finally:
        if proc:
            proc.terminate()
    print(f"{turns} turns")
    return 0
