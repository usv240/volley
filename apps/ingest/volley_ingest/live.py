"""Count turns as they happen.

`bee stream --json` emits one JSON object per line; `new-utterance`
events carry the speaker and the text. This keeps a five-second window
of role-labelled blocks in memory and prints one line per turn, with the
count so far and never the words. It is the terminal shot in the video
and the thing a parent runs once to see that it is real.
"""

from __future__ import annotations

import json
from pathlib import Path
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
        clock=None, poll_seconds: float = 30.0, say=None, record: str | None = None) -> int:
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
    # Blind households: every speaker arrives "Unknown", so roles are read
    # from the hour's lines together, as `volley today` reads a day, and the
    # hour's count is recomputed with the shipped scale. The lines live in
    # memory for the hour only and are counted, never printed or kept.
    hour_lines: dict[tuple[str, int], list] = {}
    if h.blind:
        from serve_return import Roles, Utterance, count_turns
        from serve_return.blind import childes_model, relabel

        model = childes_model()
        blind_roles = Roles.of(adult=["adult"], child=["child"])

    started = clock()
    log: dict = {"started": started.isoformat(timespec="seconds"), "seconds": seconds, "blind": h.blind,
                 "usual": None if usual is None else {"hour": usual.hour, "turns": usual.turns, "days": usual.days},
                 "rule": {"check_after_minutes": nd.CHECK_AFTER_MINUTES, "quiet_fraction": nd.QUIET_FRACTION},
                 "checks": [], "nudge": None, "words_kept": 0}

    def check() -> None:
        now = clock()
        date = now.date().isoformat()
        # Only an hour heard from its start can be called quiet: started at
        # half past, the count so far would be zero and every hour would look
        # quiet. Five minutes of grace for starting just after the hour.
        if started > now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=5):
            return
        so_far = by_hour.get((date, now.hour), 0)
        if usual is not None and now.hour == usual.hour and (not log["checks"] or log["checks"][-1]["minute"] != now.minute):
            log["checks"].append({"minute": now.minute, "turns_this_hour": so_far})
        if not nd.should_nudge(now, usual, so_far, nd.nudged_today(date)):
            return
        text = nd.message(h.child_name)
        print(f"  nudge at {now:%H:%M}: {text}")
        placed = None
        if h.write_reminders_to_bee:
            placed = cli.todo_create(text, nd.due_in_a_minute())
            print("  placed in your Bee, due in a minute")
        log["nudge"] = {"at": now.isoformat(timespec="seconds"), "turns_this_hour": so_far, "text": text,
                        "placed_in_bee": bool(h.write_reminders_to_bee),
                        "todo_id": placed.get("id") if isinstance(placed, dict) else None, "spoken": bool(speak)}
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
            if h.blind:
                now = clock()
                key = (now.date().isoformat(), now.hour)
                for k in [k for k in hour_lines if k != key]:
                    del hour_lines[k]
                lines_now = hour_lines.setdefault(key, [])
                lines_now.append(Utterance(when, "Unknown", text, when + max(1.0, len(text.split()) / 2.5)))
                before = by_hour.get(key, 0)
                by_hour[key] = round(count_turns(relabel(lines_now, model), blind_roles) * model.turn_scale)
                if by_hour[key] > before:
                    turns += by_hour[key] - before
                    print(f"  {by_hour[key]} turns this hour")
                if nudge:
                    check()
                continue
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
    if record:
        import json as _json

        log["turns_counted"] = turns
        Path(record).parent.mkdir(parents=True, exist_ok=True)
        Path(record).write_text(_json.dumps(log, indent=1), encoding="utf-8")
        print(f"wrote {record}: counts and times only")
    return 0
