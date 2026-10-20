"""The command a parent runs.

    volley status              is the Bee installed and signed in, and is a household set up
    volley setup               which label is you, which is your child
    volley connect             make a household on the service so your own days show on the site
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


DEFAULT_API_URL = "https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws"


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


def _request(url: str, body: dict | None, headers: dict[str, str], method: str = "POST") -> tuple[int, dict]:
    """One HTTP call with the standard library, so the parent's machine
    needs nothing installed beyond this package. Tests replace it."""
    import urllib.request

    data = json.dumps(body).encode("utf8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json", **headers}, method=method)
    with urllib.request.urlopen(req, timeout=30) as res:  # noqa: S310
        return res.status, json.loads(res.read().decode("utf8") or "{}")


def _post(h: Household, days: list[DayCounts], request=None) -> str | None:
    """Counts only, to the household's own route on the service, if the
    parent connected one. The body is the day's `to_dict()`, which has
    no field that can hold a word."""
    if not h.connected:
        return None
    status, _ = (request or _request)(
        f"{h.api_url.rstrip('/')}/v1/households/{h.household_id}/days",
        {"days": [d.to_dict() for d in days]},
        {"x-api-key": h.api_key},
    )
    return f"{status}"


def cmd_connect(args, request=None) -> int:
    """Makes a household on the service and keeps its key here. The
    service answers with a link to the page that shows this household
    only; the key travels in the link's fragment, which a browser never
    sends to any server, and the page moves it into local storage."""
    h = Household.load() or Household()
    if h.connected and not args.again:
        print(f"already connected as {h.household_id}; run with --again to make a new household")
        if h.mine_url:
            print(f"your days: {h.mine_url}")
        return 0
    api = (args.api_url or h.api_url or DEFAULT_API_URL).rstrip("/")
    status, answer = (request or _request)(f"{api}/v1/households", {"name": args.name, "child_name": h.child_name}, {})
    if status != 200 or "api_key" not in answer:
        print(f"the service did not make a household ({status})", file=sys.stderr)
        return 1
    h.api_url = api
    h.household_id = answer["household_id"]
    h.api_key = answer["api_key"]
    site = answer.get("site_url")
    h.mine_url = f"{site.rstrip('/')}/mine/#h={h.household_id}&k={h.api_key}" if site else None
    h.save()
    print(f"connected: household {h.household_id} on {api}")
    print("only counts will ever be sent there; the key is shown once by the service and kept in household.json")
    if h.mine_url:
        print(f"your days, in your browser: {h.mine_url}")
    return 0


def cmd_share(args, request=None) -> int:
    """A read-only link for a home visitor or a coach: the days, the week
    and the note, nothing that writes. Home-visit gains fade when the
    visits stop; this keeps the person coaching the family reading the
    counts in between. A new share replaces the last; --revoke ends it."""
    h = Household.load()
    if h is None or not h.connected:
        print("connect first: volley connect")
        return 2
    base = f"{h.api_url.rstrip('/')}/v1/households/{h.household_id}/share"
    if args.revoke:
        status, _ = (request or _request)(base, None, {"x-api-key": h.api_key}, method="DELETE")
        print("share revoked; the old link reads nothing now" if status == 200 else f"the service answered {status}")
        return 0 if status == 200 else 1
    status, answer = (request or _request)(base, None, {"x-api-key": h.api_key})
    if status != 200 or "share_token" not in answer:
        print(f"the service did not make a share ({status})", file=sys.stderr)
        return 1
    print("a read-only link for the person coaching your family; it shows counts and the note, and cannot post, share or delete:")
    print(f"  {answer.get('share_url') or answer['share_token']}")
    print("a new share replaces this one; end it with: volley share --revoke")
    return 0


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
    if getattr(args, "blind", False):
        h.blind = True
        print("blind: roles are read from the transcript, because the Bee labels every speaker Unknown")
    if not (args.parent and args.child) and not h.blind:
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
    if h is None or not h.ready:
        print("run volley setup first: --parent and --child labels, or --blind to read the roles from the transcript")
        return 2
    cursors = CursorStore(str(home() / ".bee-cursor"))
    if getattr(args, "conversation", None):
        # One session and nothing else: a Bee worn all day also hears work
        # and strangers, and a count of those is not the family's.
        rows = [cli.conversation_get(args.conversation)]
        new_cursor = None
    elif args.now:
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
        if h.mine_url:
            print(f"  see them: {h.mine_url}")
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
    s.add_argument("--blind", action="store_true",
                   help="read who is the child and who the adult from the transcript, for a Bee that labels everyone Unknown")
    s.add_argument("--parent")
    s.add_argument("--child")
    s.add_argument("--child-name", dest="child_name")
    s.add_argument("--tz", type=float, help="hours from UTC, for example 5.5")
    s.add_argument("--api-url", dest="api_url")
    s.add_argument("--api-key", dest="api_key")
    s.add_argument("--reminders", type=lambda v: v.lower() in ("1", "true", "yes"), help="write tomorrow's one thing into your Bee: yes or no")
    c = sub.add_parser("connect", help="make a household on the service so your own days show on the site")
    c.add_argument("--name", default="ours", help="a name you choose; it is the only text the service keeps")
    c.add_argument("--api-url", dest="api_url", help="another deployment of the service, if you run your own")
    c.add_argument("--again", action="store_true", help="make a new household even if one is connected")
    t = sub.add_parser("today", help="count the day, show it, post the counts, write tomorrow's reminder")
    t.add_argument("--now", action="store_true", help="the last several hours rather than everything since the last run")
    t.add_argument("--conversation", help="count one Bee conversation by its id, and read nothing else")
    e = sub.add_parser("evidence", help="a publishable record that live Bee data flowed, with no words in it")
    e.add_argument("--out", default="docs/BEE_LIVE.md")
    l = sub.add_parser("live", help="count turns as they happen")
    l.add_argument("--seconds", type=int, default=600)
    sh = sub.add_parser("share", help="a read-only link for a home visitor or a coach")
    sh.add_argument("--revoke", action="store_true", help="end the current share")
    v = sub.add_parser("verify", help="recompute every published number from committed inputs")
    v.add_argument("--repo", default=".")
    args = p.parse_args(argv)

    cli = cli or BeeCli()
    try:
        if args.command == "status":
            return cmd_status(cli)
        if args.command == "setup":
            return cmd_setup(cli, args)
        if args.command == "connect":
            return cmd_connect(args)
        if args.command == "share":
            return cmd_share(args)
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
