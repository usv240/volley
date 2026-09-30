"""The Tuesday agent's allow-list, and the two servers side by side.

The Bee is stood in for by a small MCP server over stdio that offers
the same tool names the real one does (captured from `bee mcp serve`
on 2026-09-30), so the filter can be tested on the real surface
without a signed-in Bee. The claims: the transcript, search, photo and
location tools are never offered to the model; the summary and to-do
tools are; Volley's tools sit beside them; and an answer that mixes a
Volley number with a Bee summary passes the gate while an invented
number does not.
"""

from __future__ import annotations

import sys
from pathlib import Path

from conftest import ScriptedModel
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient
from volley_agent.tuesday import BEE_TOOLS_ALLOWED, BEE_TOOLS_NEVER, Tuesday

FAKE_BEE = Path(__file__).with_name("fake_bee_mcp.py")


def fake_bee() -> MCPClient:
    return MCPClient(
        lambda: stdio_client(StdioServerParameters(command=sys.executable, args=[str(FAKE_BEE)])),
        tool_filters={"allowed": list(BEE_TOOLS_ALLOWED)},
    )


def test_the_lists_do_not_overlap_and_name_the_transcript_tool():
    assert not set(BEE_TOOLS_ALLOWED) & set(BEE_TOOLS_NEVER)
    assert "bee_get_conversation_transcript" in BEE_TOOLS_NEVER


def test_only_the_allowed_bee_tools_are_offered_beside_volleys_seven(volley_url):
    with Tuesday(f"{volley_url}/mcp", model=ScriptedModel([]), bee=fake_bee()) as t:
        offered = t.offered_tools()
    bee_side = [n for n in offered if n.startswith("bee_")]
    assert sorted(bee_side) == sorted(BEE_TOOLS_ALLOWED)
    assert not set(offered) & set(BEE_TOOLS_NEVER)
    assert "how_was_our_talking_today" in offered and "week_trend" in offered


def test_a_quiet_day_is_explained_from_both_servers_and_gated(volley_url):
    import json
    import urllib.request

    week = json.loads(urllib.request.urlopen(f"{volley_url}/v1/households/demo-family/week").read())
    quiet = min(week["days"], key=lambda d: d["turns"])
    script = [
        ("tool", "week_trend", {}),
        ("tool", "bee_get_daily_summary", {"date": quiet["date"]}),
        ("say", f"{quiet['date']} had {quiet['turns']} turns and the Bee's summary of that day says you were at the clinic all afternoon, so the quiet was the calendar."),
    ]
    with Tuesday(f"{volley_url}/mcp", model=ScriptedModel(script), bee=fake_bee()) as t:
        a = t.ask("why was Tuesday quiet")
    assert a.tools_called == ["week_trend", "bee_get_daily_summary"]
    assert a.layer == "model", a.refused


def test_an_invented_number_is_refused_with_two_servers_too(volley_url):
    script = [
        ("tool", "bee_get_daily_summary", {"date": "2026-09-23"}),
        ("say", "You were at the clinic, and most families would have had 60 turns that day."),
        ("say", "You were at the clinic; other families manage 60."),
    ]
    with Tuesday(f"{volley_url}/mcp", model=ScriptedModel(script), bee=fake_bee()) as t:
        a = t.ask("why was Tuesday quiet")
    assert a.layer == "plain" and "60" in a.refused[0]
