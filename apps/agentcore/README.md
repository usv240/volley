# Volley's Coach, hosted on Amazon Bedrock AgentCore

The same Coach that runs locally in [`apps/agent`](../agent), deployed to AgentCore Runtime as an invocable endpoint.

```
Runtime: volleycoach_coach
Region:  us-east-1
```

The Coach answers a parent from Volley's MCP tools only (the endpoint Alexa+ uses, spec 2025-11-25 over Streamable HTTP). Every answer passes the gate: any number no tool returned, or any forbidden word, is refused; the Coach is corrected once, and a second refusal falls back to a plain rendering of the tool results. The hosted runtime speaks about the simulated demo household only, because a parent's own household needs their key, which never leaves their machine.

## Verified running, 2026-10-19

```
npx @aws/agentcore invoke --prompt "how was our talking this week, and what is the best hour?"
```

It called Volley's tools and answered with the week's trend, the best and quietest days and the best hour, every number from a tool; the gate refused nothing (`"layer": "model"`, `"refused": []`).

## Deploy it yourself

```
cd apps/agentcore
cp agentcore/aws-targets.example.json agentcore/aws-targets.json   # set your account id
(cd agentcore/cdk && npm install)
npx @aws/agentcore deploy --yes
```

`app/coach/volley_agent` and `app/coach/serve_return` are copies of the repository's own modules; `apps/agent/tests/test_agentcore_copy.py` fails if they differ.
