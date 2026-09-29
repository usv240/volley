"""A publishable record that live Bee data flowed through Volley.

Counts, shapes and the day's numbers; never a word, a name, a title or
a place. The words are counted so the record can say how many were read
and that zero were written, which is the product in one line.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .bee import BeeCli, BeeCliError, normalize_conversation, with_utterances
from .days import count_days, words_in
from .household import Household


def shape(value, depth: int = 0):
    """Field names and value types, with every string reduced to its length."""
    if depth > 4:
        return "..."
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in list(value.items())[:20]}
    if isinstance(value, list):
        return [shape(value[0], depth + 1)] if value else []
    if isinstance(value, str):
        return f"<string, {len(value)} chars>"
    if isinstance(value, bool):
        return "<bool>"
    if isinstance(value, (int, float)):
        return "<number>"
    return "<null>" if value is None else f"<{type(value).__name__}>"


def build(cli: BeeCli, h: Household) -> dict:
    out: dict = {"captured": datetime.now(timezone.utc).isoformat(timespec="seconds"), "calls": [], "shapes": {}}

    def attempt(label: str, argv_hint: str, fn):
        try:
            result = fn()
            out["calls"].append({"call": label, "command": argv_hint, "ok": True})
            out["shapes"][label] = shape(result)
            return result
        except BeeCliError as err:
            out["calls"].append({"call": label, "command": argv_hint, "ok": False, "error": str(err)[:160]})
            return None

    attempt("account", "bee me --json", cli.me)
    attempt("recent hours", "bee now --json", cli.now)
    convos = attempt("conversations", "bee conversations list --json", lambda: cli.conversations_list(limit=50))
    rows = convos.get("conversations", []) if isinstance(convos, dict) else (convos or [])
    records = with_utterances(cli, rows)
    if records:
        out["shapes"]["conversation"] = shape(records[0])
    utterances = []
    for raw in records:
        utterances.extend(normalize_conversation(raw))
    out["conversations"] = len(rows)
    out["utterances"] = len(utterances)
    out["speakers"] = sorted({u.speaker or "?" for u in utterances})
    out["words_read"] = words_in(utterances)
    out["words_published"] = 0
    days = count_days(utterances, h) if h.parent_labels and h.child_labels else []
    del utterances
    out["days"] = [d.to_dict() for d in days]
    out["household_configured"] = bool(h.parent_labels and h.child_labels)
    return out


def render(r: dict) -> str:
    ok = sum(1 for c in r["calls"] if c["ok"])
    lines = [
        "# Live Bee data: what actually came back",
        "",
        "Evidence that Volley reads a real Bee device, captured by `volley evidence`.",
        "",
        f"Captured: {r['captured']}. Commands answering: {ok} of {len(r['calls'])}.",
        "",
        "Counts, shapes and the day's numbers only. No transcript text, no titles, no names, no places.",
        "",
        "## Commands",
        "",
        "| Call | Command | Result |",
        "|---|---|---|",
    ]
    for c in r["calls"]:
        lines.append(f"| {c['call']} | `{c['command']}` | {'answered' if c['ok'] else 'failed: ' + c.get('error', '')} |")
    lines += [
        "",
        "## What the device returned",
        "",
        f"- Conversations: {r['conversations']}",
        f"- Utterances: {r['utterances']}",
        f"- Speaker labels seen: {len(r['speakers'])}",
        f"- Words read on this machine: {r['words_read']}",
        f"- Words written to this file: {r['words_published']}",
        "",
        "That last pair is the product in one line.",
        "",
    ]
    if r["household_configured"]:
        lines += ["## The day, in counts", "", "```json", json.dumps(r["days"], indent=1), "```", ""]
    else:
        lines += ["## The day", "", "No household is set up yet, so no roles were assigned and nothing was counted. Run `volley setup`.", ""]
    lines += ["## Response shapes", "", "```json", json.dumps(r["shapes"], indent=1), "```", ""]
    return "\n".join(lines)
