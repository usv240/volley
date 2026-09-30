"""Ask the agents from a terminal.

    volley-agent coach "how was our talking today"
    volley-agent tuesday "why was Tuesday quiet"
    volley-agent coach --demo "what is the best hour this week"

Without --demo the household comes from ~/.volley/household.json, the
file `volley connect` wrote, so the agent speaks about the parent's
own days. The answer is printed with the layer that produced it and
the tools it called, and any refused sentence is printed after it,
so a run is its own evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .coach import Coach
from .tuesday import Tuesday

DEFAULT_MCP = "https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/mcp"


def household_from_disk() -> tuple[str | None, str | None]:
    try:
        from volley_ingest.household import Household
    except ImportError:
        return None, None
    h = Household.load()
    if h is None or not h.connected:
        return None, None
    return h.household_id, h.api_key


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="volley-agent", description=__doc__.split("\n\n")[0])
    p.add_argument("agent", choices=("coach", "tuesday"))
    p.add_argument("question")
    p.add_argument("--demo", action="store_true", help="the simulated household rather than your own")
    p.add_argument("--mcp", default=os.environ.get("VOLLEY_MCP_URL", DEFAULT_MCP))
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    hid, key = (None, None) if args.demo else household_from_disk()
    if not args.demo and hid is None:
        print("no connected household in ~/.volley; run volley connect, or pass --demo", file=sys.stderr)
        return 2
    cls = Coach if args.agent == "coach" else Tuesday
    with cls(args.mcp, hid, key) as agent:
        answer = agent.ask(args.question)
    if args.json:
        print(json.dumps(answer.__dict__, indent=1))
        return 0
    print(answer.text)
    print(f"  [{answer.layer}; tools: {', '.join(answer.tools_called) or 'none'}]")
    for r in answer.refused:
        print(f"  refused: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
