"""A stand-in for `bee mcp serve` with the real tool names.

The 34 names were captured from the real server on 2026-09-30, so the
allow-list is tested against the surface it will meet. Every tool
returns a small fixed record; the transcript tool returns a sentence
that would be found in a test if it ever reached the model.
"""

from __future__ import annotations

import json

try:
    from mcp.server.mcpserver import MCPServer as Server  # mcp 2.x
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

NAMES = [
    "bee_status", "bee_search", "bee_list_facts", "bee_search_facts", "bee_get_fact", "bee_create_fact", "bee_update_fact",
    "bee_delete_fact", "bee_get_recent_activity", "bee_get_today", "bee_list_conversations", "bee_get_conversation",
    "bee_get_conversation_transcript", "bee_get_related_conversations", "bee_get_daily_summary", "bee_list_daily_summaries",
    "bee_list_voice_notes", "bee_search_voice_notes", "bee_get_voice_note", "bee_list_todos", "bee_create_todo", "bee_update_todo",
    "bee_complete_todo", "bee_delete_todo", "bee_get_todo_suggestions", "bee_accept_todo_suggestion", "bee_dismiss_todo_suggestion",
    "bee_get_insights", "bee_get_insight", "bee_get_location_clusters", "bee_get_recent_visits", "bee_get_current_location",
    "bee_get_photos", "bee_get_photo",
]

server = Server("fake-bee", log_level="ERROR")


def make(name: str):
    def tool(date: str = "", limit: int = 5, text: str = "") -> str:
        if name == "bee_get_daily_summary":
            return json.dumps({"date": date or "2026-09-23", "short_summary": "A clinic visit took the afternoon; a quiet evening at home."})
        if name == "bee_get_conversation_transcript":
            return json.dumps({"utterances": [{"speaker": "Asha", "text": "TRANSCRIPT-SENTINEL the tower fell"}]})
        if name == "bee_create_todo":
            return json.dumps({"id": 1, "text": text})
        return json.dumps({"tool": name, "ok": True})

    tool.__name__ = name
    return tool


for n in NAMES:
    server.add_tool(make(n), name=n, description=f"stand-in for {n}")

if __name__ == "__main__":
    server.run(transport="stdio")
