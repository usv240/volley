"""Roles from the transcript alone: the shipped model, and its contract."""

from __future__ import annotations

import json

from serve_return import Roles, Utterance, count_turns
from serve_return.blind import RoleModel, childes_model, infer_roles, relabel

ADULT = ["What did you build at school today?", "Wow, how tall was it?", "Did it fall down before lunch?",
         "That sounds like a lot of fun, can you show me?"]
CHILD = ["a tower", "big", "yeah", "me do it"]


def convo(t0: float = 1000.0) -> list[Utterance]:
    us, t = [], t0
    for a, c in zip(ADULT, CHILD):
        us.append(Utterance(t, "Unknown", a, t + 2.0)); t += 2.6
        us.append(Utterance(t, "Unknown", c, t + 0.8)); t += 1.5
    return us


def test_the_shipped_model_loads_and_is_weights_only():
    m = childes_model()
    assert len(m.weights) > 10_000
    assert all(isinstance(v, float) for v in list(m.weights.values())[:1000])


def test_a_typical_exchange_is_read_as_adult_then_child():
    roles = infer_roles(convo())
    assert roles == ["adult", "child"] * 4


def test_relabel_lets_the_turn_rule_count_an_unlabelled_exchange():
    us = convo()
    unlabelled = count_turns(us, Roles.of(adult=["adult"], child=["child"]))
    counted = count_turns(relabel(us), Roles.of(adult=["adult"], child=["child"]))
    assert unlabelled == 0 and counted == 7


def test_relabel_sorts_and_keeps_times_and_text():
    us = list(reversed(convo()))
    out = relabel(us)
    assert [u.start for u in out] == sorted(u.start for u in us)
    assert {u.speaker for u in out} <= {"adult", "child"}


def test_a_model_round_trips_through_json():
    m = RoleModel().fit([[(u, r) for u, r in zip(convo(), ["adult", "child"] * 4)]])
    back = RoleModel.from_json(m.to_json())
    assert back.weights == m.weights
    assert json.loads(m.to_json())["positive"] == "child"


def test_the_shipped_model_carries_its_learned_turn_scale():
    m = childes_model()
    assert 1.05 < m.turn_scale < 1.3


def test_calibrate_day_scales_turns_and_keeps_hours_summing():
    from serve_return import count_day
    from serve_return.blind import calibrate_day

    day = count_day(relabel(convo()), Roles.of(adult=["adult"], child=["child"]), date="2026-10-19")
    before = day.turns
    m = RoleModel(turn_scale=1.5)
    day = calibrate_day(day, m)
    assert day.turns == sum(h.turns for h in day.hours)
    assert day.turns >= before


def test_turn_scale_round_trips():
    m = RoleModel({"bias": 0.1}, turn_scale=1.2)
    assert RoleModel.from_json(m.to_json()).turn_scale == 1.2
