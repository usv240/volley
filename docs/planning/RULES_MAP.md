# Rules map

Every requirement in Rules.md and every judging criterion, with where
it is met and what "exceeded" means for it. Written before the build,
so the build is checked against it.

## Hard requirements

| Rule | Where it is met | The test |
|---|---|---|
| Public GitHub repository with all source, assets, run instructions, and an open-source licence visible at the top | `usv240/volley`, MIT, topics set, README run section | A clean clone runs `pip install -e` and `pytest` green |
| Bee: the repo must import and actually call Bee's CLI, MCP or Skill at runtime | `apps/ingest` runs `bee conversations list`, `get`, `now`, `changed`; the Strands agent holds Bee's own MCP server | Tests pin the exact argv; `volley evidence` records real calls |
| Bee: the demo must show the project using live Bee data to deliver value to a user | The video's two live shots: `volley today` on the operator's own day, then the day view and the note | Gate 3 |
| Alexa+: show the Agent Skill (prioritised) or MCP server (2025-11-25, Streamable HTTP) in action | `skills/volley/SKILL.md`; the MCP server at `/mcp`; the live panel on the site; the video's session | Conformance over real HTTP; the skill pinned to the server's tools |
| Demo video under three minutes, public, English, no third-party marks or music | `video/`, 2:55 target, 4K, captions, Polly narration only | `beats.py` refuses a plan over the ceiling; every narrated sentence appears on the site |
| Product feedback on every tool, API or SDK used | `PRODUCT_FEEDBACK.md`: Bee CLI and speaker labels, MCP, Strands, Bedrock, DynamoDB, Lambda, S3 and CloudFront, CDK, Next.js, FastAPI, Polly, Playwright | A test that every service in `docs/AWS.md` is in the feedback |
| Tracks and mini challenges stated; Open Source fields (contribution URL, repo, username, description); AWS Builder fields | `docs/SUBMISSION.md` | Read |
| Pre-existing project explanation | None pre-existed; the first commit is in the window; reuse from siblings is stated with the commit that did it | Read |
| Friction log (up to 10 percent bonus) | From day one, entry 1 being the speaker labels | Counted by a test against the stated total |

## Mini challenges

| Challenge | What qualifies |
|---|---|
| AWS Builder | Bedrock (the note, with a deterministic floor), Strands (two agents), DynamoDB, Lambda function URL, S3 and CloudFront, CDK, documented in `docs/AWS.md` with what each does and the minimum permissions |
| Open Source | `serve-return` on PyPI under MIT: the turn counter with its published rule, its harness, and a fixture from the device with placeholder words |

## Judging criteria, and what 10 means here

### Tech implementation

Judges ask: how well is it built, how effectively does it use the
required tech.

- The Bee integration is real, pinned to the device's actual shapes, and
  exercised on live data before the video exists.
- The count is validated against a person, in the same form as the
  literature, and the result is published either way.
- The MCP server conforms over real HTTP and is shown from the page; the
  Skill is pinned to the server by a test.
- Every number on the site is a test. The privacy promise is a test.
- What would cost a point: an unmeasured count. Gate 2 exists for this.

### Design

Judges ask: complete, coherent experience; the interaction model right
for the platform.

- The product is one number and one sentence, and the whole site is
  built so a stranger reads it in one pass. The first-time test is run
  with three people and recorded.
- Two audiences, never mixed: the page for the parent, the i-buttons for
  everyone else.
- Light and dark chosen, mobile first, accessibility 100, every chart
  with a table behind it.
- The Alexa+ surface is the question a parent actually asks, "how was
  our talking today", answered without a word of the transcript.
- What would cost a point: the wearer's first day being a terminal. The
  local command prints the day view; the site's drop zone counts in the
  browser; the API key makes it a service. Three doors, each for someone.

### Potential impact

Judges ask: a credible, specific case; an audience beyond the hackathon.

- The number is the most validated one in the field, the instrument is
  unavailable to parents, and the Bee is the first consumer device that
  can produce it. The audience is every household with a young child and
  a wearable, and the families the science says gain most are those
  programmes could not reach.
- The coaching is the mechanism a randomised trial used, delivered daily
  by the day's own counts rather than by a visitor.
- The honesty holds the line: associations stated as associations,
  LENA's figures as LENA's, a child never scored.
- The case beyond the hackathon is made on the site, in its own
  section, in the order a sceptic asks: cities have paid for this
  count (Providence Talks, LENA Start); it is coachable in randomised
  trials at this age (Romeo 2021, Suskind 2016, Leung 2020); the number
  reaches beyond language (Gomez 2021, Romeo 2018); it does not rest on
  the word gap (Sperry 2019, Golinkoff 2019); the phone is the mechanism
  the quietest hour points at (Reed 2017, Radesky 2014); the research
  instrument's own turn count is imperfect (Cristia 2020, Ferjan
  Ramirez 2021); the scale and who is asked to act (Norbury 2016, the
  AAP's 2014 and 2021 policies); and what changes at fifty dollars.
  Every study is resolved in `docs/citations.json` with what it showed
  and did not, and a test refuses a citation that is not there.
- What would cost a point: one family. The site says so; the pilot
  paragraph names the study to run next: the Bee against a LENA
  recorder on the same afternoon.

### Quality of the idea

Judges ask: creative use of the tools; genuine understanding of the
ecosystem and the users' needs.

- A validated developmental measure, put in a parent's hand for the
  first time, on the one consumer device that can, in the track's first
  priority category, with the words destroyed where they are read.
- The ecosystem understanding is in the friction log from day one: what
  the Bee's speaker labels do and do not do, what its CLI returns and
  does not, and the feature request that would make this product
  trivial for Amazon to ship.
- What would cost a point: sounding like a reminder to talk to your kid.
  The worked example that shows the rule counting, and the harness that
  measures it, are the difference.

## The twelve winner patterns

Audited separately in [WINNER_PATTERNS.md](WINNER_PATTERNS.md): the
public corpus as the second number, the two baselines, the negative
controls as the headline, the reminder written back into the parent's
Bee, the live counter, the practitioner's sentence, `pip install
volley`, measured limits, and `volley verify`.

## The judge's three minutes

0:00 the sentence and the number; 0:20 the three figures; 0:45 the rule
counting on a real exchange; 1:10 the operator's own day and the note;
1:40 the transcript refused, live; 2:00 Alexa+ asked out loud; 2:25 what
it will never say; 2:45 the line. Every second of it is on the site in
the same words.
