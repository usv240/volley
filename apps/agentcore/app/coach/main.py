"""Volley's Coach, hosted on Amazon Bedrock AgentCore Runtime.

Invoke with {"prompt": "how was our talking today"}. The Coach is the same
Strands agent as apps/agent: it answers a parent from Volley's MCP tools
only (the endpoint Alexa+ uses, spec 2025-11-25 over Streamable HTTP), and
every answer passes the gate, which refuses any number no tool returned and
any forbidden word; a refused answer is corrected once, then replaced by a
plain rendering of the tool results.

The volley_agent and serve_return modules here are copies of the ones in
the repository; apps/agent/tests/test_agentcore_copy.py fails if they
differ. The runtime speaks about the simulated demo household only: a
parent's own household needs their key, which never leaves their machine.
"""

from __future__ import annotations

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from volley_agent import Coach

app = BedrockAgentCoreApp()
log = app.logger

MCP_URL = os.environ.get("VOLLEY_MCP_URL", "https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/mcp")


@app.entrypoint
def invoke(payload, context):
    question = "how was our talking today"
    if isinstance(payload, dict) and isinstance(payload.get("prompt"), str) and payload["prompt"].strip():
        question = payload["prompt"].strip()
    log.info("coach: %s", question)
    with Coach(MCP_URL) as coach:
        answer = coach.ask(question)
    return {**answer.__dict__, "household": "the simulated demo household", "runtime": "Amazon Bedrock AgentCore Runtime"}


if __name__ == "__main__":
    app.run()
