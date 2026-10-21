"""Every evening, without typing: `volley setup --daily 20:30`.

A step counter you have to remember to run is not a step counter. This
registers `volley today` with the operating system's own scheduler, on
the computer where the Bee is signed in: Task Scheduler on Windows, the
user's crontab elsewhere. Each run reads only what changed since the
last one (the cursor), counts, posts the counts if a household is
connected, writes tomorrow's reminder into the Bee if the parent agreed,
and leaves its output in ~/.volley/last-run.txt. `--daily off` removes it.

Nothing here runs as anyone but the parent, and nothing is installed
outside their own account.
"""

from __future__ import annotations

import platform
import re
import subprocess
import sys
from typing import Callable

from .household import home

TASK = "Volley today"
MARK = "# volley today (volley setup --daily)"

Runner = Callable[[list[str], str | None], tuple[int, str]]


def _run(argv: list[str], stdin: str | None = None) -> tuple[int, str]:
    p = subprocess.run(argv, input=stdin, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def command() -> str:
    """The line the scheduler runs: this Python, this package, output kept."""
    log = home() / "last-run.txt"
    return f'"{sys.executable}" -m volley_ingest.cli today > "{log}" 2>&1'


def _windows(at: str | None, run: Runner) -> str:
    if at is None:
        code, out = run(["schtasks", "/Delete", "/TN", TASK, "/F"], None)
        return "the evening count is off" if code == 0 else f"nothing to remove ({out.strip()[:120]})"
    code, out = run(["schtasks", "/Create", "/SC", "DAILY", "/TN", TASK, "/ST", at, "/TR", f"cmd /c {command()}", "/F"], None)
    return f"every evening at {at}, volley today runs on this computer" if code == 0 else f"the scheduler refused: {out.strip()[:200]}"


def _cron(at: str | None, run: Runner) -> str:
    code, current = run(["crontab", "-l"], None)
    lines = [l for l in (current.splitlines() if code == 0 else []) if MARK not in l]
    if at is not None:
        hh, mm = at.split(":")
        lines.append(f"{int(mm)} {int(hh)} * * * {command()} {MARK}")
    code, out = run(["crontab", "-"], "\n".join(lines) + "\n")
    if code != 0:
        return f"crontab refused: {out.strip()[:200]}"
    return f"every evening at {at}, volley today runs on this computer" if at else "the evening count is off"


def schedule(at: str, run: Runner | None = None, system: str | None = None) -> str:
    run = run or _run
    if at != "off" and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", at):
        return "give the time as HH:MM in 24-hour local time, for example 20:30, or off"
    when = None if at == "off" else at
    return (_windows if (system or platform.system()) == "Windows" else _cron)(when, run)
