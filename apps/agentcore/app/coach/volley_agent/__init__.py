"""The Coach and its gate, vendored for AgentCore Runtime. The Tuesday agent
runs on the parent's machine beside Bee's own MCP server and is not hosted."""

from .coach import Answer, Coach
from .gate import check, numbers_returned, plain_rendering

__all__ = ["Answer", "Coach", "check", "numbers_returned", "plain_rendering"]
