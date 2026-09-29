"""The command a parent runs.

    volley status              is the Bee installed and signed in, and is a household set up
    volley setup               which label is you, which is your child, and where the counts go
    volley today               count the day, show it, post the counts, write tomorrow's reminder
    volley evidence            write a publishable record that live Bee data flowed, with no words
    volley live                count turns as they happen, from the Bee's live stream
    volley verify              recompute every published number from committed inputs

`today` is the product. It reads the transcript on this machine, counts,
prints the day, and lets the words go. The only files it writes are the
cursor and the counts. A test runs it against a transcript of names in a
temporary home and asserts nothing else appears on disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from serve_return import DayCounts

from .bee import BeeCli, BeeCliError, BeeNotAuthenticated, CursorStore, normalize_conversation, with_utterances
from .coach import note
from .days import count_days, words_in
from .household import Household, home
from .reminder import write as write_reminder


def _hour(h: int) -> str:
    return f"{h:02d}:00"


def render_day(day: DayCounts, child: str | None) -> str:
    who = child or "your child"
    lines = [f"{day.date}: {day.turns} turns with {who}"]
    if day.hours:
        width = max(1, max(h.turns for h in day.hours))
        for h in day.hours:
            bar = "#" * int(round(24 * h.turns / width)) if h.turns else ""
            away = "" if h.utterances_child else "  (away)"
            lines.append(f"  {_hour(h.hour)}  {h.turns:3d}  {bar}{away}")
    if day.best_hour is not None:
        lines.append(f"  best hour {_hour(day.best_hour)}; longest exchange {day.longest_volley} turns; "
                     f"{day.questions_adult} questions asked")
    lines.append(f"  {day.words_discarded} words read and thrown away")
    return "\n".join(lines)


def _post(h: Household, days: list[DayCounts]) -> str | None:
    """Counts only, to the household's API, if one is configured."""
    if not h.api_url or not h.api_key:
        return None
    import urllib.request

    body = json.dumps({"days": [d.to_dict() for d in days]}).encode("utf8")
    req = urllib.request.Request(
        h.api_url.rstrip("/") + "/v1/days",
        data=body,
        headers={"content-type": "application/json", "x-api-key": h.api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:  # noqa: S310
        return f"{res.status}"


def cmd_status(cli: BeeCli) -> int:
    print(cli.status_text() if cli.installed() else "bee is not installed: npm install -g @beeai/cli")
    h = Household.load()
    print("household:", f"parent {h.parent_labels}, child {h.child_labels}" if h else "not set up; run volley setup")
    return 0


def cmd_setup(cli: BeeCli, args) -> int:
    """Labels come from what the Bee has actually produced, so the parent
    picks from real names rather than typing a guess."""
    h = Household.load() or Household()
    if args.parent:
        h.parent_labels = [args.parent]
    if args.child:
        h.child_labels = [args.child]
    if args.child_name is not None:
        h.child_name = args.child_name or None
    if args.tz is not None:
        h.tz_offset_hours = args.tz
    if args.api_url:
        h.api_url = args.api_url
    if args.api_key:
        h.api_key = args.api_key
    if args.reminders is not None:
        h.write_reminders_to_bee = args.reminders
    if not (args.parent and args.child):
        try:
            rows = cli.conversations_list(limit=10)
            rows = rows.get("conversations", rows) if isinstance(rows, dict) else rows
            seen: dict[str, int] = {}
            for raw in with_utterances(cli, rows, limit=5):
                for u in normalize_conversation(raw):
                    seen[u.speaker or "?"] = seen.get(u.speaker or "?", 0) + 1
            print("labels the Bee has produced this week:", ", ".join(f"{k} ({v})" for k, v in sorted(seen.items(), key=lambda kv: -kv[1])) or "none yet")
            print("set them with: volley setup --parent <label> --child <label>")
        except BeeCliError as err:
            print(str(err))
    print("recording other people is your responsibility under local law; the child's words never leave this machine")
    p = h.save()
    print(f"saved {p}")
    return 0


def cmd_today(cli: BeeCli, args) -> int:
    h = Household.load()
    if h is None or not h.parent_labels or not h.child_labels:
        print("run volley setup first: it needs to know which label is you and which is your child")
        return 2
    cursors = CursorStore(str(home() / ".bee-cursor"))
    if args.now:
        payload = cli.now()
        rows = payload.get("conversations", []) if isinstance(payload, dict) else payload
        new_cursor = None
    else:
        payload = cli.changed(cursors.load())
        rows = payload.get("conversations", []) if isinstance(payload, dict) else payload
        new_cursor = (payload.get("meta") or {}).get("next_cursor") if isinstance(payload, dict) else None
    utterances = []
    for raw in with_utterances(cli, rows):
        utterances.extend(normalize_conversation(raw))
    read = words_in(utterances)
    days = count_days(utterances, h)
    del utterances  # the words end here
    if not days:
        print("nothing counted yet: no mapped speech since the last run")
        return 0
    out_dir = home() / "counts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for d in days:
        (out_dir / f"{d.date}.json").write_text(json.dumps(d.to_dict(), indent=1), encoding="utf8")
        print(render_day(d, h.child_name))
    today = days[-1]
    text, fact, layer = note(today, h.child_name)
    print(f"\nTomorrow: {text}  [{layer}]")
    written = write_reminder(cli, text, fact, today.date, h.tz_offset_hours, h.write_reminders_to_bee)
    if written:
        print("  placed in your Bee as a reminder")
    posted = _post(h, days)
    if posted:
        print(f"  counts posted ({posted})")
    if new_cursor:
        cursors.save(new_cursor)
    print(f"  {read} words read on this machine, 0 kept")
    return 0


def cmd_evidence(cli: BeeCli, args) -> int:
    from .evidence import build, render

    h = Household.load() or Household()
    record = build(cli, h)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(record), encoding="utf8")
    print(f"wrote {dest}: {record['words_read']} words read, {record['words_published']} published")
    return 0


def cmd_live(cli: BeeCli, args) -> int:
    from .live import run as live_run

    h = Household.load()
    if h is None:
        print("run volley setup first")
        return 2
    return live_run(cli, h, seconds=args.seconds)


def cmd_verify(args) -> int:
    from .verify import run as verify_run

    return verify_run(Path(args.repo))


def main(argv: list[str] | None = None, cli: BeeCli | None = None) -> int:
    p = argparse.ArgumentParser(prog="volley", description="Counts the back-and-forth with your child from your Bee, keeps the counts, throws the words away.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="is the Bee installed and signed in, and is a household set up")
    s = sub.add_parser("setup", help="which label is you, which is your child, and where the counts go")
    s.add_argument("--parent")
    s.add_argument("--child")
    s.add_argument("--child-name", dest="child_name")
    s.add_argument("--tz", type=float, help="hours from UTC, for example 5.5")
    s.add_argument("--api-url", dest="api_url")
    s.add_argument("--api-key", dest="api_key")
    s.add_argument("--reminders", type=lambda v: v.lower() in ("1", "true", "yes"), help="write tomorrow's one thing into your Bee: yes or no")
    t = sub.add_parser("today", help="count the day, show it, post the counts, write tomorrow's reminder")
    t.add_argument("--now", action="store_true", help="the last several hours rather than everything since the last run")
    e = sub.add_parser("evidence", help="a publishable record that live Bee data flowed, with no words in it")
    e.add_argument("--out", default="docs/BEE_LIVE.md")
    l = sub.add_parser("live", help="count turns as they happen")
    l.add_argument("--seconds", type=int, default=600)
    v = sub.add_parser("verify", help="recompute every published number from committed inputs")
    v.add_argument("--repo", default=".")
    args = p.parse_args(argv)

    cli = cli or BeeCli()
    try:
        if args.command == "status":
            return cmd_status(cli)
        if args.command == "setup":
            return cmd_setup(cli, args)
        if args.command == "today":
            return cmd_today(cli, args)
        if args.command == "evidence":
            return cmd_evidence(cli, args)
        if args.command == "live":
            return cmd_live(cli, args)
        if args.command == "verify":
            return cmd_verify(args)
    except BeeNotAuthenticated as err:
        print(str(err), file=sys.stderr)
        return 3
    except BeeCliError as err:
        print(str(err), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
