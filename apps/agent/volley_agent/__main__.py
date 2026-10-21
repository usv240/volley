"""Ask the agents from a terminal.

    volley-agent coach "how was our talking today"
    volley-agent tuesday "why was Tuesday quiet"
    volley-agent coach --demo "what is the best hour this week"
    volley-agent tuesday --sim-bee "which day this week was the quietest"

Without --demo the household comes from ~/.volley/household.json, the
file `volley connect` wrote, so the agent speaks about the parent's
own days. The answer is printed with the layer that produced it and
the tools it called, and any refused sentence is printed after it,
so a run is its own evidence.

--sim-bee puts the SIMULATED Bee of sim_bee.py where the parent's Bee
would be, and implies --demo: a simulated Bee speaks only for the
simulated household. --record PATH writes the whole run as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from .coach import Coach, tool_results
from .tuesday import Tuesday, sim_bee_client

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
    p.add_argument("--sim-bee", action="store_true", help="tuesday only: the SIMULATED Bee, on the simulated household")
    p.add_argument("--record", metavar="PATH", help="write the question, tools, answer and model to PATH as JSON")
    args = p.parse_args(argv)

    if args.sim_bee:
        if args.agent != "tuesday":
            print("--sim-bee is for the tuesday agent", file=sys.stderr)
            return 2
        args.demo = True
    hid, key = (None, None) if args.demo else household_from_disk()
    if not args.demo and hid is None:
        print("no connected household in ~/.volley; run volley connect, or pass --demo", file=sys.stderr)
        return 2
    if args.agent == "coach":
        agent = Coach(args.mcp, hid, key)
    else:
        agent = Tuesday(args.mcp, hid, key, bee=sim_bee_client() if args.sim_bee else None)
    with agent:
        answer = agent.ask(args.question)
        if args.record:
            record(args, agent, answer, argv)
    if args.json:
        print(json.dumps(answer.__dict__, indent=1))
        return 0
    print(answer.text)
    print(f"  [{answer.layer}; tools: {', '.join(answer.tools_called) or 'none'}]")
    for r in answer.refused:
        print(f"  refused: {r}")
    return 0


def record(args, agent, answer, argv) -> None:
    run = {
        "label": "SIMULATED Bee, simulated household" if args.sim_bee else ("simulated household" if args.demo else "own household"),
        "simulated_bee": bool(args.sim_bee),
        "bee_server": "python -m volley_agent.sim_bee (SIMULATED)" if args.sim_bee else ("bee mcp serve" if args.agent == "tuesday" else None),
        "household": "demo-family (simulated)" if args.demo else "own",
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": "python -m volley_agent " + " ".join(_quote(a) for a in (sys.argv[1:] if argv is None else argv)),
        "mcp_url": args.mcp,
        "model": getattr(agent, "models_used", None),
        "question": args.question,
        "tools_offered": sorted(agent.agent.tool_names),
        "tools_called": answer.tools_called,
        "tool_calls": [b["toolUse"] for m in agent.agent.messages for b in m.get("content", []) if "toolUse" in b],
        "answer": answer.text,
        "layer": answer.layer,
        "refused": answer.refused,
        "tool_results": tool_results(agent.agent.messages),
    }
    with open(args.record, "w", encoding="utf-8") as f:
        json.dump(run, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _quote(a: str) -> str:
    return f'"{a}"' if " " in a or not a else a


if __name__ == "__main__":
    raise SystemExit(main())
