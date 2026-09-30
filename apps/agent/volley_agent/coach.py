"""The coach: a Strands agent over Volley's MCP server.

It answers a parent the way Alexa+ would, from the seven tools and
nothing else. The household's id and key never pass through the model:
each MCP tool is wrapped so the model sees no credential argument and
the wrapper adds them on the way out. Every answer goes through the
gate before it is returned; a refused answer is sent back once with the
violation named, and a second refusal is replaced by the tool results
read out plainly. The result says which happened.

    coach = Coach(mcp_url, household_id, api_key)
    with coach:
        answer = coach.ask("how was our talking today")

The model is the Bedrock ladder unless one is injected, which is how
the tests drive it without an AWS account.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from strands import Agent
from strands.tools import PythonAgentTool
from strands.tools.mcp import MCPClient

from .gate import check, plain_rendering, spoken

CREDENTIAL_ARGS = ("household_id", "api_key")

SYSTEM = "\n".join(
    [
        "You are Volley's coach, speaking out loud to a parent who wears a Bee.",
        "Volley counts the back-and-forth between the parent and their child, by the hour, like steps.",
        "Answer from the tools. Call one before you say any number, and report only numbers a tool returned,",
        "in the form it returned them; an hour of 18 may be said as six in the evening.",
        "It is a count: not a test of the child, not a comparison with other families, not a diagnosis.",
        "Never judge the parent. Never use the words delay, behind, risk, deficit, disorder, diagnosis, percentile or IQ.",
        "There is no transcript to ask for; the server never receives one, and neither do you.",
        "Two or three short sentences. Warm, plain, specific, and nothing the tools did not say.",
    ]
)


@dataclass
class Answer:
    text: str
    layer: str                       # model | model-after-correction | plain
    tools_called: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)


def tool_results(messages: list[dict]) -> list[str]:
    """The text of every tool result in the conversation so far."""
    out: list[str] = []
    for m in messages:
        for block in m.get("content", []):
            tr = block.get("toolResult")
            if tr:
                out.extend(c["text"] for c in tr.get("content", []) if "text" in c)
    return out


def tools_used(messages: list[dict]) -> list[str]:
    return [b["toolUse"]["name"] for m in messages for b in m.get("content", []) if "toolUse" in b]


def without_credentials(spec: dict) -> dict:
    """The tool as the model sees it: same name and description, the
    credential arguments removed from the schema."""
    schema = json.loads(json.dumps(spec.get("inputSchema", {})))
    props = schema.get("properties", {})
    for k in CREDENTIAL_ARGS:
        props.pop(k, None)
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r not in CREDENTIAL_ARGS]
    return {"name": spec["name"], "description": spec["description"], "inputSchema": schema}


def wrap_tools(client: MCPClient, household_id: str | None, api_key: str | None) -> list[PythonAgentTool]:
    tools = []
    for t in client.list_tools_sync():
        spec = without_credentials(t.tool_spec)
        name = t.tool_name

        def call(tool_use: dict, _name=name, **_: Any) -> dict:
            args = dict(tool_use.get("input") or {})
            if household_id:
                args["household_id"] = household_id
            if api_key:
                args["api_key"] = api_key
            result = client.call_tool_sync(tool_use_id=tool_use["toolUseId"], name=_name, arguments=args)
            return {"toolUseId": tool_use["toolUseId"], "status": result["status"], "content": result["content"]}

        call.__name__ = name
        tools.append(PythonAgentTool(name, spec, call))
    return tools


class Coach:
    def __init__(self, mcp_url: str, household_id: str | None = None, api_key: str | None = None, model=None):
        self.client = MCPClient(url=mcp_url)
        self.household_id = household_id
        self.api_key = api_key
        self.model = model
        self.agent: Agent | None = None

    def __enter__(self) -> "Coach":
        self.client.__enter__()
        model = self.model
        if model is None:
            from .models import bedrock_router

            model = bedrock_router()
        self.agent = Agent(model=model, tools=wrap_tools(self.client, self.household_id, self.api_key), system_prompt=SYSTEM, callback_handler=None)
        return self

    def __exit__(self, *exc) -> None:
        self.client.__exit__(*exc)

    def ask(self, question: str) -> Answer:
        assert self.agent is not None, "use the coach inside a with block"
        text = spoken(str(self.agent(question)))
        results = tool_results(self.agent.messages)
        verdict = check(text, results)
        if verdict.ok:
            return Answer(text, "model", tools_used(self.agent.messages))
        refused = [f"{text}  <- {verdict.reason()}"]
        correction = (
            "That answer was not repeated to the parent because it contained "
            + verdict.reason()
            + ". Say it again using only numbers the tools returned and none of those words."
        )
        text = spoken(str(self.agent(correction)))
        results = tool_results(self.agent.messages)
        verdict = check(text, results)
        if verdict.ok:
            return Answer(text, "model-after-correction", tools_used(self.agent.messages), refused)
        refused.append(f"{text}  <- {verdict.reason()}")
        return Answer(plain_rendering(results), "plain", tools_used(self.agent.messages), refused)
