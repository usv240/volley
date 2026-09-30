"""The CHAT loader against a fixture small enough to count by hand.

Two files. The first is a mother, a child and a sibling with time
bullets: by the rule, MOT 1.0-2.5, CHI 3.0-3.8 (turn: 0.5 s after),
MOT 4.0-5.0 (turn: 0.2 s after), CHI 12.0-13.0 (no turn: 7 s gap),
SIB 13.2-14.0 (ignored: not mapped), MOT 14.5-15.5 (turn from the
child at 12.0-13.0: 1.5 s after the child finished) gives 3 turns; the
naive speaker-change count over the mapped two is 4. The second file
has no time marks and must be skipped by name.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import importlib.util

spec = importlib.util.spec_from_file_location("childes_run", Path(__file__).with_name("run.py"))
childes_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(childes_run)
load, roles_for, playlogue_harness = childes_run.load, childes_run.roles_for, childes_run.playlogue_harness

from serve_return import count_turns  # noqa: E402

TIMED = "\n".join([
    "@UTF8", "@Begin", "@Languages:\teng",
    "@Participants:\tCHI Target_Child, MOT Mother, SIB Sibling",
    "@ID:\teng|test|CHI|3;06.|male|||Target_Child|||",
    "@ID:\teng|test|MOT|||||Mother|||",
    "@ID:\teng|test|SIB|7;00.|female|||Sibling|||",
    "@Media:\ttest, audio",
    "*MOT:\twhat did you build today ? \x151000_2500\x15",
    "*CHI:\ta tower . \x153000_3800\x15",
    "*MOT:\thow tall was it ? \x154000_5000\x15",
    "*CHI:\ttaller than me . \x1512000_13000\x15",
    "*SIB:\tno it was not . \x1513200_14000\x15",
    "*MOT:\tdid it fall down ? \x1514500_15500\x15",
    "@End", "",
])

UNTIMED = "\n".join([
    "@UTF8", "@Begin", "@Languages:\teng",
    "@Participants:\tCHI Target_Child, MOT Mother",
    "@ID:\teng|test|CHI|2;00.|male|||Target_Child|||",
    "@ID:\teng|test|MOT|||||Mother|||",
    "*MOT:\thello .", "*CHI:\thi .", "@End", "",
])


def fixture(tmp_path: Path) -> Path:
    z = tmp_path / "corpus.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("corpus/timed.cha", TIMED)
        zf.writestr("corpus/untimed.cha", UNTIMED)
    return z


def test_roles_time_marks_and_the_hand_count(tmp_path):
    sessions, meta, skipped = load(fixture(tmp_path))
    assert list(sessions) == ["timed"] and skipped == ["untimed"]
    utts = sessions["timed"]
    assert [u.speaker for u in utts] == ["ADULT:MOT", "CHI", "ADULT:MOT", "CHI", "OTHER:SIB", "ADULT:MOT"]
    assert utts[0].start == 1.0 and utts[0].end == 2.5
    roles = roles_for(utts)
    assert count_turns(utts, roles) == 3
    assert meta["timed"]["age_months"] == 42.0


def test_the_evaluation_runs_on_it_with_the_playlogue_shape(tmp_path):
    playlogue = playlogue_harness()
    playlogue.role_map = roles_for
    sessions, meta, _skipped = load(fixture(tmp_path))
    result = playlogue.evaluate(sessions, meta)
    assert result["turns"] == 3
    assert result["baselines"]["naive_speaker_changes"] == 4
    assert result["window_check"]["differs"] is True
    assert set(result["per_session"][0]) >= {"turns_per_hour", "adult_words", "age_months", "single_speaker_stretches"}
