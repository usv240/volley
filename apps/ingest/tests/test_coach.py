"""The note can be warm; the facts cannot be wrong.

Every digit in a note must come from the fact it was written from, and
no forbidden word may appear. A model that breaks either rule is
overruled by the template, and the caller is told which layer wrote it.
"""

from __future__ import annotations

from serve_return import Roles, Utterance, count_day

from volley_ingest.coach import FORBIDDEN, Fact, accept, note, pick, template

ROLES = Roles.of(adult=["Ujwal"], child=["Unknown"])
T0 = 1_790_700_000.0


def exchange(hour: int, turns: int, questions: bool = True) -> list[Utterance]:
    base = T0 - (T0 % 86400) + hour * 3600
    out = []
    for i in range(turns + 1):
        speaker = "Ujwal" if i % 2 == 0 else "Unknown"
        text = "What is that?" if (speaker == "Ujwal" and questions) else "That one there."
        out.append(Utterance(base + 3 * i, speaker, text, base + 3 * i + 1))
    return out


def test_a_quiet_hour_with_the_child_present_wins_over_everything():
    day = count_day(exchange(9, 2) + exchange(18, 30), ROLES, date="2026-09-29")
    fact = pick(day)
    assert fact.kind == "quiet_hour" and fact.hour == 9 and fact.value == 2


def test_a_good_day_names_the_best_hour():
    day = count_day(exchange(18, 30), ROLES, date="2026-09-29")
    fact = pick(day)
    assert fact.kind == "best_hour" and fact.hour == 18 and fact.value == 30


def test_the_template_carries_only_the_facts_numbers():
    fact = Fact("quiet_hour", 9, 2, 40)
    text = template(fact, "Asha")
    assert "Asha" in text and "2 turns" in text
    assert accept(text, fact)


def test_a_model_that_invents_a_number_is_overruled():
    fact = Fact("best_hour", 18, 30, None)
    assert not accept("Your best hour was 6 in the evening with 30 turns, above the 27th percentile.", fact)
    assert not accept("Great day: 30 turns, and 45 yesterday.", fact)
    assert accept("Six in the evening was the hour: 30 turns. Keep it.", fact)


def test_forbidden_words_never_reach_a_parent():
    fact = Fact("best_hour", 18, 30, None)
    for word in FORBIDDEN:
        assert not accept(f"30 turns. Nothing here suggests {word}.", fact)


def test_note_falls_back_to_the_template_and_says_so():
    day = count_day(exchange(18, 30), ROLES, date="2026-09-29")
    text, fact, layer = note(day, "Asha", phrase=lambda f, floor: "30 turns, and your child is not behind.")
    assert layer == "template" and "behind" not in text
    text, fact, layer = note(day, "Asha", phrase=lambda f, floor: "Six in the evening, 30 turns with Asha. Keep it exactly so.")
    assert layer == "model"
    text, fact, layer = note(day, "Asha", phrase=lambda f, floor: (_ for _ in ()).throw(RuntimeError("bedrock down")))
    assert layer == "template"
