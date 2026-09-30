"""A Volley server on a free port for the agent to talk to, and a model
that says what the test tells it to.

The server is the real one, in memory, seeded with the simulated
household, so the MCP tools the agent wraps are the seven that ship.
The scripted model replaces Bedrock: each turn it either calls a tool
or says a sentence, in the order the test wrote, which is how a test
can make it invent a number and watch the gate refuse it.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any

import pytest
import uvicorn
from strands.models.model import Model

from volley_server.app import build_app


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def volley_url():
    port = free_port()
    config = uvicorn.Config(build_app(), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


class ScriptedModel(Model):
    """Turns are ("tool", name, input) or ("say", text); one per call."""

    def __init__(self, script: list[tuple]):
        self.script = list(script)
        self.calls: list[list[dict]] = []

    def get_config(self) -> dict:
        return {"model_id": "scripted"}

    def update_config(self, **kwargs: Any) -> None:
        pass

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        self.calls.append(list(messages))
        if not self.script:
            turn = ("say", "I have nothing scripted.")
        else:
            turn = self.script.pop(0)
        yield {"messageStart": {"role": "assistant"}}
        if turn[0] == "tool":
            _, name, payload = turn
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"t{len(self.calls)}", "name": name}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(payload)}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": turn[1]}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": {"usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}, "metrics": {"latencyMs": 0}}}
