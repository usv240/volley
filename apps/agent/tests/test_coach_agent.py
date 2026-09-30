"""The coach against the real server and a scripted model.

Claims: the model is offered the seven tools with no credential
argument on any of them; the wrapper adds the household's id and key
and the server answers; an answer that uses the numbers a tool
returned is repeated; an answer that invents a number is sent back
once with the invented number named, and if the model does it again
the parent hears the tool results plainly; a forbidden word is
refused the same way.
"""

from __future__ import annotations

import json

from conftest import ScriptedModel
from volley_agent.coach import Coach
from volley_server.mcp import TOOLS

SEVEN = sorted(t["name"] for t in TOOLS)


def test_the_model_sees_seven_tools_and_no_credential_on_any(volley_url):
    with Coach(f"{volley_url}/mcp", model=ScriptedModel([("say", "hello")])) as c:
        assert sorted(c.agent.tool_names) == SEVEN
        for name in SEVEN:
            spec = c.agent.tool_registry.registry[name].tool_spec
            props = spec["inputSchema"].get("properties", {})
            assert "api_key" not in props and "household_id" not in props, name


def test_an_answer_from_the_tools_is_repeated_as_the_model_layer(volley_url):
    script = [
        ("tool", "how_was_our_talking_today", {}),
        ("say", "You and Asha went back and forth 157 times today, and the best of it was around 6 in the evening."),
    ]
    with Coach(f"{volley_url}/mcp", model=ScriptedModel(script)) as c:
        a = c.ask("how was our talking today")
    assert a.layer == "model"
    assert a.tools_called == ["how_was_our_talking_today"]
    assert "157" in a.text and not a.refused


def test_an_invented_number_is_sent_back_once_then_read_plainly(volley_url):
    script = [
        ("tool", "how_was_our_talking_today", {}),
        ("say", "157 turns today, which is 45 more than most families manage."),
        ("say", "157 turns, and honestly 45 above the average."),
    ]
    model = ScriptedModel(script)
    with Coach(f"{volley_url}/mcp", model=model) as c:
        a = c.ask("how was our talking today")
    assert a.layer == "plain"
    assert len(a.refused) == 2 and "45" in a.refused[0]
    assert "turns: 157" in a.text
    # The correction named the number, so the model was told exactly what it did.
    correction = model.calls[-1][-1]["content"][0]["text"]
    assert "45" in correction and "not repeated" in correction


def test_a_corrected_answer_is_labelled_as_such(volley_url):
    script = [
        ("tool", "how_was_our_talking_today", {}),
        ("say", "Nothing here points to a delay; 157 turns."),
        ("say", "157 turns today, with the best hour around 6 in the evening."),
    ]
    with Coach(f"{volley_url}/mcp", model=ScriptedModel(script)) as c:
        a = c.ask("how was our talking today")
    assert a.layer == "model-after-correction"
    assert "delay" in a.refused[0]


def test_the_household_credentials_travel_in_the_wrapper_not_the_model(volley_url):
    import urllib.request

    made = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{volley_url}/v1/households", data=json.dumps({"name": "ours", "child_name": "Mira"}).encode(),
        headers={"content-type": "application/json"}, method="POST")).read())
    script = [("tool", "household_settings", {}), ("say", "Your household is set up for Mira.")]
    model = ScriptedModel(script)
    with Coach(f"{volley_url}/mcp", made["household_id"], made["api_key"], model=model) as c:
        a = c.ask("who is this for")
    assert a.layer == "model"
    # The tool result came back for the private household, so the key reached the server.
    result = [b for m in c.agent.messages for b in m["content"] if "toolResult" in b][0]["toolResult"]["content"][0]["text"]
    assert made["household_id"] in result and "Mira" in result
    # And the model never saw the key: not in any message it was given.
    everything = json.dumps(model.calls)
    assert made["api_key"] not in everything
