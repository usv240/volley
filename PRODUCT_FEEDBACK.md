# Product feedback

On every tool, API and SDK used, as the rules ask: what it was used
for, what worked, what needs work, how onboarding felt, and whether we
would build with it again.

## Bee CLI (`@beeai/cli`) and the Bee developer surface

**Used for:** the whole sensor. `conversations list` and `get`, `now`,
`changed` with a cursor, `stream --json` for the live counter, `sync`
markdown for the browser drop zone, and `todos create --alarm-at` to
put tomorrow's one thing back into the parent's own Bee.

**What worked well:** the times. Each utterance carries `spoken_at`
and `start` and `end` offsets, which is exactly what the published
five-second rule needs and what no consumer transcript has offered
before. `todos create` with an alarm closes the loop into the
wearer's own device in one command; that is the feature that turns a
dashboard into a product.

**What needs work:** speaker labels are "Unknown" until a voice is
trained in the app, and nothing on the developer side says so
(friction log entry 1). The readme's response shapes differ from the
device's in three ways (entry 2). `sync` exports carry no times
(entry 3).

**Onboarding:** Developer Mode by tapping the version five times, then
`bee login` with an approval link, took five minutes and worked first
time. Finding out why every speaker was "Unknown" took an afternoon and
ended on a forum.

**Would we build with it again:** yes. It is the only consumer device
that can do this at all.

## Model Context Protocol, revision 2025-11-25, over Streamable HTTP

**Used for:** the Alexa+ surface: seven tools, one of which returns no
data by design.

**What worked well:** the transport is small enough to implement by
hand and test over real HTTP, and having done it three times in sibling
projects the fourth took an hour.

**What needs work:** the DNS-rebinding guidance says to validate
Origin and does not say to allow your own site; every sibling hit a 403
from its own front page. Here the stack passes the site's origin to the
server so it is never typed.

**Would we build with it again:** yes.

## Amazon Bedrock (Anthropic Claude)

**Used for:** phrasing the one thing for tomorrow from a fact the rules
chose. A model ladder of three Claude models, each tried in turn, with
a template as the floor and a gate that rejects any sentence carrying a
number not in the fact or a forbidden word.

**What worked well:** a strong model phrases warmly from four lines of
facts, and the gate makes the warmth safe to ship.

**What needs work:** the model will use dashes and add reassurance
however the prompt asks it not to; both are enforced after the fact by
code, not by the prompt.

**Would we build with it again:** yes, behind a gate, always.

## Amazon DynamoDB, AWS Lambda with a function URL, Amazon S3 and CloudFront, AWS CDK

**Used for:** one stack: the households table with no item type that
can hold a transcript, the API and MCP server on Lambda behind a
function URL, the static site on S3 behind CloudFront, described in
TypeScript and deployed with one command.

**What worked well:** a function URL is the right size for an endpoint
that speaks one protocol; `BucketDeployment` makes a static export one
line; the site's origin flows from the distribution into the function's
environment so the allowlist is never stale.

**What needs work:** an ESM Lambda bundling a CommonJS dependency fails
at runtime with a 502 rather than at synth time; the Lambda asset is
built without Docker by fetching manylinux wheels, which works and is
undocumented.

**Would we build with it again:** yes.

## Next.js, Tailwind, Playwright, FastAPI, Mangum, Vitest, pytest (third-party)

**Used for:** the site, the service, the tests, and the screenshots
that check the site in both themes at two widths before anything ships.

**What worked well:** a static export with no server is the simplest
thing that can be deployed; the browser port of the counter is thirty
lines and pinned to the Python package by a shared set of examples.

**What needs work:** nothing attributable to these tools.

**Would we build with them again:** yes.

## Strands Agents SDK (1.57)

- What worked: `MCPClient(url=...)` for Streamable HTTP and a
  `transport_callable` for stdio, so Volley's server and Bee's sat side
  by side in one agent with no glue; `tool_filters={"allowed": [...]}`
  made the Bee allow-list one line; `ModelRouter` with
  `FallbackStrategy` replaced a hand-written Bedrock ladder; a custom
  `Model` subclass that yields stream events was enough to drive the
  whole agent loop in tests with no AWS account.
- What got in the way: nothing in the SDK lets a tool's credential
  arguments be filled in outside the model. Volley wraps each MCP tool
  in a `PythonAgentTool` with the credential properties removed from
  the schema and added back on the way out; it is forty lines, but an
  `inject={"api_key": ...}` on `MCPClient` would make the pattern
  obvious rather than something each project rediscovers.
- What was missing: a gate on the final answer. Strands has hooks and
  interventions, but "every number in the answer must have come from a
  tool result" had to be written against `agent.messages` after the
  call. A `validate_output` hook with the tool results in hand would
  make that a declared property of the agent.
- The `mcp` 2.x rename (`FastMCP` to `MCPServer`) broke the stand-in
  server used in tests on the day it was written; the SDK's own
  examples still show the 1.x import.

## Still to record

Amazon Transcribe, Rekognition and any service that would see a child
were deliberately not used, and the AWS document says why.

## Amazon Bedrock AgentCore Runtime

**Used for:** hosting our Strands agent as an invocable endpoint with its own IAM role and traces (`apps/agentcore`), so Alexa+, a scheduled job or another agent can call it. It reaches the product only through our MCP server.

**What worked well:** `npx @aws/agentcore deploy` turned an existing Strands agent into a hosted endpoint in about four minutes, first time, and `invoke` returned the agent's own JSON.

**What needs work:** the scaffold's default model profile was not one this account could invoke, so the model is pinned by hand.

**Onboarding:** no global install; deploy and invoke both worked on Windows on the first run.

**Would we build with it again:** yes. It is the shortest path from a local agent to something Alexa+ or a schedule can call.

## Agent Skills

**Used for:** `skills/volley/SKILL.md`, which tells an agent what the product is, which MCP tools to call in what order, and what it must never say. A test checks it names every tool on the server.

**What worked well:** plain markdown an agent reads directly, so the product's rules travel with its tools.

**What needs work:** we found no public way to load a skill into Alexa+ ourselves and watch it run, so ours is checked against the MCP server by a test rather than end to end in Alexa+.

**Would we build with it again:** yes.

## Amazon Polly

**Used for:** voicing a real CHILDES parent-child conversation, adult and child voices, at its original timing, so the count could be tested on the Bee with no person in the room (`harness/beeloop`).

**What worked well:** neural adult and child voices from one call each, as raw PCM a WAV header turns into sound with no audio library.

**Would we build with it again:** yes.

## Bee's own MCP server (`bee mcp`)

**Used for:** the Tuesday agent holds it beside Volley's server on the parent's machine, behind a five-tool allow-list, so a quiet day can be read against the parent's calendar without either server seeing the other's data.

**What worked well:** it authenticates with the existing Bee login, so there is no second token to manage.

**Would we build with it again:** yes.
