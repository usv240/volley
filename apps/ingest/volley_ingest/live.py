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


def run(cli: BeeCli, h: Household, seconds: int = 600, lines=None, nudge: bool = False, speak: bool = False,
        clock=None, poll_seconds: float = 30.0, say=None) -> int:
    """Count turns as they happen. With ``nudge``, also watch the family's
    usual best hour and put one sentence into the Bee if it goes quiet
    (nudge.py). A quiet hour has no events, so the stream is read on a
    thread and the rule is checked every ``poll_seconds`` as well as on
    every utterance. ``clock`` returns local time; tests replace it."""
    import queue
    import threading
    from datetime import datetime, timedelta, timezone

    from . import nudge as nd

    roles = roles_for(h)
    proc = None
    if lines is None:
        proc = subprocess.Popen(cli._argv("stream", "--json"), stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        lines = proc.stdout
    clock = clock or (lambda: datetime.now(timezone.utc) + timedelta(hours=h.tz_offset_hours))
    usual = nd.usual_best_hour() if nudge else None
    print(f"counting turns with {h.child_name or 'your child'} for {seconds}s; words are not printed")
    if nudge:
        if usual is None:
            print("no counted days yet, so no usual hour to watch; run volley today on a few days first")
        else:
            print(f"watching {usual.hour:02d}:00, usually your best hour ({usual.turns:g} turns on average over {usual.days} days)")
    if nudge and not h.write_reminders_to_bee:
        print("reminders are off in setup, so a nudge would only be printed: volley setup --reminders yes")

    events: "queue.Queue[str | None]" = queue.Queue()

    def reader():
        for line in lines:
            events.put(line)
        events.put(None)

    threading.Thread(target=reader, daemon=True).start()
    last_role, last_end, turns = None, None, 0
    by_hour: dict[tuple[str, int], int] = {}

    def check() -> None:
        now = clock()
        date = now.date().isoformat()
        if not nd.should_nudge(now, usual, by_hour.get((date, now.hour), 0), nd.nudged_today(date)):
            return
        text = nd.message(h.child_name)
        print(f"  nudge at {now:%H:%M}: {text}")
        if h.write_reminders_to_bee:
            cli.todo_create(text, nd.due_in_a_minute())
            print("  placed in your Bee, due in a minute")
        if speak:
            (say or nd.say)(text)
        nd.mark_nudged(date)

    deadline = time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            try:
                line = events.get(timeout=poll_seconds)
            except queue.Empty:
                if nudge:
                    check()
                continue
            if line is None:
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
                now = clock()
                key = (now.date().isoformat(), now.hour)
                by_hour[key] = by_hour.get(key, 0) + 1
                print(f"  turn {turns}: {last_role} then {role}, {when - last_end:.1f}s later")
            last_role, last_end = role, end
            if nudge:
                check()
        if nudge:
            check()
    finally:
        if proc:
            proc.terminate()
    print(f"{turns} turns")
    return 0
