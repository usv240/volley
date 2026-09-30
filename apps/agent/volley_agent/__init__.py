"""Two Strands agents over Volley's MCP server.

`Coach` answers a parent from Volley's seven tools and cannot say a
number no tool returned. `Tuesday` holds Bee's own MCP server beside
Volley's, on the parent's machine, so a quiet day can be explained
from the parent's own calendar without either server seeing the
other's data. Both put every answer through the same gate.
"""

from .coach import Answer, Coach
from .gate import check, numbers_returned, plain_rendering
from .tuesday import BEE_TOOLS_ALLOWED, BEE_TOOLS_NEVER, Tuesday

__all__ = ["Answer", "Coach", "Tuesday", "check", "numbers_returned", "plain_rendering", "BEE_TOOLS_ALLOWED", "BEE_TOOLS_NEVER"]
