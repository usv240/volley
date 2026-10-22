# Technical design

The governing rule, from which everything else follows: **words are read
on the parent's machine and never written anywhere.** Every component is
placed on one side of that line, and a test walks the line.

```
Bee wristband  ->  Bee cloud (Amazon's transcript, the parent's account)
                        |
                 bee CLI on the parent's machine
                        |
               apps/ingest   reads utterances (ts, speaker, text)
                        |
        packages/serve-return   counts turns; text is dropped here
                        |
                counts only, from here on
                        |
   +--------------------+----------------------+
   |                    |                      |
 volley today       apps/server (Lambda)    apps/coach
 (local view)       DynamoDB, API keys      one thing for tomorrow
                    MCP server, Skill       rules, then Bedrock wording
                        |
                    apps/web (S3 + CloudFront)
                    the site, the household view, the live panels
```

## 1. `packages/serve-return` (Python, MIT)

The open-source deliverable. Dependency-free core so a researcher can
`pip install serve-return` and count turns from any transcript,
with speaker labels or, through `serve_return.blind`, without them.

### Input

```python
@dataclass(frozen=True)
class Utterance:
    ts: str          # ISO 8601 UTC
    speaker: str     # any label; the caller says which is the adult
    text: str        # used only for word and question counts, then gone
    conversation_id: str | None = None
```

### The rule

A conversational turn, following the definition the published studies
used (LENA's Conversational Turn Count): an adult utterance followed by
a child utterance within five seconds, or a child utterance followed by
an adult utterance within five seconds, counts one turn. Consecutive
utterances by the same speaker merge. A gap over five seconds ends the
volley. The window is a constant with its source in the docstring; a
test pins it to five.

Beyond the count, per hour of the day:

| Field | Meaning | Why it is there |
|---|---|---|
| `turns` | turns by the rule above | the validated number |
| `serves_adult`, `serves_child` | who started each volley | the coaching literature is about the adult responding, not only talking |
| `responses_within_5s` | child utterances answered by the adult within five seconds | responsiveness, the mechanism named by the RCT |
| `response_latency_median_s` | adult reply time to a child utterance | shorter is the coachable thing |
| `questions_adult` | adult utterances ending in a question mark or starting with a wh-word | the one behaviour parents can change tonight |
| `longest_volley` | most consecutive turns in one exchange | a number a parent remembers |
| `talk_minutes_adult`, `talk_minutes_child` | speaking time by utterance span | context for the count |
| `words_discarded` | how many words were read and thrown away | the privacy proof, as a number |

Nothing textual survives. `questions_adult` is computed and the sentence
is gone; a test feeds a transcript of names and asserts none of them
appears in the output, serialised.

### Validation harness

`harness/handcount/`: five of the operator's own conversations counted
blind by a person from the Bee app's transcript view on a printed sheet
(turns per conversation, nothing else written down), against the
package's count. The published comparison to cite and to match in form
is the "word of caution" paper on automated versus manual LENA turns
(see EVIDENCE.md). The harness prints agreement and the site shows it
whichever way it comes out.

### Tests

Worked examples from the rule's definition (two speakers, 4-second gaps
count; 6-second gaps do not; same-speaker runs merge; a child's babble
transcribed as "buh" counts as an utterance). The device fixture with
placeholder words. Property tests: reordering utterances within a
second does not change the count by more than one; deleting text never
changes the count.

### The benchmark: recordings we did not make

`harness/playlogue/` runs the counter over Playlogue v1 (Kalanadhabhatta
et al., IMWUT 2024): 33 hours of preschool adult-child play drawn from
CHILDES, speaker-attributed, time-aligned by forced alignment, with
diarisation ground truth. Licence CC BY-NC-SA 3.0 behind the TalkBank
ground rules; used for evidence, never shipped, cited as TalkBank
requires. The harness publishes, per session and in total:

- turns per hour by the rule, using the corpus's human speaker labels;
- agreement of the rule's turn structure with the labelled alternation;
- the negative control: turns counted inside stretches the labels mark
  as single-speaker (the right answer is zero);
- baseline one, adult word count per session beside turn count, with
  the sessions where the same word count carries very different turn
  counts, which is the whole argument for counting turns;
- baseline two, speaker changes counted with no window, and how far it
  overcounts;
- the youngest sessions on their own, so the undercount on younger
  children is a measured number rather than a caveat.

Results are committed as JSON; the site's evidence section reads them;
a test fails if the site's figures and the JSON disagree, and another
fails if a deliberately broken window (fifty seconds) does not change
the numbers, so the harness cannot pass by measuring nothing.

Second corpus, for age coverage: CHILDES media-linked transcripts
through `childespy` (`media_start`, `media_end` from CHAT bullets).

### The device's own negative controls

Run on the operator's Bee on 2026-10-20 (`harness/beeloop/controls.py`),
three minutes each, no person speaking: two adults from a CHILDES family
dinner with the child's lines left out, 21 false turns; silence, 1 (the
room was not silent: the Bee wrote 16 utterances in that window); one
adult voice back to back, 14. A real parent and child of the same length
gave 66. The corpus agrees (`harness/blind/adults_only.py`: false turns
at 43 percent of the real count with the child removed). The counts are
on the site as numbers, which is what this section promised whichever
way they came out.

### The loop back into the parent's Bee

The one thing for tomorrow is not only shown; it is placed where the
parent already lives. `bee todos create --text <the note> --alarm-at
<the named hour tomorrow>` puts it into the parent's own Bee as a
reminder that fires at bath time, or dinner, or whichever hour the
counts named. Alexa+ reads it back through the MCP server. The argv is
pinned by a test; the text is the note and nothing else; it is written
only after the parent said yes to it in `volley setup`, and never twice
for one day.

### The live counter

`volley live` reads `bee stream --json`, keeps a five-second window in
memory, and prints the turn count as it changes, one line per turn,
with the words never printed. It is the terminal shot in the video and
the thing a parent runs once to see that it is real. If the stream
drops, it says so and the day's count comes from `volley today`.

### `volley verify`

Recomputes every published number from committed inputs (the corpus
results, the negative controls, the hand-count harness, the device
fixture) and prints a diff against the figures in the site's source.
The evidence record from `volley evidence` carries a hash of the
previous record, so a judge can see the chain of runs and rerun the
last one.

## 2. `apps/ingest` (Python, from Bellwether)

Bellwether's `BeeCli` with the device's real shapes: rows from
`conversations list` are fetched one by one with `get` and unwrapped;
`spoken_at` is the time; offsets are never instants. New here:

- **Household setup.** `volley setup` asks two things: which label is
  you (the wearer, from the labels the Bee has produced this week), and
  which label is the child, or "everyone else". Stored locally only.
- **`volley today`**: pull since the last cursor, count, print the day
  as the site would show it, delete the utterances from memory, and
  post counts to the API if a key is configured. The words never touch
  the disk: a test runs it with a temporary home and asserts the only
  files written are the cursor and the counts.
- **`volley evidence`**: like Bellwether's, a publishable record that
  live Bee data flowed, with counts, shapes, and zero words.

## 3. `apps/coach` (Python)

"One thing for tomorrow" in two layers, so the wording can be warm and
the facts cannot be wrong.

1. **Rules pick the thing.** From the day's counts, in priority order:
   an hour with the child present and under five turns; a median reply
   latency over five seconds; fewer than one adult question per ten
   turns; a best hour worth naming. Each rule yields a structured fact:
   `{kind, hour, value, target}`.
2. **Bedrock phrases it.** The fact goes to Claude on Bedrock with the
   instruction to write two sentences a tired parent would want to read,
   naming the hour and the number given and no other number. A
   deterministic template is the floor: if Bedrock is unavailable, or
   returns a number that is not in the fact, the template is used and
   the response says so. A test extracts every digit from the note and
   asserts it came from the fact.

Never: comparisons with other families, percentiles of the child, any
sentence with "delay", "risk" or "behind". A test holds a list of
forbidden words against every template and every Bedrock response in
the fixture set.

## 4. `apps/server` (FastAPI on Lambda, from Bellwether)

### What it stores

DynamoDB, one table, household-keyed. Per day, per hour: the count
fields above. Per day: the note and its fact. Per household: a name the
parent chose, the child's first name or a nickname (optional, and the
site says why it is optional), the API key hash, created date. No
utterance table exists; there is no column that could hold text longer
than a nickname, and a test asserts the schema.

### Bring your own data, three ways

Every judge and every parent can use the product without us:

1. **Your Bee, on your machine.** `pip install serve-return "volley-bee @ git+https://github.com/usv240/volley#subdirectory=apps/ingest"`, `volley setup --blind`,
   `volley today`. The only route that reads a transcript, and it reads
   it where you are.
2. **A Bee export, in your browser.** The site has a drop zone for the
   markdown `bee sync` writes. The counting runs in the browser (the
   rule is small; a TypeScript port lives in `apps/web/src/count`, with
   a test that it agrees with the Python package on the fixtures).
   Nothing is uploaded unless the visitor presses "save these counts".
3. **An API key, for developers.** `POST /v1/households` returns a key;
   `POST /v1/days` takes counts; `GET /v1/days`, `/v1/week`, `/v1/note`
   read. Interactive docs at `/v1/docs`. The request schema drops every
   field it does not know, so a transcript posted by mistake is dropped
   at the door, and the live privacy panel on the site demonstrates it.

### The MCP server (the Alexa+ surface)

Spec revision 2025-11-25 over Streamable HTTP, on the same Lambda at
`/mcp`, with origin validation that allows the site's own origin from a
value the stack passes in. Seven tools:

| Tool | Returns | Why |
|---|---|---|
| `what_volley_counts` | the rule, in words; no data | so an assistant can explain without reporting |
| `how_was_our_talking_today` | today's turns, best hour, quietest hour | the question a parent asks |
| `one_thing_for_tomorrow` | the note | the coaching |
| `week_trend` | seven days of turns and the direction | the step-counter view |
| `best_hour_this_week` | one hour and its count | a habit to keep |
| `record_day` | stores counts a client already computed | the write path, counts only |
| `household_settings` | names and options, no counts | for the assistant to address the child by name if the parent chose one |

A test walks every tool with a household whose counts were made from a
transcript of names and asserts no tool ever returns a word of it. A
conformance script drives initialize, initialized, tools/list,
tools/call, and DELETE over real HTTP against the deployed endpoint.

### The Agent Skill

`skills/volley/SKILL.md`, pinned to the server's tools by a test, for
Alexa+ and for coding agents. It tells the agent what the numbers mean,
what it must never say, and that it cannot get a transcript from this
server because there is none.

## 5. `apps/web` (Next.js static export, S3 + CloudFront)

SITE.md has every section. Technically:

- Static export, no server; the household view fetches the API with the
  key from local storage; the demo household is public and labelled.
- The design tokens are the shared warm-paper set (light default, dark
  by `data-theme`, a blocking script so there is no flash): background
  #f7f4ee, surface #fffdf9, ink #1c1a17, accent #1f4fd8, and their dark
  counterparts; Fraunces for display, Inter for reading, self-hosted.
- Components carried over: `InfoButton` (click, not hover; Escape
  closes; `aria-expanded`), `ThemeToggle`, `Nav` (sticky, section
  links), `McpProof` (a real session, timed), `PrivacyProof` (post a
  transcript, watch it refused). New: `DayView` (the step-counter day,
  hours as a bar row, single hue, direct labels), `WorkedExample` (a
  twenty-second exchange as bars with turns marked, the rule made
  visible), `DropZone` (the browser-side counter), `HandCount` (the
  agreement table from the harness).
- Charts: one hue for magnitude, no colour-only meaning, direct labels
  on the bars that matter, a table view behind an i-button for every
  chart.

## 6. AWS (documented for the mini challenge)

| Service | What it does here |
|---|---|
| Amazon Bedrock | phrases the one thing for tomorrow from a structured fact, with a deterministic floor |
| Strands Agents SDK | an agent that consumes Volley's MCP server as an outside client, and a second that holds Bee's MCP server beside ours to answer "why was Tuesday quiet" with the Bee's own summary of that day |
| Amazon DynamoDB | counts, households, keys; nothing textual longer than a nickname |
| AWS Lambda with a function URL | the API and the MCP server |
| Amazon S3 and CloudFront | the site |
| AWS CDK | one stack, one deploy, the site's origin passed to the server |

Not used, and said: Transcribe (Bee already transcribes), Rekognition,
anything that would see a child.

## 7. Tests as claims

Every number on the site is re-derived by a test from committed output:
the agreement from the harness, the counts from the device fixture, the
test total, the friction log count. A guard that matches nothing fails.
Public text is checked for forbidden words, for em dashes, for
"validated on children" and for any sentence claiming the product
predicts an outcome.

## 8. The video pipeline

Earshot's, copied: `beats.py` as the single source, `narrate.py` (Polly),
`record.py` (browser at 3840x2160 with the clapperboard), a terminal
camera for the two Bee shots (real commands and real output rendered in
a terminal frame the same recorder captures, and the script says so),
`assemble.py`, `subtitle.py`. Every narrated sentence appears on the
site; a test checks it.

## 9. Repository layout

```
volley/
  README.md
  LICENSE                     MIT
  docs/                       design, evidence, honesty
  packages/serve-return/      the counter and the role model
  apps/ingest/                the Bee client and the volley command
  apps/coach/                 the one thing for tomorrow
  apps/server/                API, MCP, Skill
  apps/web/                   the site
  apps/agent/                 the Strands agents
  harness/handcount/          agreement with a person
  infra/                      the CDK stack
  skills/volley/SKILL.md
  video/                      the pipeline
  FRICTION_LOG.md
  PRODUCT_FEEDBACK.md
```
