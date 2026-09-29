"""Tomorrow's one thing, placed where the parent already lives.

`bee todos create --text <note> --alarm-at <iso>` puts the note into
the parent's own Bee as a reminder that fires at the hour the counts
named. The loop closes back into the user's system rather than ending
on a web page. It is written only if the parent said yes in setup, and
never twice for one day; the marker for "written today" is a date in
the household directory, not anything about the note.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .bee import BeeCli
from .coach import Fact
from .household import home


def alarm_for(fact: Fact, tz_offset_hours: float, now: datetime | None = None) -> str:
    """Tomorrow at the fact's hour, or six in the evening if it names none, as ISO in UTC."""
    now = now or datetime.now(timezone.utc)
    local_now = now + timedelta(hours=tz_offset_hours)
    hour = fact.hour if fact.hour is not None else 18
    local_alarm = (local_now + timedelta(days=1)).replace(hour=hour % 24, minute=0, second=0, microsecond=0)
    return (local_alarm - timedelta(hours=tz_offset_hours)).isoformat(timespec="seconds").replace("+00:00", "Z")


def already_written(date: str) -> bool:
    return (home() / "reminders" / f"{date}.written").exists()


def mark_written(date: str) -> None:
    d = home() / "reminders"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{date}.written").write_text("", encoding="utf8")


def write(cli: BeeCli, text: str, fact: Fact, date: str, tz_offset_hours: float, consented: bool) -> bool:
    """Create the reminder. Returns whether it was written."""
    if not consented or already_written(date):
        return False
    cli.todo_create(text, alarm_for(fact, tz_offset_hours))
    mark_written(date)
    return True
