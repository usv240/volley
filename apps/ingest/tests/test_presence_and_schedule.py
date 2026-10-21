"""The two settings that make Volley a thing a parent can leave running.

`--only-with-child`: a stretch of adults talking is set aside, a stretch
with a child in it is kept, and the threshold is the one the harness
measured. `--daily`: the evening run is registered with the operating
system's own scheduler, with the exact command pinned, and removed
again by `off`. The scheduler is injected; nothing here touches the
machine's real task list.
"""

from __future__ import annotations

import json
from pathlib import Path

from serve_return import Utterance

from volley_ingest import schedule as sched
from volley_ingest.presence import THRESHOLD, harness_threshold, stretches, with_child

REPO = Path(__file__).resolve().parents[3]
ADULT = ["Did you remember to send the invoice to the accountant before Friday?", "I think the meeting moved to Thursday afternoon.",
         "We should look at the budget again next week.", "Can you pick up groceries on the way home?", "The plumber said he would come around ten."]
CHILD = ["What's that?", "Mommy look!", "A doggy!", "I want the ball.", "No!", "Again again!", "Where daddy go?", "Me do it."]


def adults(t0: float) -> list[Utterance]:
    return [Utterance(t0 + 4 * i, "Unknown", ADULT[i % 5], t0 + 4 * i + 2.5) for i in range(30)]


def family(t0: float) -> list[Utterance]:
    out = []
    for i in range(30):
        text = ("What did you build there?" if i % 4 == 0 else "Is that a big tower?") if i % 2 == 0 else CHILD[i % 8]
        out.append(Utterance(t0 + 3 * i, "Unknown", text, t0 + 3 * i + (1.8 if i % 2 == 0 else 0.8)))
    return out


def test_the_threshold_is_the_one_the_harness_measured():
    assert THRESHOLD == harness_threshold(REPO)


def test_adults_talking_are_set_aside_and_a_child_is_kept():
    kept, dropped = with_child(adults(0.0) + family(1000.0))
    assert dropped == 1
    assert {u.start for u in kept} == {u.start for u in family(1000.0)}


def test_stretches_are_three_minutes_from_their_first_line():
    us = [Utterance(t, "Unknown", "x", t + 1) for t in (0, 100, 179, 181, 400)]
    assert [len(s) for s in stretches(us)] == [3, 1, 1]


def test_the_rule_on_the_bee_keeps_the_real_conversation_and_drops_the_controls():
    r = json.loads((REPO / "harness" / "beeloop" / "with_child.json").read_text(encoding="utf-8"))["rows"]
    assert r["parent_and_child"]["turns_only_with_child"] == r["parent_and_child"]["turns_every_stretch"] > 0
    assert r["adults"]["turns_only_with_child"] == 0 < r["adults"]["turns_every_stretch"]
    assert r["onevoice"]["turns_only_with_child"] == 0 < r["onevoice"]["turns_every_stretch"]


def test_daily_on_windows_registers_one_task_with_the_pinned_command(monkeypatch, tmp_path):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    calls = []
    said = sched.schedule("20:30", run=lambda argv, stdin: (calls.append(argv), (0, ""))[1], system="Windows")
    assert "20:30" in said
    argv = calls[0]
    assert argv[:2] == ["schtasks", "/Create"] and argv[argv.index("/TN") + 1] == "Volley today"
    assert argv[argv.index("/ST") + 1] == "20:30" and "/F" in argv
    tr = argv[argv.index("/TR") + 1]
    assert "-m volley_ingest.cli today" in tr and "last-run.txt" in tr
    sched.schedule("off", run=lambda argv, stdin: (calls.append(argv), (0, ""))[1], system="Windows")
    assert calls[-1] == ["schtasks", "/Delete", "/TN", "Volley today", "/F"]


def test_daily_elsewhere_edits_only_its_own_crontab_line(monkeypatch, tmp_path):
    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    table = {"text": "0 7 * * * backup.sh\n"}

    def run(argv, stdin):
        if argv == ["crontab", "-l"]:
            return 0, table["text"]
        table["text"] = stdin
        return 0, ""

    sched.schedule("21:05", run=run, system="Linux")
    lines = table["text"].strip().splitlines()
    assert lines[0] == "0 7 * * * backup.sh" and lines[1].startswith("5 21 * * * ") and sched.MARK in lines[1]
    sched.schedule("21:30", run=run, system="Linux")
    assert sum(sched.MARK in l for l in table["text"].splitlines()) == 1
    sched.schedule("off", run=run, system="Linux")
    assert table["text"].strip() == "0 7 * * * backup.sh"


def test_a_bad_time_is_refused_before_anything_runs():
    calls = []
    said = sched.schedule("8pm", run=lambda argv, stdin: (calls.append(argv), (0, ""))[1], system="Windows")
    assert calls == [] and "HH:MM" in said


def test_setup_records_the_choice_and_today_says_what_it_set_aside(monkeypatch, tmp_path, capsys):
    import json as _json

    from volley_ingest.bee import BeeCli
    from volley_ingest.cli import main
    from volley_ingest.household import Household

    monkeypatch.setenv("VOLLEY_HOME", str(tmp_path))
    assert main(["setup", "--blind", "--only-with-child", "yes", "--tz", "0"], cli=BeeCli(runner=lambda a: (1, "", "no"))) == 0
    assert Household.load().only_with_child is True

    def utt(i, u):
        return {"id": i, "start": u.start - 1_790_000_000, "end": u.finish - 1_790_000_000, "spoken_at": int(u.start * 1000),
                "text": u.text, "speaker": "Unknown"}

    day = adults(1_790_000_000.0) + family(1_790_001_000.0)
    convo = {"id": 7, "start_time": 1_790_000_000_000, "end_time": 1_790_002_000_000, "state": "COMPLETED",
             "transcriptions": [{"id": 1, "realtime": False, "utterances": [utt(i, u) for i, u in enumerate(day)]}]}

    def runner(argv):
        if "changed" in " ".join(argv):
            return 0, _json.dumps({"meta": {}, "conversations": [convo]}), ""
        return 1, "", "unexpected"

    capsys.readouterr()
    assert main(["today"], cli=BeeCli(runner=runner)) == 0
    assert "1 three-minute stretch with no child's voice set aside" in capsys.readouterr().out


def test_the_licence_free_option_uses_the_measured_scale_and_no_model(monkeypatch, tmp_path):
    from volley_ingest.alternation import ALTERNATION_SCALE
    from volley_ingest.bee import Utterance as BeeUtterance
    from volley_ingest.days import count_days
    from volley_ingest.household import Household

    r = json.loads((REPO / "harness" / "blind" / "results.json").read_text(encoding="utf-8"))
    assert ALTERNATION_SCALE == r["alternating_scale_all_families"]
    us = [BeeUtterance(ts="2026-10-21T18:00:00Z", start_s=1_790_000_000 + 3 * i, end_s=1_790_000_001.5 + 3 * i, speaker="Unknown", text=t)
          for i, t in enumerate(["What is that?", "A doggy!", "Is it big?", "Big doggy!"] * 5)]
    h = Household(blind=True, role_model="alternation")
    days = count_days(us, h)
    assert days and days[0].turns == round(19 * ALTERNATION_SCALE)
