# Volley: submission

## What it does

**Counts the back-and-forth between you and your child from the Bee on
your wrist, keeps the counts and throws the words away, and puts one
thing to try tomorrow into your Bee as a reminder.**

Your child's brain is built in the back-and-forth. The number that
measures it, adult-child conversational turns, explained 14 to 27
percent of the variance in IQ and vocabulary a decade later in a
longitudinal study, after adjusting for family income; word counts did
not survive that adjustment. It is coachable: parents shown their own
recordings raised turns and their children's language in a randomised
trial, and the gain held to 30 months. The only instrument that
measures it, LENA, is sold to programmes, clinics and researchers, and
never to a parent.

The Bee on a parent's wrist already hears the day. Volley reads its
transcript on the parent's own computer, counts turns by the published
five-second rule, deletes the words, and shows the day like a step
counter: turns by the hour, the best hour, the quietest hour with the
child present, and one thing to try tomorrow, which goes into the
parent's own Bee as a reminder at the hour it names.

## How it works

1. **Wear.** The parent wears the Bee; the child wears nothing.
2. **Count.** `volley today` reads the day through Bee's own command
   line tool, counts with the open-source `serve-return` package, and
   drops the words. The only files written are a cursor and the counts;
   a test runs the command against a transcript of names and reads every
   byte it wrote.
3. **Show.** The day, an hour at a time; the week; one thing for
   tomorrow, written by rules and phrased on Bedrock with a gate that
   overrules any sentence carrying a number not in the fact.
4. **Close the loop.** With consent, the sentence becomes a reminder in
   the parent's Bee (`bee todos create --alarm-at`), and Alexa+ can read
   it back through the MCP server.
5. **See it.** `volley connect` makes a household on the service and
   prints a link to `/mine`, the parent's own page: the day, the week
   and the note, read from the API with the household's key from the
   browser. The key travels in the link's fragment, which no server
   receives, and lives in that browser only.

## The Bee track requirement, answered directly

The rules: "your video and code need to show your project actually
using live Bee data to do something for a user."

**In code.** `apps/ingest` is a client of the Bee CLI with the device's
real response shapes pinned in tests (the list carries no utterances;
`get` wraps its record; `spoken_at` is the time; `start` and `end` are
offsets that give the rule its end-to-start measure). It runs
`conversations list` and `get`, `now`, `changed` with a cursor, `stream
--json` for the live counter, and `todos create` for the reminder. The
argv of every call is pinned.

**On live data.** The device is in hand and signed in; the same
household's day is what Bellwether, the sibling entry, already proved
live on 2026-09-29. What Volley needs from the device is speaker
labels, which the Bee produces only after the wearer's voice is trained
in the app; on 2026-09-29 every utterance was "Unknown" (friction log
entry 1), and on 2026-09-30 a 270-utterance conversation was checked
again and every label was still "Unknown". Gate 1 of the plan is one
conversation with labels; the video is recorded from the operator's own
day the moment it passes, and this document will say the date. The
Tuesday agent has already run against the operator's real Bee through
its MCP server (AGENT.md); that is live Bee data, but it is the day's
summary and not the count this entry is about.

## Tracks and mini challenges

- **Primary track: Bee.** Education, the track's first priority: a
  parent-facing count of the interaction that builds language.
- **Alexa+:** an Agent Skill at [skills/volley/SKILL.md](../skills/volley/SKILL.md),
  pinned to the server's tools by a test, backed by a self-hosted MCP
  server implementing revision 2025-11-25 over Streamable HTTP with
  seven tools. Held live from the site.
- **Mini challenge: AWS Builder.** Bedrock, DynamoDB, Lambda, S3,
  CloudFront, CDK, and two Strands agents over the MCP server, one of
  which holds Bee's MCP server beside Volley's; see [AWS.md](AWS.md)
  and [AGENT.md](AGENT.md).
- **Mini challenge: Open Source.** `serve-return`, a dependency-free
  Python package under MIT.

## Open Source mini challenge

- **Repository:** https://github.com/usv240/volley
- **GitHub username:** usv240
- **The contribution:** `packages/serve-return`, the conversational
  turn counter with the published five-second rule, per-hour counts,
  and nothing that can hold a word.
- **Why it matters:** the research instrument is unavailable to parents
  and to most researchers; every study of this number used it. A free,
  tested implementation of the published definition that works on any
  speaker-labelled transcript is what a graduate student with a
  smartphone corpus has wanted.

## Pre-existing project

None of this existed before the submission window. The Bee client, the
service skeleton, the CDK stack and the site's design system were
carried across from sibling entries of ours in the same window, which
the commits say; every claim, every rule and every word on the site is
Volley's.

## Beyond this hackathon

Cities have paid for this count: Providence won a Bloomberg
Philanthropies grand prize to put the research recorder in families'
homes with coaching, and community classes on the same instrument
raised turns in an evaluation. It is coachable in randomised trials at
the age Volley serves, and the gains from home visits fade when the
visits end, which is the case for a daily count. The number reaches
beyond language to how children handle feelings, and to the wiring of
the brain's language pathway. About one child in ten arrives at school
with a language disorder, and paediatricians are asked to promote talk
at every well visit with no instrument a parent can bring. The Bee
costs about fifty dollars and is already worn. Every sentence of that
has its study on the site's Impact section and in
[EVIDENCE.md](EVIDENCE.md); every study is resolved in
[citations.json](citations.json) with what it showed and what it did
not, and a test refuses any citation in public text that is not there.

## Evidence

[EVIDENCE.md](EVIDENCE.md): every number, its study, what it showed and
did not, and the words the site may use. [PRIOR_ART.md](PRIOR_ART.md):
who has done what. [WINNER_PATTERNS.md](WINNER_PATTERNS.md): the twelve
patterns and where this stands. The corpus benchmark ran on 2026-09-30
on the CHILDES Gleason corpus: 54 sessions, 26.59
hours, 20,344 turns from the human speaker labels, zero inside
the 34 single-speaker stretches, both
baselines beside it, and what it does not show said in the same
paragraph. The device negative controls and the hand count are
scheduled in [PLAN.md](PLAN.md) and published whichever way they come
out; until then the site says "not yet measured" for them in the same
type size as the numbers.

## Live

- Site: https://da78ygi6ol1oi.cloudfront.net
- API: https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws with interactive docs at https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/v1/docs
- MCP server: https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/mcp, spec 2025-11-25 over Streamable HTTP, seven tools

## Honest limits

- Speaker labels are the device's. The count is as good as they are,
  and the harness measures the disagreement.
- Talking age, about three to six, until the undercount on younger
  children is measured on the corpus.
- One family. The pilot to run next: the Bee against a LENA recorder on
  the same afternoon.
- Not a diagnosis, not a test, not a comparison with anyone. A count.

## Run it

```
python -m venv .venv
.venv/Scripts/pip install -e "packages/serve-return[dev]" -e "apps/ingest[dev]" -e "apps/server[dev]" -e "apps/agent[dev]"
.venv/Scripts/python -m pytest packages apps
cd apps/web && npm install && npm test && npm run dev
```

No AWS account is needed for any of that.
