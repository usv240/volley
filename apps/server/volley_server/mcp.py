"""MCP server for Volley: Model Context Protocol spec revision 2025-11-25
over the Streamable HTTP transport. The Alexa+ surface.

The transport is the one that already runs in three sibling projects,
including the lesson they paid for: a real client terminates a session
with DELETE carrying a JSON content-type and an empty body, which a naive
body parser answers with a 500. Here DELETE never reads a body.

Why an agent surface belongs on this product: the question a parent asks
is spoken and casual ("how was our talking today?", "what should I try
tomorrow?"), and the answer is a count and a sentence. The agent gets
the seven tools below and nothing else. There is no tool that returns a
word of speech, because the server never has one, and a test walks every
tool to prove it.

Transport behaviour, per the spec:
  POST /mcp    JSON-RPC 2.0 requests and notifications, answered as JSON
  GET  /mcp    405 with an Allow header (no server-initiated stream)
  DELETE /mcp  terminates the session (204), unknown session 404
  MCP-Session-Id issued on initialize and required after: missing 400,
  unknown or terminated 404. MCP-Protocol-Version validated when present.
  Origin, when present, must be loopback or an allowed site origin
  (DNS-rebinding guidance), the site's origin being passed in by the
  stack that knows it.
"""

from __future__ import annotations

import json
import os
import re
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from serve_return import accept, pick, template
from serve_return.coach import TARGET_TURNS_PER_HOUR

from .store import Store, key_hash

_LOOPBACK = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")


def is_allowed_origin(origin: str) -> bool:
    """Loopback, or anything named in VOLLEY_ALLOWED_ORIGINS.

    The site's own origin is not written here. The CDK stack knows the
    distribution's domain and passes it in, so the allowlist cannot be
    stale and a fork deployed elsewhere needs no code change. A rule that
    only wrong callers can trip is indistinguishable from a correct rule
    until a right caller turns up, so the test suite checks that a right
    caller is let in, not only that a wrong one is kept out.
    """
    if _LOOPBACK.match(origin):
        return True
    named = {o.strip().rstrip("/") for o in os.environ.get("VOLLEY_ALLOWED_ORIGINS", "").split(",") if o.strip()}
    return origin.rstrip("/") in named


MCP_PROTOCOL_VERSION = "2025-11-25"
FALLBACK_PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "volley-mcp", "version": "0.1.0"}

DISCLAIMER = (
    "Volley counts the back-and-forth between a parent and a child. It is a count, like steps: "
    "not a test of the child, not a comparison with other families, and not a diagnosis. "
    "The words are read on the parent's machine and never kept."
)

INSTRUCTIONS = (
    "Volley counts conversational turns between a parent and their child from the Bee the parent wears, "
    "by the hour, and writes one thing to try tomorrow from the day's counts. Ask how the talking went today, "
    "for the one thing for tomorrow, for the week's trend, or for the best hour. Report only the numbers these "
    "tools return. There is no transcript to ask for: the server never receives one. Never judge the parent, "
    "never compare families, never mention delay, risk or development; it is a count."
)

TOOLS = [
    {
        "name": "what_volley_counts",
        "description": "How Volley counts, in words. Returns the rule and its source, and no data about anybody.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "how_was_our_talking_today",
        "description": "Today's turns with the child, the best hour and the quietest hour with the child present, for one household.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "household_id": {"type": "string", "description": "Omit for the simulated household."},
                "api_key": {"type": "string", "description": "Required for any household that is not the simulated one."},
                "date": {"type": "string", "description": "YYYY-MM-DD; the latest day if omitted."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "one_thing_for_tomorrow",
        "description": "The one thing to try tomorrow, written from the day's counts, with the fact it came from.",
        "inputSchema": {
            "type": "object",
            "properties": {"household_id": {"type": "string"}, "api_key": {"type": "string"}, "date": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "week_trend",
        "description": "Seven days of turns and whether they are going up, down or holding level.",
        "inputSchema": {"type": "object", "properties": {"household_id": {"type": "string"}, "api_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "best_hour_this_week",
        "description": "The hour of the day that had the most turns this week, and its count.",
        "inputSchema": {"type": "object", "properties": {"household_id": {"type": "string"}, "api_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "record_day",
        "description": "Store a day of counts a client already computed with the serve-return package. Counts only; any text field is dropped.",
        "inputSchema": {
            "type": "object",
            "properties": {"household_id": {"type": "string"}, "api_key": {"type": "string"}, "day": {"type": "object"}},
            "required": ["household_id", "api_key", "day"],
            "additionalProperties": False,
        },
    },
    {
        "name": "household_settings",
        "description": "The household's name and the child's name or nickname, so an assistant can address them; no counts.",
        "inputSchema": {"type": "object", "properties": {"household_id": {"type": "string"}, "api_key": {"type": "string"}}, "additionalProperties": False},
    },
]

RULE_IN_WORDS = (
    "A conversational turn is one alternation between the parent and the child within five seconds: the parent "
    "says something and the child answers within five seconds of its end, or the reverse. Consecutive utterances "
    "by the same person merge first, so a monologue is one block. A gap over five seconds ends the exchange. This is "
    "the conversational turn count the developmental studies used, produced by the LENA system from daylong "
    "recordings, and the rule the manual comparison in Child Development hand-counted."
)


def _text(payload) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


def _result(id_, result) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error(id_, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


class ToolError(Exception):
    def __init__(self, message: str, code: int = -32602) -> None:
        super().__init__(message)
        self.code = code


def register_mcp(app: FastAPI, store: Store, demo_household: str, note_deps: dict | None = None) -> None:
    sessions: set[str] = set()

    def resolve(args: dict, write: bool = False) -> dict:
        hid = args.get("household_id") if isinstance(args.get("household_id"), str) and args.get("household_id").strip() else demo_household
        h = store.get_household(hid)
        if h is None:
            raise ToolError("no such household")
        if write or not h.get("simulated"):
            key = args.get("api_key") if isinstance(args.get("api_key"), str) else ""
            if not key or store.household_id_for_key(key_hash(key)) != hid:
                raise ToolError("this household's api_key is required")
        return h

    def latest(h: dict, args: dict) -> dict:
        days = store.list_days(h["household_id"])
        if not days:
            raise ToolError("no days yet")
        date = args.get("date")
        if isinstance(date, str):
            row = next((d for d in days if d["date"] == date), None)
            if row is None:
                raise ToolError("no counts for that date")
            return row
        return days[-1]

    def call_tool(name: str, args: dict) -> dict:
        if name == "what_volley_counts":
            return _text({"rule": RULE_IN_WORDS, "window_seconds": 5, "target_turns_per_hour": TARGET_TURNS_PER_HOUR,
                          "target_source": "LENA's figure, stated as theirs", "data": None, "why_no_data": "This tool explains; it does not report on anybody.", "disclaimer": DISCLAIMER})

        if name == "how_was_our_talking_today":
            h = resolve(args)
            row = latest(h, args)
            return _text({"household_id": h["household_id"], "simulated": h.get("simulated", False), "date": row["date"], "turns": row["turns"],
                          "best_hour": row.get("best_hour"), "quietest_hour_with_child": row.get("quietest_hour_with_child"),
                          "longest_volley": row.get("longest_volley"), "questions_adult": row.get("questions_adult"),
                          "words_discarded": row.get("words_discarded"), "note": "Counts only. No transcript exists here."})

        if name == "one_thing_for_tomorrow":
            from .app import day_from_dict
            from .bedrock import phrase_note

            h = resolve(args)
            row = latest(h, args)
            fact = pick(day_from_dict(row))
            floor = template(fact, h.get("child_name"))
            fact_d = {"kind": fact.kind, "hour": fact.hour, "value": fact.value, "target": fact.target}
            result = phrase_note(fact_d, h.get("child_name"), floor, lambda t: accept(t, fact), note_deps)
            return _text({"household_id": h["household_id"], "simulated": h.get("simulated", False), "date": row["date"], "fact": fact_d,
                          "text": result["text"], "source": result["source"], "model": result["model"], "disclaimer": DISCLAIMER})

        if name == "week_trend":
            from .app import week_view

            h = resolve(args)
            return _text({"household_id": h["household_id"], "simulated": h.get("simulated", False), **week_view(store.list_days(h["household_id"]))})

        if name == "best_hour_this_week":
            h = resolve(args)
            days = store.list_days(h["household_id"])[-7:]
            if not days:
                raise ToolError("no days yet")
            by_hour: dict[int, int] = {}
            for d in days:
                for hr in d.get("hours", []):
                    by_hour[hr["hour"]] = by_hour.get(hr["hour"], 0) + hr.get("turns", 0)
            best = max(by_hour, key=lambda k: by_hour[k]) if by_hour else None
            return _text({"household_id": h["household_id"], "simulated": h.get("simulated", False), "hour": best, "turns_this_week": by_hour.get(best) if best is not None else None, "days": len(days)})

        if name == "record_day":
            from .app import validate_day

            h = resolve(args, write=True)
            day = args.get("day")
            if not isinstance(day, dict):
                raise ToolError("day must be an object of counts")
            try:
                clean = validate_day(day)
            except Exception as err:  # noqa: BLE001
                raise ToolError(str(getattr(err, "detail", err)))
            store.put_day(h["household_id"], clean)
            dropped = sorted(k for k in day if k not in clean)
            return _text({"stored": clean["date"], "household_id": h["household_id"], "dropped_fields": dropped})

        if name == "household_settings":
            h = resolve(args)
            return _text({k: h.get(k) for k in ("household_id", "name", "child_name", "simulated", "created")})

        raise ToolError(f"Unknown tool: {name}")

    @app.post("/mcp")
    async def mcp_post(request: Request):
        origin = request.headers.get("origin")
        if origin and not is_allowed_origin(origin):
            return JSONResponse(_error(None, -32600, "Origin not allowed"), status_code=403)

        raw = await request.body()
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return JSONResponse(_error(None, -32700, "Parse error"), status_code=400)
        if isinstance(body, list):
            return JSONResponse(_error(None, -32600, "Batching is not part of this protocol revision"), status_code=400)
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or not isinstance(body.get("method"), str):
            return JSONResponse(_error(None, -32600, "Invalid JSON-RPC request"), status_code=400)

        msg_id = body.get("id")
        method = body["method"]
        session_id = request.headers.get("mcp-session-id")
        version = request.headers.get("mcp-protocol-version")
        if version is not None and version not in (MCP_PROTOCOL_VERSION, FALLBACK_PROTOCOL_VERSION):
            return JSONResponse(_error(msg_id, -32600, f"Unsupported protocol version: {version}"), status_code=400)

        if method == "initialize":
            new_session = str(uuid.uuid4())
            sessions.add(new_session)
            return JSONResponse(
                _result(msg_id, {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS}),
                headers={"MCP-Session-Id": new_session},
            )

        if not session_id:
            return JSONResponse(_error(msg_id, -32600, "Missing MCP-Session-Id header"), status_code=400)
        if session_id not in sessions:
            return JSONResponse(_error(msg_id, -32001, "Unknown or terminated session"), status_code=404)

        if msg_id is None:
            return Response(status_code=202)

        if method == "ping":
            return JSONResponse(_result(msg_id, {}))
        if method == "tools/list":
            return JSONResponse(_result(msg_id, {"tools": TOOLS}))
        if method == "tools/call":
            params = body.get("params") or {}
            name = params.get("name") if isinstance(params.get("name"), str) else ""
            args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            try:
                return JSONResponse(_result(msg_id, call_tool(name, args)))
            except ToolError as err:
                return JSONResponse(_error(msg_id, err.code, str(err)))
            except Exception as err:  # noqa: BLE001
                return JSONResponse(_error(msg_id, -32603, str(err)))
        return JSONResponse(_error(msg_id, -32601, f"Method not found: {method}"))

    @app.get("/mcp")
    async def mcp_get():
        return Response(status_code=405, headers={"Allow": "POST, DELETE"})

    @app.delete("/mcp")
    async def mcp_delete(request: Request):
        # Never reads a body: a real client sends one, empty, with a JSON
        # content-type, and parsing it is how the siblings got a 500.
        session_id = request.headers.get("mcp-session-id")
        if session_id and session_id in sessions:
            sessions.discard(session_id)
            return Response(status_code=204)
        return Response(status_code=404)
