# Volley

**A step counter for conversations with your child.**

**Judging this?** [docs/FOR_JUDGES.md](docs/FOR_JUDGES.md) maps every Rules.md requirement and judging criterion to the file, command or link that proves it.

The Bee on a parent's wrist already hears the day. Volley counts the
back-and-forth exchanges between the parent and the child, keeps the
counts, throws the words away on the parent's own machine, and says one
thing to try tomorrow. The number it counts is the most validated one in
early childhood; the only instrument that measures it has never been
sold to a parent.

Status: built on 2026-09-29 against the plan in `docs/`, which was
written first so the build is judged against it. The API and MCP server
are live at https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws (interactive docs at `/v1/docs`) and the site at https://da78ygi6ol1oi.cloudfront.net.
The rule has run on 26.59 hours of public parent-child recordings
(the CHILDES Gleason corpus, 2026-09-30): 20,344 turns from the
human speaker labels, zero in any stretch where one person spoke alone.
What is not measured says so on the site in the same type size as
the numbers.

**No speaker labels, no problem, measured.** The Bee labels every speaker
"Unknown" (1,004 of 1,004 utterances on this account). `volley setup
--blind` reads who is the child and who the adult from the words and
the pauses instead, with `serve_return.blind`, trained on CHILDES. On
families it never saw: the day's turn count within 9.6 percent of the
true count in the median session (49 of 54 sessions within 20
percent, +1.6 percent in total), turns per hour correlated with the
truth at 0.874, against a naive count that misses 87.3 percent. The
raw blind count runs low by a steady 11 to 15 percent because misread
roles merge exchanges; a scale learned only from other families corrects
it. Every
session is in `harness/blind/results.json`; `python harness/blind/run.py`
reproduces it.

**On the Bee itself, no person in the room.** A real CHILDES mother-child conversation, voiced by Amazon Polly with an adult and a child voice at its original timing, played to the band for 190 seconds: the Bee wrote 124 utterances for 125 played and kept 75 of 75 turns, so its segmentation loses none. Volley's blind count with a model and scale that never saw this family: 66 (-12.0 percent; 58 before the scale), 76.6 percent of lines given the right speaker. `harness/beeloop` reproduces it. 123 tests.

| Document | What it answers |
|---|---|
| [docs/FOR_JUDGES.md](docs/FOR_JUDGES.md) | **Start here.** Every Rules.md requirement and judging criterion, with the file or link that proves it |
| [docs/DESIGN.md](docs/DESIGN.md) | The technical design: packages, the turn rule, privacy by construction, API, MCP, AWS, tests as claims |
| [docs/SITE.md](docs/SITE.md) | The landing page and product surface: every section, its copy outline, the i-buttons, light and dark, mobile and desktop, the first-time-visitor path |
| [docs/EVIDENCE.md](docs/EVIDENCE.md) | The science, what each number is and is not, and how the site is allowed to say it |
| [docs/PRIOR_ART.md](docs/PRIOR_ART.md) | Who has done what, named before a judge has to find it |
| [docs/HONESTY.md](docs/HONESTY.md) | Privacy, consent, what it never does, the limits, and the kill criteria |
| [docs/planning/](docs/planning/) | The pre-build plan, gates and audits, kept as a record; superseded by FOR_JUDGES.md |
| [docs/AGENT.md](docs/AGENT.md) | The two Strands agents over the MCP server, their gate, and two real runs |

Track: Bee (primary), Alexa+ (an Agent Skill backed by an MCP server).
Mini challenges: AWS Builder, Open Source (`serve-return`, MIT, installable from this repository).

Sibling projects in this hackathon, each with its own repository and
docs: Earshot (Fire TV, hearing in noise), Bellwether (Bee, speech as a
vital sign), EveryWord (Fire TV), Nightlight (Ring). Volley reuses
Bellwether's Bee client, server, stack and video pipeline; it shares no
claim with it.

## Run it

```
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e "packages/serve-return[dev]" -e "apps/ingest[dev]" -e "apps/server[dev]" -e "apps/agent[dev]"
python -m pytest packages apps harness -q          # 123 tests, the same two lines CI runs
cd apps/web && npm ci && npm test && npm run dev   # the site, on localhost:3000
```

No AWS account and no Bee are needed for any of that.

### If you own a Bee

No clone. Three lines, checked in a fresh environment:

```
pip install "serve-return @ git+https://github.com/usv240/volley#subdirectory=packages/serve-return" "volley-bee @ git+https://github.com/usv240/volley#subdirectory=apps/ingest"
volley setup --blind         # the Bee labels every speaker Unknown; Volley reads the roles itself
volley today                 # count since the last run, throw the words away, remind tomorrow
```

`volley connect` gives your counts a page of your own; `volley today
--conversation <id>` counts one session and reads nothing else.

To let your own assistant answer questions about the counts, add the
Agent Skill the same way Bee's own skill is added:
`npx skills add usv240/volley`.

## Built with

Every tool this project uses, and the file that uses it.

| Tool | What it does here | Where |
|---|---|---|
| Bee CLI | conversations, changes, the live stream, and tomorrow's reminder written back into the Bee | [`apps/ingest/volley_ingest/bee.py`](apps/ingest/volley_ingest/bee.py) |
| Bee's own MCP server | the Tuesday agent holds it beside Volley's, behind a five-tool allow-list | [`apps/agent/volley_agent/tuesday.py`](apps/agent/volley_agent/tuesday.py) |
| MCP server, spec 2025-11-25, Streamable HTTP | the Alexa+ surface: seven tools, signed sessions, conformance-probed live | [`apps/server/volley_server/mcp.py`](apps/server/volley_server/mcp.py) |
| Agent Skill | tells an agent how to use the seven tools; a test pins it to the server | [`skills/volley/SKILL.md`](skills/volley/SKILL.md) |
| Amazon Bedrock (Claude) | phrases tomorrow's one thing behind a gate that refuses any number the rules did not choose | [`apps/server/volley_server/bedrock.py`](apps/server/volley_server/bedrock.py) |
| Strands Agents SDK | the Coach and the Tuesday agent, both behind the same number gate | [`apps/agent/volley_agent`](apps/agent/volley_agent) |
| Amazon Bedrock AgentCore Runtime | hosts the Coach as an invocable endpoint | [`apps/agentcore`](apps/agentcore) |
| Amazon Polly | voices a real CHILDES conversation, adult and child, for the on-device test | [`harness/beeloop/make.py`](harness/beeloop/make.py) |
| Amazon DynamoDB, AWS Lambda, Amazon S3, Amazon CloudFront, AWS CDK | households and counts, the service, the site, one deploy | [`infra/bin/app.ts`](infra/bin/app.ts) |
| CHILDES (TalkBank) | the corpus the count and the role model are measured on | [`harness/childes/run.py`](harness/childes/run.py) |

