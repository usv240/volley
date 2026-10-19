# What this uses on AWS, and what it needs to be allowed to do

One stack, `infra/bin/app.ts`, deployed with `npm run deploy` from the
repository root. Nothing that reads a transcript runs on AWS: counting
happens on the parent's machine, and only counts cross into the stack.

| Service | What it does here | What it never holds |
|---|---|---|
| Amazon DynamoDB | One on-demand table: households (a chosen name, an optional child's first name, the hash of an API key), days of counts by the hour, and the note written from each day | Any string longer than a nickname; there is no item type for a transcript, and a test asserts the schema |
| AWS Lambda with a function URL | The FastAPI service: households behind keys, the day and week views, the note, the pressable privacy check, and the MCP server on `/mcp` | Audio, text, anything from the Bee itself |
| Amazon Bedrock (Anthropic Claude) | Phrases the one thing for tomorrow from a four-line fact chosen by rules, on a ladder of three models with a template as the floor. Every digit in the sentence must come from the fact and no forbidden word may appear, or the template is used | The counts themselves; the model sees the fact, not the day |
| Amazon S3 and Amazon CloudFront | The static site, uploaded by `BucketDeployment` behind a distribution; the distribution's domain is passed to the function as the one allowed browser origin | Nothing but the site |
| AWS CDK | Describes all of the above in TypeScript; the Lambda asset is built without Docker by fetching manylinux wheels for the compiled dependencies | |

## Amazon Bedrock AgentCore Runtime

The Coach is deployed as runtime `volleycoach_coach` (`apps/agentcore`), with its own IAM role and traces, so Alexa+, a scheduled job or another agent can invoke it. It reaches Volley only through the public MCP tools and the same gate.

## Strands Agents SDK

Two agents in `apps/agent`, documented in [AGENT.md](AGENT.md): the
coach, a Strands agent over Volley's MCP server that answers a parent
the way Alexa+ would and cannot say a number no tool returned; and the
Tuesday agent, which holds Bee's own MCP server beside Volley's so a
quiet day can be explained from the parent's own calendar without
either server seeing the other's data. Both run the same Bedrock
ladder as the note, as a Strands `ModelRouter` with `FallbackStrategy`.
Fifteen tests drive them with a scripted model and a real server on a
free port; two real runs on Bedrock are in AGENT.md.

## Permissions

The function's role: read and write on its one table;
`bedrock:InvokeModel` and `InvokeModelWithResponseStream` on Anthropic
foundation models and the account's inference profiles. Deploying the
stack needs the usual CloudFormation, S3, Lambda, DynamoDB, CloudFront
and IAM permissions of the account that owns it.

## Deploy

```
node infra/build-lambda.mjs            # the Python asset, no Docker
cd infra && npx cdk deploy             # API and MCP first; prints ApiUrl and McpUrl
cd ../apps/web
NEXT_PUBLIC_API_URL=<ApiUrl> NEXT_PUBLIC_MCP_URL=<McpUrl> npm run build
cd ../../infra && npx cdk deploy       # now with the site; prints SiteUrl
```

The second deploy passes the site's origin into the function, which is
why the site is built before it and not after.

## What it costs

Pennies. On-demand DynamoDB, a function that runs for tens of
milliseconds per request, a static site, and one Bedrock call per note
with a floor that costs nothing.

## What was deliberately not used

Amazon Transcribe: the Bee already transcribes, and Volley must never
handle audio. Amazon Rekognition or anything that would see a child.
API Gateway: the endpoint speaks one protocol and needs no stages.

## Amazon Polly

Voices a real CHILDES parent-child conversation, adult and child, at its original timing, for the on-device test in `harness/beeloop`. Nothing it produces is published.
