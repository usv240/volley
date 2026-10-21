"""A SIMULATED Bee: an MCP server over stdio that plays the parent's Bee
for Volley's simulated household, and nobody else.

The real Bee (`bee mcp serve`) holds a real person's days, work
meetings included, and none of that may reach a model in a recorded
run. This server stands in for it. It offers the four tools Tuesday is
allowed, and bee_get_today, which Tuesday refuses, under the names and argument shapes `bee mcp serve` uses
(read from the @beeai/cli 0.7.3 tool definitions: camelCase
`startDate`/`endDate`, `id` or `date`, `text` and `alarmAt`), and
answers them from fourteen short days written for the demo household
of apps/server/volley_server/demo.py: Asha, 2026-09-15 to 2026-09-28,
at daycare on weekday middays and home at weekends, as the counts are.
The quietest day of the simulated week, 2026-09-24, has an ordinary
reason: a long drive to the grandparents and a late nap.

Every response carries ``"simulated": true`` and a SIMULATED notice,
and so does every tool description. It also offers one tool the
allow-list refuses, `bee_get_conversation_transcript`, so a test can
show Tuesday never passes it to the model.

    python -m volley_agent.sim_bee        # stdio; for Tuesday's --sim-bee
"""

from __future__ import annotations

import json
from typing import Annotated

from pydantic import Field

try:
    from mcp.server.mcpserver import MCPServer as Server  # mcp 2.x
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

NOTICE = "SIMULATED Bee: synthetic days written for Volley's simulated household (child: Asha). No real person's data."
TIMEZONE = "America/Los_Angeles"
TODAY = "2026-09-28"  # the simulated household's latest day

# Written as a Bee daily summary reads: second person, the day's shape,
# no quotes. Times are in words so the gate's allowed numbers stay the
# ones Volley returned.
DAYS: dict[str, tuple[str, str]] = {
    "2026-09-15": (
        "A work day, then the park on the way home from daycare.",
        "You picked Asha up from daycare and stopped at the park on the way home. After dinner there was a bath and two picture books before bed.",
    ),
    "2026-09-16": (
        "A late finish at work and a quick dinner.",
        "Work ran late, so dinner was quick. Asha helped stir the soup and talked about the sandpit at daycare. Bedtime was on time.",
    ),
    "2026-09-17": (
        "An evening walk to the library.",
        "After daycare you and Asha walked to the library and she chose three books about trains. You read one of them twice at bedtime.",
    ),
    "2026-09-18": (
        "Pizza night at home.",
        "A regular work day. In the evening you made pizza at home, then a long bath and building blocks on the living room floor.",
    ),
    "2026-09-19": (
        "Home all day: the market, painting, the garden.",
        "A Saturday at home. The farmers market in the morning, painting at the kitchen table before lunch, and a long afternoon in the garden with Asha.",
    ),
    "2026-09-20": (
        "A slow Sunday at home.",
        "Pancakes for breakfast, a neighbour stopped by with a puppy, and Asha built a tower out of blocks most of the afternoon.",
    ),
    "2026-09-21": (
        "A tired Monday and an early bedtime.",
        "A long work day. Asha was tired after daycare, so it was dinner, bath and an early bedtime.",
    ),
    "2026-09-22": (
        "Groceries with Asha after daycare.",
        "You did the grocery shop with Asha after daycare; she named the fruit as it went into the trolley. An ordinary evening at home after that.",
    ),
    "2026-09-23": (
        "Swimming lesson after daycare.",
        "Asha had her swimming lesson after daycare and was chatty all through dinner about the floats. Bedtime was a little late.",
    ),
    "2026-09-24": (
        "A long drive to the grandparents and back; Asha napped late.",
        "You left work early and drove Asha to her grandparents' house for dinner, a long drive each way. Asha fell asleep in the car on the way there and napped late into the afternoon, then slept again for most of the drive home. Most of the evening was spent in the car, and she went from the car seat straight to bed.",
    ),
    "2026-09-25": (
        "Back to routine after the trip.",
        "A regular work day. Asha talked about her grandparents' dog all evening, and there were songs at bath time.",
    ),
    "2026-09-26": (
        "Home all day: baking and the duck pond.",
        "A Saturday at home. You baked banana bread together in the morning and walked to the duck pond in the afternoon; Asha had a lot of questions about the ducks.",
    ),
    "2026-09-27": (
        "A puppet show and a quieter afternoon.",
        "A Sunday at home. Tidying in the morning, a puppet show Asha put on after lunch, and a quieter afternoon with puzzles.",
    ),
    "2026-09-28": (
        "An ordinary Monday evening.",
        "A regular work day. After daycare: dinner, bath and stories, and Asha asked when she would see her grandparents again.",
    ),
}

TODOS: list[dict] = [
    {"id": 701, "text": "Pack Asha's swim bag", "completed": False, "alarm_at": None},
    {"id": 702, "text": "Return the train books to the library", "completed": False, "alarm_at": None},
    {"id": 703, "text": "Send the grandparents the photos from Thursday", "completed": False, "alarm_at": None},
]


def summary(date: str) -> dict:
    ids = sorted(DAYS)
    short, long = DAYS[date]
    return {
        "id": 5001 + ids.index(date),
        "date": date,
        "short_summary": short,
        "summary": "## Summary\n\n" + long,
        "simulated": True,
    }


def marked(payload: dict) -> str:
    """Every answer, whatever the tool: the notice first, then the data."""
    return json.dumps({"notice": NOTICE, "simulated": True, **payload})


server = Server("simulated-bee", log_level="ERROR")


@server.tool(
    name="bee_get_daily_summary",
    description="SIMULATED. Get a Bee daily summary by ID or YYYY-MM-DD date, including context from conversations and other wearable-captured activity.",
)
def bee_get_daily_summary(
    id: Annotated[int | None, Field(description="Bee daily summary ID.")] = None,
    date: Annotated[str | None, Field(description="Date as YYYY-MM-DD.")] = None,
) -> str:
    if id is not None:
        match = [d for d in DAYS if summary(d)["id"] == id]
        date = match[0] if match else None
        if date is None:
            return marked({"id": id, "daily_summary": None})
    if not date:
        return marked({"error": "Provide id or date."})
    date = date[:10]
    if date not in DAYS:
        return marked({"date": date, "dailySummary": None})
    return marked({"daily_summary": summary(date), "timezone": TIMEZONE})


@server.tool(
    name="bee_list_daily_summaries",
    description="SIMULATED. List Bee daily summaries over a date range to find days with relevant captured conversations or activity.",
)
def bee_list_daily_summaries(
    startDate: Annotated[str | None, Field(description="Start date as YYYY-MM-DD.")] = None,
    endDate: Annotated[str | None, Field(description="End date as YYYY-MM-DD.")] = None,
    limit: Annotated[int, Field(description="Maximum summaries to return.")] = 10,
) -> str:
    lo, hi = (startDate or "0000-00-00")[:10], (endDate or "9999-99-99")[:10]
    dates = [d for d in sorted(DAYS, reverse=True) if lo <= d <= hi][: max(1, min(int(limit), 30))]
    return marked({"daily_summaries": [summary(d) for d in dates], "timezone": TIMEZONE})


@server.tool(
    name="bee_get_today",
    description="SIMULATED. Show today's Bee wearable context: daily summary, active todos, notes, and captured conversations.",
)
def bee_get_today() -> str:
    return marked(
        {
            "date": TODAY,
            "daily_summary": summary(TODAY),
            "todos": [t for t in TODOS if not t["completed"]],
            "notes": [],
            "conversations": [],
            "timezone": TIMEZONE,
        }
    )


@server.tool(
    name="bee_list_todos",
    description="SIMULATED. List active Bee todos. Paginate with cursor using the returned next_cursor.",
)
def bee_list_todos(
    limit: Annotated[int, Field(description="Maximum todos to return.")] = 20,
    cursor: Annotated[str | None, Field(description="Pagination cursor.")] = None,
) -> str:
    active = [t for t in TODOS if not t["completed"]][: max(1, min(int(limit), 50))]
    return marked({"todos": active, "next_cursor": None, "timezone": TIMEZONE})


@server.tool(name="bee_create_todo", description="SIMULATED. Create a Bee todo.")
def bee_create_todo(
    text: Annotated[str, Field(min_length=1, max_length=2000, description="Todo text.")],
    alarmAt: Annotated[str | None, Field(description="Optional reminder time as an ISO date string.")] = None,
) -> str:
    todo = {"id": 701 + len(TODOS), "text": text, "completed": False, "alarm_at": alarmAt}
    TODOS.append(todo)
    return marked({"todo": todo})


@server.tool(
    name="bee_get_conversation_transcript",
    description="SIMULATED. Get ASR transcript utterances for one captured Bee conversation. Tuesday's allow-list never offers this tool.",
)
def bee_get_conversation_transcript(id: int, since: float | None = None) -> str:
    return marked({"id": id, "utterances": [{"speaker": "Asha", "text": "SIM-TRANSCRIPT-SENTINEL the tower fell"}]})


if __name__ == "__main__":
    server.run(transport="stdio")
