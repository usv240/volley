"""The command a parent runs, against a transcript full of names.

The promise is that the words are read on this machine and never
written anywhere. This runs `volley today` in a temporary home with an
injected Bee that answers with a conversation of made-up people and
places, then reads every byte the command wrote and every byte it
printed, and looks for them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from volley_ingest.bee import BeeCli
from volley_ingest.cli import main
from volley_ingest.household import Household

NAMES = ["Priya", "Arjun", "Mehta", "Bangalore", "Koramangala"]
T0 = 1_790_714_400_000  # ms, 2026-09-29 20:40Z


def utterance(i: int, speaker: str, text: str) -> dict:
    return {
        "id": 100 + i,
        "realtime": False,
        "start": 2 * i,
        "end": 2 * i + 1,
        "spoken_at": T0 + 2000 * i,
        "text": text,
        "speaker": speaker,
        "created_at": T0 + 2000 * i + 500,
    }


def conversation() -> dict:
    lines = [
        ("Ujwal", f"What did you and {NAMES[0]} build at school?"),
        ("Unknown", f"A tower with {NAMES[1]}."),
        ("Ujwal", "How tall was it?"),
        ("Unknown", "Taller than me."),
        ("Ujwal", f"Did it fall down before {NAMES[2]} came?"),
        ("Unknown", "Yes, twice."),
        ("Ujwal", f"We could build one on the way to {NAMES[3]}."),
        ("Unknown", f"In {NAMES[4]}?"),
    ]
    return {
        "id": 10824219,
        "start_time": T0,
        "end_time": T0 + 20_000,
        "state": "COMPLETED",
        "transcriptions": [{"id": 1, "realtime": False, "utterances": [utterance(i, s, t) for i, (s, t) in enumerate(lines)]}],
    }


def runner_for(calls: list[list[str]]):
    def runner(argv: list[str]):
        calls.append(argv)
        joined = " ".join(argv)
        if "changed" in joined:
            return (0, json.dumps({"meta": {"next_cursor": "c-2"}, "conversations": [conversation()]}), "")
        if "todos create" in joined:
            return (0, json.dumps({"id": 1}), "")
        return (1, "", f"unexpected {argv}")

    return runner


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    Household(parent_labels=["Ujwal"], child_labels=["Unknown"], child_name="Asha", tz_offset_hours=5.5,
              write_reminders_to_bee=True).save()
    return tmp_path


def test_today_counts_prints_the_day_and_writes_no_word(home, capsys):
    calls: list[list[str]] = []
    assert main(["today"], cli=BeeCli(runner=runner_for(calls))) == 0
    out = capsys.readouterr().out
    assert "7 turns with Asha" in out
    assert "words read and thrown away" in out
    written = [p for p in home.rglob("*") if p.is_file()]
    names = {p.name for p in written}
    assert names == {"household.json", ".bee-cursor", "2026-09-30.json", "2026-09-30.written"}, names
    everything = out + "".join(p.read_text(encoding="utf8") for p in written)
    for name in NAMES:
        assert name not in everything
    for word in ("tower", "tall", "school"):
        assert word not in everything.lower().replace("thrown away", "")


def test_the_counts_file_is_numbers_only(home):
    main(["today"], cli=BeeCli(runner=runner_for([])))
    day = json.loads((home / "counts" / "2026-09-30.json").read_text(encoding="utf8"))
    assert day["turns"] == 7 and day["questions_adult"] == 3
    assert day["words_discarded"] == 39
    for h in day["hours"]:
        for k, v in h.items():
            assert not isinstance(v, str), (k, v)


def test_the_reminder_goes_into_the_bee_only_with_consent_and_once(home):
    calls: list[list[str]] = []
    main(["today"], cli=BeeCli(runner=runner_for(calls)))
    creates = [c for c in calls if "todos" in c and "create" in c]
    assert len(creates) == 1
    argv = creates[0]
    assert argv[argv.index("--text") + 1].startswith(("Around", "Today", "Your best hour", "A first day"))
    assert argv[argv.index("--alarm-at") + 1].endswith("Z")
    main(["today"], cli=BeeCli(runner=runner_for(calls)))
    assert len([c for c in calls if "todos" in c and "create" in c]) == 1

    h = Household.load()
    h.write_reminders_to_bee = False
    h.save()
    (home / "reminders" / "2026-09-30.written").unlink()
    calls.clear()
    main(["today"], cli=BeeCli(runner=runner_for(calls)))
    assert not [c for c in calls if "todos" in c]


def test_the_cursor_is_saved_after_the_counts_not_before(home):
    main(["today"], cli=BeeCli(runner=runner_for([])))
    assert json.loads((home / ".bee-cursor").read_text(encoding="utf8"))["cursor"] == "c-2"


def test_without_a_household_it_says_what_to_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    assert main(["today"], cli=BeeCli(runner=runner_for([]))) == 2
    assert "volley setup" in capsys.readouterr().out


def test_a_blind_household_counts_an_all_unknown_day(tmp_path, monkeypatch, capsys):
    """The Bee labels everyone Unknown; a blind household reads the roles
    from the transcript and still counts the turns, and still keeps no word."""
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    Household(blind=True, child_name="Asha", tz_offset_hours=5.5).save()

    # A two-year-old's side of the exchange, as the model's own tests use;
    # this test is about the wiring, harness/blind measures the accuracy.
    lines = [f"What did you and {NAMES[0]} build at school today?", "a tower",
             "Wow, how tall was it?", "big",
             f"Did it fall down before {NAMES[2]} came?", "yeah",
             "That sounds like a lot of fun, can you show me?", "me do it"]

    def all_unknown():
        c = conversation()
        c["transcriptions"][0]["utterances"] = [utterance(i, "Unknown", t) for i, t in enumerate(lines)]
        return c

    def runner(argv):
        joined = " ".join(argv)
        if "changed" in joined:
            return (0, json.dumps({"meta": {"next_cursor": "c-2"}, "conversations": [all_unknown()]}), "")
        return (1, "", f"unexpected {argv}")

    assert main(["today"], cli=BeeCli(runner=runner)) == 0
    day = json.loads((tmp_path / "counts" / "2026-09-30.json").read_text(encoding="utf8"))
    assert day["turns"] >= 5
    out = capsys.readouterr().out
    for name in NAMES:
        assert name not in out


def test_setup_blind_needs_no_labels(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    assert main(["setup", "--blind"], cli=BeeCli(runner=lambda argv: (1, "", "no device"))) == 0
    assert Household.load().blind is True
