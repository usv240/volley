"""The rule against its own definition.

Worked examples first, because a counter that is wrong about a
four-second gap is wrong about everything downstream. Then the two
promises the package makes to anyone who reads its output: the window
is the published five seconds, and no word survives.
"""

from __future__ import annotations

import json

from serve_return import WINDOW_SECONDS, Roles, Utterance, count_day, count_turns

ROLES = Roles.of(adult=["MOT", "FAT"], child=["CHI"])
T0 = 1_790_714_400.0  # 2026-09-29 20:40:00Z


def u(offset: float, speaker: str, text: str, length: float | None = None) -> Utterance:
    return Utterance(T0 + offset, speaker, text, None if length is None else T0 + offset + length)


def test_the_window_is_the_published_five_seconds():
    assert WINDOW_SECONDS == 5.0


def test_an_adult_answered_by_a_child_within_the_window_is_one_turn():
    assert count_turns([u(0, "MOT", "What is that?", 1.0), u(4.9, "CHI", "A dog.", 1.0)], ROLES) == 1


def test_a_gap_over_the_window_is_not_a_turn():
    assert count_turns([u(0, "MOT", "What is that?", 1.0), u(6.1, "CHI", "A dog.", 1.0)], ROLES) == 0


def test_the_gap_is_measured_from_the_end_of_the_first_utterance():
    # Starts eight seconds apart, but the first utterance lasts four, so
    # the child answered four seconds after it ended: a turn.
    assert count_turns([u(0, "MOT", "Tell me about your day at school", 4.0), u(8.0, "CHI", "Fun.", 0.5)], ROLES) == 1


def test_same_role_runs_merge_so_a_monologue_is_one_block():
    utts = [u(0, "MOT", "One.", 1), u(1.5, "MOT", "Two.", 1), u(3.0, "MOT", "Three.", 1), u(4.5, "CHI", "Yes.", 1)]
    assert count_turns(utts, ROLES) == 1


def test_a_back_and_forth_counts_every_alternation():
    utts = [u(0, "MOT", "Hi?", 1), u(2, "CHI", "Hi.", 1), u(4, "MOT", "What now?", 1), u(6, "CHI", "Play.", 1), u(8, "MOT", "Which?", 1)]
    assert count_turns(utts, ROLES) == 4


def test_an_unmapped_speaker_is_ignored_not_counted_as_either_role():
    utts = [u(0, "MOT", "Dinner?", 1), u(2, "VISITOR", "Lovely.", 1), u(4, "CHI", "Yes!", 1)]
    # MOT then CHI with the visitor removed: 4 seconds after MOT ended, one turn.
    assert count_turns(utts, ROLES) == 1


def test_a_childs_babble_counts_as_an_utterance():
    assert count_turns([u(0, "MOT", "Is that yours?", 1), u(2, "CHI", "buh", 0.5)], ROLES) == 1


def test_two_adults_alone_count_zero_child_turns():
    utts = [u(0, "MOT", "Did you call?", 1), u(2, "FAT", "I did.", 1), u(4, "MOT", "And?", 1)]
    assert count_turns(utts, ROLES) == 0


def test_silence_counts_nothing():
    assert count_turns([], ROLES) == 0
    assert count_day([], ROLES, date="2026-09-29").turns == 0


def test_the_day_breaks_out_serves_responses_latency_questions_and_the_longest_exchange():
    utts = [
        u(0, "CHI", "Mama look.", 1),           # the child serves
        u(2, "MOT", "What did you find?", 1),    # adult responds in 1s, a question
        u(4, "CHI", "A bug.", 1),
        u(6, "MOT", "Where was it?", 1),         # question
        u(20, "MOT", "Time for a bath.", 1),     # a new exchange after a 13s gap; adult serves
        u(22, "CHI", "No.", 1),
    ]
    day = count_day(utts, ROLES, date="2026-09-29")
    assert day.turns == 4
    assert day.serves_child == 1 and day.serves_adult == 1
    assert day.responses_within_window == 2
    assert day.response_latency_median_s == 1.0
    assert day.questions_adult == 2
    assert day.longest_volley == 3
    assert day.words_discarded == 16
    assert day.best_hour == 20
    assert day.date == "2026-09-29"


def test_hours_are_local_when_an_offset_is_given():
    day = count_day([u(0, "MOT", "Hi?", 1), u(2, "CHI", "Hi.", 1)], ROLES, date="2026-09-30", tz_offset_hours=5.5)
    assert [h.hour for h in day.hours] == [2]  # 20:40Z is 02:10 in India


def test_no_word_survives_into_the_output():
    names = ["Priya", "Arjun", "Dr Mehta", "Bangalore"]
    utts = [u(i * 2, "MOT" if i % 2 == 0 else "CHI", f"Tell {names[i % 4]} about {names[(i + 1) % 4]}?", 1) for i in range(12)]
    blob = json.dumps(count_day(utts, ROLES, date="2026-09-29").to_dict())
    for name in names:
        assert name.split()[-1] not in blob
    assert "Tell" not in blob and "about" not in blob


def test_deleting_the_text_never_changes_the_count():
    utts = [u(0, "MOT", "What is that?", 1), u(2, "CHI", "A dog.", 1), u(4, "MOT", "Big?", 1)]
    stripped = [Utterance(x.start, x.speaker, "x", x.end) for x in utts]
    assert count_turns(utts, ROLES) == count_turns(stripped, ROLES) == 2


def test_a_deliberately_wrong_window_changes_the_answer():
    # The harness relies on this: a rule that ignored its window could
    # not be caught by any agreement figure.
    utts = [u(0, "MOT", "Hi?", 1), u(20, "CHI", "Hi.", 1)]
    assert count_turns(utts, ROLES) == 0
    assert count_turns(utts, ROLES, window=50.0) == 1


def test_iso_timestamps_are_accepted():
    a = Utterance.from_iso("2026-09-29T20:40:00Z", "MOT", "Hi?", "2026-09-29T20:40:01Z")
    b = Utterance.from_iso("2026-09-29T20:40:03Z", "CHI", "Hi.")
    assert count_turns([a, b], ROLES) == 1
