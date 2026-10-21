"""The SIMULATED Bee, and Tuesday holding it.

sim_bee.py stands in for the parent's Bee in a recorded run, so no real
person's day reaches the model. The claims: it offers exactly the five
tools Tuesday is allowed plus one the allow-list refuses; Tuesday,
given it, never offers the refused one; every answer it gives is marked
SIMULATED; it has a day for every date of the simulated household,
including the quiet one; and a quiet-day answer built from both servers
passes the gate. No Bedrock and no network: the model is scripted and
Volley is the in-memory server on a free port.
"""

from __future__ import annotations

import json
import sys
import urllib.request

from conftest import ScriptedModel
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient
from volley_agent.__main__ import main
from volley_agent.tuesday import BEE_TOOLS_ALLOWED, BEE_TOOLS_NEVER, Tuesday, sim_bee_client

REFUSED = "bee_get_conversation_transcript"


def unfiltered_sim_bee() -> MCPClient:
    return MCPClient(lambda: stdio_client(StdioServerParameters(command=sys.executable, args=["-m", "volley_agent.sim_bee"])))


def text_of(result: dict) -> str:
    return "".join(c["text"] for c in result["content"] if "text" in c)


def test_the_sim_bee_offers_exactly_the_allowed_tools_and_the_refused_one():
    with unfiltered_sim_bee() as bee:
        names = sorted(t.tool_name for t in bee.list_tools_sync())
    assert REFUSED in BEE_TOOLS_NEVER
    # It also plays bee_get_today, which Tuesday refuses because it returns conversations.
    assert names == sorted(BEE_TOOLS_ALLOWED + [REFUSED, "bee_get_today"])
    assert "bee_get_today" in BEE_TOOLS_NEVER


def test_tuesday_given_the_sim_bee_never_offers_the_refused_tool(volley_url):
    with Tuesday(f"{volley_url}/mcp", model=ScriptedModel([]), bee=sim_bee_client()) as t:
        offered = t.offered_tools()
    assert REFUSED not in offered
    assert not set(offered) & set(BEE_TOOLS_NEVER)
    assert sorted(n for n in offered if n.startswith("bee_")) == sorted(BEE_TOOLS_ALLOWED)


def test_every_sim_bee_answer_is_marked_simulated():
    calls = [
        ("bee_get_daily_summary", {"date": "2026-09-24"}),
        ("bee_get_daily_summary", {"date": "2026-01-01"}),
        ("bee_list_daily_summaries", {"startDate": "2026-09-22", "endDate": "2026-09-28"}),
        ("bee_get_today", {}),
        ("bee_list_todos", {}),
        ("bee_create_todo", {"text": "Read the train book at six"}),
        (REFUSED, {"id": 1}),
    ]
    with unfiltered_sim_bee() as bee:
        for name, args in calls:
            tool = next(t for t in bee.list_tools_sync() if t.tool_name == name)
            assert tool.tool_spec["description"].startswith("SIMULATED."), name
            data = json.loads(text_of(bee.call_tool_sync(tool_use_id=name, name=name, arguments=args)))
            assert data["simulated"] is True and data["notice"].startswith("SIMULATED Bee"), name


def test_the_sim_bee_has_a_day_for_every_simulated_date_and_explains_the_quiet_one(volley_url):
    week = json.loads(urllib.request.urlopen(f"{volley_url}/v1/households/demo-family/week").read())
    assert week["simulated"] is True
    with unfiltered_sim_bee() as bee:
        for day in week["days"]:
            data = json.loads(text_of(bee.call_tool_sync(tool_use_id="d", name="bee_get_daily_summary", arguments={"date": day["date"]})))
            assert data["daily_summary"]["simulated"] is True, day["date"]
        quiet = json.loads(text_of(bee.call_tool_sync(tool_use_id="q", name="bee_get_daily_summary", arguments={"date": week["quietest_day"]})))
    assert "grandparents" in quiet["daily_summary"]["summary"] and "nap" in quiet["daily_summary"]["summary"]


def test_a_quiet_day_answer_from_volley_and_the_sim_bee_passes_the_gate(volley_url):
    week = json.loads(urllib.request.urlopen(f"{volley_url}/v1/households/demo-family/week").read())
    quiet = next(d for d in week["days"] if d["date"] == week["quietest_day"])
    script = [
        ("tool", "week_trend", {}),
        ("tool", "bee_get_daily_summary", {"date": quiet["date"]}),
        ("say", f"{quiet['date']} had {quiet['turns']} turns; your simulated Bee says it was the long drive to Asha's grandparents and a late nap."),
    ]
    with Tuesday(f"{volley_url}/mcp", model=ScriptedModel(script), bee=sim_bee_client()) as t:
        a = t.ask("which day this week was the quietest, and what was I doing")
        assert t.models_used == ["scripted"]
    assert a.tools_called == ["week_trend", "bee_get_daily_summary"]
    assert a.layer == "model", a.refused


def test_sim_bee_on_the_command_line_is_for_tuesday_only(capsys):
    assert main(["coach", "--sim-bee", "how was today"]) == 2
    assert "tuesday" in capsys.readouterr().err
