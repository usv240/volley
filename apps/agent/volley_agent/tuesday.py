"""The Tuesday agent: Bee's own MCP server beside Volley's.

"Why was Tuesday quiet" is a question Volley's counts cannot answer and
the parent's own Bee can: it holds the day's summary, the calendar and
the to-do list. This agent runs on the parent's machine and holds both
servers at once. Volley's server sees only what it always sees, a
household id and a key; Bee's server sees only its own calls, made
through the CLI the parent already signed in. Neither is told the
other exists. The only place both sets of facts meet is the model, in
the parent's own AWS account, for the length of one answer.

What the agent may reach on the Bee side is a short allow-list:
daily summaries, today's brief, and the to-do list. The transcript
tools are not offered, so no word a child said can reach the model
this way either. The list is a constant a test reads.
"""

from __future__ import annotations

from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient

from .coach import Answer, check, plain_rendering, spoken, tool_results, tools_used, wrap_tools

BEE_TOOLS_ALLOWED = [
    "bee_get_daily_summary",
    "bee_list_daily_summaries",
    "bee_get_today",
    "bee_list_todos",
    "bee_create_todo",
]

# Named so the reason is on record, not only the effect.
BEE_TOOLS_NEVER = [
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
        "The Bee's tools hold the parent's own day: its summary, the calendar, the to-do list. Use them to explain, never to judge.",
        "Report only numbers a tool returned, in the form it returned them; an hour of 18 may be said as six in the evening.",
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


class Tuesday:
    def __init__(self, mcp_url: str, household_id: str | None = None, api_key: str | None = None, model=None, bee: MCPClient | None = None):
        self.volley = MCPClient(url=mcp_url)
        self.bee = bee or bee_client()
        self.household_id = household_id
        self.api_key = api_key
        self.model = model
        self.agent: Agent | None = None

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
        return self

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
