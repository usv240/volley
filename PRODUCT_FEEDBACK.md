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

## Still to record

Amazon Transcribe, Rekognition and any service that would see a child
were deliberately not used, and the AWS document says why.
