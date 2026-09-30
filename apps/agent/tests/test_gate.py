"""The gate, on its own."""

from __future__ import annotations

import json

from volley_agent.gate import check, numbers_returned, plain_rendering

DAY = json.dumps({"household_id": "demo-family", "simulated": True, "date": "2026-09-28", "turns": 157, "best_hour": 18,
                  "quietest_hour_with_child": 16, "longest_volley": 7, "questions_adult": 32, "words_discarded": 1196})


def test_every_number_a_tool_returned_is_allowed_in_both_clock_forms():
    allowed = numbers_returned([DAY])
    for n in ("157", "18", "6", "16", "4", "7", "32", "1196", "2026", "09", "9", "28"):
        assert n in allowed, n


def test_a_number_no_tool_returned_is_refused_and_named():
    v = check("You had 157 turns today, about 45 more than yesterday.", [DAY])
    assert not v.ok
    assert v.invented == {"45"}
    assert "45" in v.reason()


def test_an_hour_may_be_said_on_a_twelve_hour_clock():
    assert check("Your best hour was around 6 in the evening, with 157 turns in the day.", [DAY]).ok


def test_the_forbidden_words_are_refused_even_with_no_numbers():
    v = check("Nothing here suggests a delay.", [DAY])
    assert not v.ok and v.forbidden == ["delay"]


def test_a_sentence_with_no_numbers_passes():
    assert check("A good day of talking, and the evening was the best of it.", [DAY]).ok


def test_the_plain_rendering_is_numbers_only():
    text = plain_rendering([DAY])
    assert "turns: 157" in text and "best hour: 18" in text and "date: 2026-09-28" in text
    assert check(text, [DAY]).ok
