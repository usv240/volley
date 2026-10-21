"""The Tuesday agent: Bee's own MCP server beside Volley's.

"Why was Tuesday quiet" is a question Volley's counts cannot answer and
the parent's own Bee can: it holds the daily summaries
and the to-do list. This agent runs on the parent's machine and holds both
servers at once. Volley's server sees only what it always sees, a
household id and a key; Bee's server sees only its own calls, made
through the CLI the parent already signed in. Neither is told the
other exists. The only place both sets of facts meet is the model, in
the parent's own AWS account, for the length of one answer.

What the agent may reach on the Bee side is a short allow-list:
daily summaries and the to-do list. The transcript tools,
and today's brief, which returns captured conversations, are not offered, so no word a child said can reach the model
this way either. The list is a constant a test reads.

For a run that must not touch a real person's Bee, `sim_bee_client()`
starts the SIMULATED Bee in sim_bee.py instead, through the same filter.
"""

from __future__ import annotations

import sys

from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.hooks import AfterModelCallEvent
from strands.tools.mcp import MCPClient

from .coach import Answer, check, plain_rendering, spoken, tool_results, tools_used, wrap_tools

BEE_TOOLS_ALLOWED = [
    "bee_get_daily_summary",
    "bee_list_daily_summaries",
    "bee_list_todos",
    "bee_create_todo",
]

# Named so the reason is on record, not only the effect.
BEE_TOOLS_NEVER = [
    # Its description in @beeai/cli 0.7.3 says it returns today's captured
    # conversations, which can carry what anyone in the room said. It was
    # allowed until 2026-10-21, when a reading of the tool definitions for
    # the simulated Bee found that; no recorded run called it.
    "bee_get_today",
    "bee_get_conversation_transcript",
    "bee_get_conversation",
    "bee_list_conversations",
    "bee_get_related_conversations",
    "bee_search",
    "bee_get_photos",
    "bee_get_photo",
    "bee_get_current_location",
    "bee_get_recent_visits",
    "bee_get_location_clusters",
]

SYSTEM = "\n".join(
    [
        "You are Volley's coach, speaking out loud to a parent who wears a Bee, with two sources in front of you.",
        "Volley's tools hold the counts: the back-and-forth between the parent and their child, by the hour and by the day.",
        "The Bee's tools hold the parent's own day: its daily summaries and the to-do list. Use them to explain, never to judge.",
        "Report only numbers a tool returned, in the form it returned them; an hour of 18 may be said as six in the evening.",
        "Say a date as a month and day, never with a day of the week: no tool returns the weekday, so it would be a guess.",
        "Never use the words delay, behind, risk, deficit, disorder, diagnosis, percentile or IQ. It is a count, not a test.",
        "Do not quote anything anyone said; you have no transcript and want none.",
        "If asked to set a reminder, write one to-do with bee_create_todo and say what you wrote.",
        "Three short sentences at most.",
    ]
)


def bee_client(command: list[str] | None = None) -> MCPClient:
    """Bee's MCP server over stdio, through the CLI the parent signed in.
    On Windows the CLI is a .cmd shim, so it runs through cmd."""
    argv = command or ["cmd", "/c", "bee", "mcp", "serve"]
    return MCPClient(
        lambda: stdio_client(StdioServerParameters(command=argv[0], args=argv[1:])),
        tool_filters={"allowed": list(BEE_TOOLS_ALLOWED)},
    )


def sim_bee_client() -> MCPClient:
    """The SIMULATED Bee of sim_bee.py, for the simulated household only.
    Same allow-list filter as the real one."""
    return bee_client([sys.executable, "-m", "volley_agent.sim_bee"])


def _model_name(event) -> str | None:
    """Which model produced a response: the router's rung, or the model's id."""
    for key, state in event.invocation_state.items():
        if str(key).startswith("strands:model_routing") and getattr(state, "candidate", None) is not None:
            return state.candidate.name
    try:
        return event.agent.model.get_config().get("model_id")
    except Exception:
        return None


class Tuesday:
    def __init__(self, mcp_url: str, household_id: str | None = None, api_key: str | None = None, model=None, bee: MCPClient | None = None):
        self.volley = MCPClient(url=mcp_url)
        self.bee = bee or bee_client()
        self.household_id = household_id
        self.api_key = api_key
        self.model = model
        self.agent: Agent | None = None
        self.models_used: list[str] = []

    def __enter__(self) -> "Tuesday":
        self.volley.__enter__()
        self.bee.__enter__()
        model = self.model
        if model is None:
            from .models import bedrock_router

            model = bedrock_router()
        tools = wrap_tools(self.volley, self.household_id, self.api_key) + self.bee.list_tools_sync()
        offered = {t.tool_name for t in tools}
        assert not offered & set(BEE_TOOLS_NEVER), offered & set(BEE_TOOLS_NEVER)
        self.agent = Agent(model=model, tools=tools, system_prompt=SYSTEM, callback_handler=None)
        self.agent.add_hook(self._note_model, AfterModelCallEvent)
        return self

    def _note_model(self, event: AfterModelCallEvent) -> None:
        if event.stop_response is not None:
            name = _model_name(event)
            if name and name not in self.models_used:
                self.models_used.append(name)

    def __exit__(self, *exc) -> None:
        self.bee.__exit__(*exc)
        self.volley.__exit__(*exc)

    def offered_tools(self) -> list[str]:
        assert self.agent is not None
        return sorted(self.agent.tool_names)

    def ask(self, question: str) -> Answer:
        assert self.agent is not None, "use the agent inside a with block"
        text = spoken(str(self.agent(question)))
        results = tool_results(self.agent.messages)
        verdict = check(text, results)
        if verdict.ok:
            return Answer(text, "model", tools_used(self.agent.messages))
        refused = [f"{text}  <- {verdict.reason()}"]
        text = spoken(str(self.agent("That answer was not repeated to the parent because it contained " + verdict.reason() + ". Say it again from the tools only.")))
        results = tool_results(self.agent.messages)
        verdict = check(text, results)
        if verdict.ok:
            return Answer(text, "model-after-correction", tools_used(self.agent.messages), refused)
        refused.append(f"{text}  <- {verdict.reason()}")
        return Answer(plain_rendering(results), "plain", tools_used(self.agent.messages), refused)
