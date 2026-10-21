# Volley, for judges

Every requirement in the hackathon rules and every judging criterion,
with the file, command or link that proves it. Written to be checked,
not believed. Numbers are generated from committed result files, and
151 tests guard the claims.

**In one line:** a step counter for conversations with your child. The
Bee on a parent's wrist hears the day; Volley counts the back-and-forth
between parent and child, keeps the counts, deletes the words on the
parent's own computer, and puts one thing to try tomorrow back into the
parent's Bee.

**Live:** site https://da78ygi6ol1oi.cloudfront.net · API and docs
https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/v1/docs
· MCP https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws/mcp

## Submission requirements

| Requirement | Met by | Check it |
|---|---|---|
| Text description of what it does and how | Devpost text; [SUBMISSION.md](SUBMISSION.md) | Read |
| Public repository with all source, assets and run instructions | This repository; [README.md](../README.md), [DESIGN.md](DESIGN.md) | Clone, then the lines under "Run it" in the README |
| Open-source licence visible at the top | MIT, [LICENSE](../LICENSE) | The About panel |
| **Bee: the repo calls Bee's CLI, MCP or Skill in code** | `apps/ingest/volley_ingest/bee.py` runs `bee conversations list`, `get`, `now`, `changed`, `stream --json`, `todos create`; every argv pinned in `apps/ingest/tests`. `apps/agent/volley_agent/tuesday.py` holds Bee's own MCP server | `pytest apps/ingest` |
| **Bee: live Bee data doing something for a user** | A real CHILDES mother-child conversation, voiced by Amazon Polly at its original timing, played to the band with no person in the room (2026-10-19). From the Bee's own transcript: 124 utterances for 125 played; given the true speakers, 75 of 75 turns kept; Volley with no labels counted 66 (-12.0 percent). Then the product on that session: `volley today --conversation 11418600` counted the same 66, kept 0 of 517 words, and put tomorrow's sentence into the Bee as a reminder | `harness/beeloop/results.json`; `python harness/beeloop/score.py`; [BEE_DAY.md](BEE_DAY.md) |
| **Alexa+: Agent Skill or MCP server, spec 2025-11-25, Streamable HTTP, in action** | Self-hosted MCP server, seven tools; [skills/volley/SKILL.md](../skills/volley/SKILL.md) pinned to the tools by a test; a live session from the site's Alexa+ section | The site's Alexa+ section; `pytest apps/server` |
| Demo video under three minutes | To be recorded last | |
| Product feedback on every tool used | [PRODUCT_FEEDBACK.md](../PRODUCT_FEEDBACK.md) and the Devpost feedback answers | Read |
| Tracks and mini challenges | Bee (primary), Alexa+; AWS Builder; Open Source | [SUBMISSION.md](SUBMISSION.md) |
| Open Source fields | Contribution: `packages/serve-return` (MIT), on PyPI: `pip install serve-return` (https://pypi.org/project/serve-return/); repository, username usv240, description in SUBMISSION.md | Read |
| AWS Builder: documented integrations | [AWS.md](AWS.md): Bedrock, Bedrock AgentCore Runtime, Strands Agents, DynamoDB, Lambda, S3, CloudFront, CDK, Polly | Read |
| Pre-existing project | None; started in the window; reuse from sibling entries stated | [SUBMISSION.md](SUBMISSION.md) |
| Feature requests, rated | [FEATURE_REQUESTS.md](FEATURE_REQUESTS.md), four, each critical, important or nice-to-have | Read |
| Friction log (up to 10 percent bonus) | [FRICTION_LOG.md](../FRICTION_LOG.md), five entries in the required form | Read |

## Judging criteria

### Technical implementation

- **The hard problem, solved and measured.** The Bee labels every speaker
  "Unknown" (1,004 of 1,004 utterances). `serve_return.blind` reads child
  and adult from the words and the pauses: an averaged perceptron trained
  on CHILDES, scored only on families it never saw (six folds by child),
  with its steady undercount corrected by a scale learned from other
  families only. Result: +1.6 percent in total, median session error 9.6
  percent, 49 of 54 sessions within 20 percent, turns per hour correlated
  with the truth at 0.874. The fairest baseline, every line a new
  speaker scaled the same way, matches the total (+0.3 percent) and
  loses per session (13.4 percent, 40 of 54) and per hour (0.766);
  treating every pause as a change of speaker misses 87.3 percent, but
  forced alignment leaves most pauses at zero here, so pauses are tested
  properly only on the Bee session. `python harness/blind/run.py` reproduces it.
- **On the device itself:** 66 of 75 turns, with a model and scale that
  never saw that family. Reading that session found and fixed a real bug:
  the Bee's `start_time` runs 33 seconds after the audio, which had made
  every utterance look half a minute long. A regression test fails
  without the fix.
- **The published rule, open source.** The five-second turn rule from
  the research literature, per hour, in a dependency-free MIT package
  whose output types cannot hold a word; a test serialises a transcript
  full of names and finds none.
- **Agents that cannot invent numbers.** Two Strands agents over the MCP
  server; a gate rejects any sentence with a number no tool returned
  ([AGENT.md](AGENT.md)). The note is phrased on Bedrock from rules-chosen
  facts behind the same gate, with a template as the floor.
- **The Coach on Amazon Bedrock AgentCore Runtime**, as an endpoint anything can invoke, verified live ([apps/agentcore](../apps/agentcore/README.md)).
- **151 tests.** `pytest packages apps harness`.

### Design

- The whole loop is on devices the parent already has: the band counts,
  the laptop deletes the words, the parent's own Bee gets tomorrow's
  reminder at the hour it names, and Alexa+ can read it back.
- A step-counter day: turns by hour, the best hour, the quietest hour
  with the child around, the week. Light and dark, phone and desktop.
- A parent's own page (`volley connect`), read from the API with a key
  carried in the link's fragment, which no server receives.
- Every number on the site carries its measured error beside it.

### Potential impact

- **The number that matters.** Turns at 18 to 24 months explained 14 to
  27 percent of the variance in IQ and vocabulary a decade later, after
  adjusting for income; word counts did not survive the adjustment
  (Gilkerson, Pediatrics 2018, PMID 30201624). Coachable in randomised
  trials (Ferjan Ramirez, PNAS 2020, PMID 32015127), with the gain held
  to 30 months (Huber, Developmental Science 2023, PMID 36999222).
- **Proven demand, missing access.** Providence won a Bloomberg Mayors
  Challenge grand prize to put the research recorder in family homes; the
  recorder has never been sold to a parent. The Bee costs about fifty
  dollars and is already worn.
- **Who carries it past the hackathon.** Home-visiting and city
  programmes already pay for this count, and its gains fade when the
  visits end. `volley share` gives the person coaching a family a
  read-only link to the counts between visits (`/coach`): it cannot
  write, is bound to one household, and the family revokes it. Live and
  tested (`apps/server/tests/test_server.py`, the DynamoDB layout in
  `test_dynamo_store.py`).
- **What it costs to run.** About 4.4 cents a family a month at AWS
  list prices, from usage measured on the live stack
  ([AWS.md](AWS.md), `scripts/cost.py`, `docs/cost.json`).
- **Scale of the need.** About one child in ten starts school with a
  language disorder (Norbury, 2016, PMID 27184709); paediatricians are
  asked to promote talk at every well visit with no instrument a parent
  can bring (Pediatrics 2014, PMID 24962987).
- Every study is resolved in [citations.json](citations.json) with what
  it showed and did not; a test refuses any citation not in it.
- **Limits, said plainly:** no family has used it; no real people are in
  this entry by design; the count is an estimate with a published error;
  it is not a screen, a diagnosis or a comparison of any child with
  another.

### Quality of the idea

- The research field's most validated early-language number, which only
  a lab instrument could count, counted by a fifty-dollar wearable.
- Bee's priority use case for this track is education; this is learning
  at its earliest, coached on the wrist, which is the kind of Bee project
  the organisers' brief asks for ("on wrist coaching for learning").
- The device's largest gap, no speaker labels, is turned into a measured,
  open contribution rather than a wait.
