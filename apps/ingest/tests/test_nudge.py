"""Coaching in the moment: the rule, the usual hour, and the live loop.

The loop is driven with a fake clock, an injected stream, and a Bee that
records what it was asked to create, so nothing here reaches a device,
a speaker or AWS.
"""

from __future__ import annotations

import json
import time
from datetime import datetime

from volley_ingest import nudge as nd
from volley_ingest.bee import BeeCli
from volley_ingest.household import Household
from volley_ingest.live import run


def _from(first, then):
    """A clock that reads `first` once (when watching starts), then `then`."""
    seen = []

    def clock():
        seen.append(1)
        return first if len(seen) == 1 else then

    return clock


def write_day(d, date, hours):
    (d / f"{date}.json").write_text(json.dumps({"date": date, "hours": [
        {"hour": hr, "turns": t, "utterances_child": c} for hr, t, c in hours]}), encoding="utf8")


def test_the_usual_best_hour_averages_days_and_ignores_hours_without_the_child(tmp_path):
    write_day(tmp_path, "2026-10-01", [(18, 30, 9), (8, 10, 4), (12, 0, 0)])
    write_day(tmp_path, "2026-10-02", [(18, 20, 7), (8, 30, 5)])
    u = nd.usual_best_hour(tmp_path)
    assert (u.hour, u.turns, u.days) == (18, 25.0, 2)
    assert nd.usual_best_hour(tmp_path / "none") is None


def test_the_rule_fires_only_late_enough_in_the_usual_hour_and_only_when_quiet():
    u = nd.Usual(hour=18, turns=24.0, days=5)
    at = lambda h, m: datetime(2026, 10, 21, h, m)
    assert nd.should_nudge(at(18, 25), u, 6, already_today=False)
    assert not nd.should_nudge(at(18, 25), u, 7, already_today=False)   # more than a quarter: leave them be
    assert not nd.should_nudge(at(18, 10), u, 0, already_today=False)   # too early in the hour to tell
    assert not nd.should_nudge(at(19, 30), u, 0, already_today=False)   # not the usual hour
    assert not nd.should_nudge(at(18, 25), u, 0, already_today=True)    # once a day
    assert not nd.should_nudge(at(18, 25), nd.Usual(18, 3.0, 5), 0, already_today=False)  # no habit to keep


def test_the_sentence_names_the_child_and_carries_no_number():
    text = nd.message("Asha")
    assert "Asha" in text and not any(ch.isdigit() for ch in text)


def test_a_quiet_usual_hour_puts_one_nudge_into_the_bee_and_says_it_once(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    counts = tmp_path / "counts"
    counts.mkdir()
    write_day(counts, "2026-10-20", [(18, 24, 8)])
    h = Household(blind=True, child_name="Asha", write_reminders_to_bee=True)
    created, spoken = [], []

    def runner(argv):
        created.append(argv)
        return 0, json.dumps({"id": 1}), ""

    # A quiet stream: open, but nothing arrives, so only the timer can notice.
    def quiet():
        time.sleep(5)
        yield from ()

    import itertools

    ticks = itertools.chain((datetime(2026, 10, 21, 18, m) for m in (5, 15, 22, 30, 40)), itertools.repeat(datetime(2026, 10, 21, 18, 50)))
    rec = tmp_path / "run.json"
    rc = run(BeeCli(runner=runner), h, seconds=1, lines=quiet(), nudge=True, speak=True,
             clock=lambda: next(ticks), poll_seconds=0.01, say=spoken.append, record=str(rec))
    logged = json.loads(rec.read_text(encoding="utf-8"))
    assert logged["nudge"]["placed_in_bee"] and logged["nudge"]["todo_id"] == 1 and logged["words_kept"] == 0
    assert logged["usual"] == {"hour": 18, "turns": 24.0, "days": 1} and logged["checks"]
    assert "Asha" not in json.dumps(logged["checks"])
    assert rc == 0
    creates = [a for a in created if "todos" in a and "create" in a]
    assert len(creates) == 1 and creates[0][creates[0].index("--text") + 1] == nd.message("Asha")
    assert spoken == [nd.message("Asha")]
    assert (tmp_path / "nudges" / "2026-10-21.sent").exists()
    assert "watching 18:00" in capsys.readouterr().out


def test_without_reminder_consent_a_nudge_is_only_printed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    counts = tmp_path / "counts"
    counts.mkdir()
    write_day(counts, "2026-10-20", [(18, 24, 8)])
    created = []
    run(BeeCli(runner=lambda a: (created.append(a), (0, "{}", ""))[1]), Household(blind=True), seconds=1, lines=iter([]),
        nudge=True, clock=_from(datetime(2026, 10, 21, 18, 0), datetime(2026, 10, 21, 18, 30)), poll_seconds=0.01)
    assert not [a for a in created if "todos" in a]
    out = capsys.readouterr().out
    assert "reminders are off" in out and "nudge at 18:30" in out


def test_blind_live_counting_reads_roles_so_a_lively_hour_is_not_nudged(tmp_path, monkeypatch, capsys):
    """Every speaker arrives Unknown. Before roles were read live, a blind
    household counted zero turns and every usual hour looked quiet."""
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    counts = tmp_path / "counts"
    counts.mkdir()
    write_day(counts, "2026-10-20", [(18, 12, 8)])
    lines = []
    t = 1_790_000_000.0
    talk = [("What did you build there?", 1.8), ("A tower!", 0.8), ("Is it taller than you?", 1.8), ("Yes taller!", 0.8)] * 6
    for i, (text, _) in enumerate(talk):
        lines.append(json.dumps({"type": "new-utterance", "utterance": {"text": text, "speaker": "Unknown", "spoken_at": int((t + 3 * i) * 1000)}}))
    created = []
    # The clock moves a minute per reading, so the hour fills as it would.
    from datetime import timedelta
    from itertools import count

    tick = count()
    clock = lambda: datetime(2026, 10, 21, 18, 0) + timedelta(minutes=min(next(tick), 59))
    run(BeeCli(runner=lambda a: (created.append(a), (0, "{}", ""))[1]), Household(blind=True, write_reminders_to_bee=True),
        seconds=2, lines=iter(lines), nudge=True, clock=clock, poll_seconds=0.01)
    out = capsys.readouterr().out
    assert "turns this hour" in out
    assert not [a for a in created if "todos" in a], "a lively hour must not be nudged"


def test_an_hour_not_heard_from_its_start_is_never_called_quiet(tmp_path, monkeypatch):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    counts = tmp_path / "counts"
    counts.mkdir()
    write_day(counts, "2026-10-20", [(18, 24, 8)])
    created = []
    run(BeeCli(runner=lambda a: (created.append(a), (0, "{}", ""))[1]), Household(blind=True, write_reminders_to_bee=True),
        seconds=1, lines=iter([]), nudge=True, clock=lambda: datetime(2026, 10, 21, 18, 30), poll_seconds=0.01)
    assert not [a for a in created if "todos" in a]
