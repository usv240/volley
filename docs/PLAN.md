# Plan

Written 2026-09-29. Deadline 2026-10-23, 3:00pm EDT. Everything below is
ordered by what can stop the project, so the cheapest reason to stop is
found first and the expensive work is never wasted.

## The one sentence a judge should leave with

A parent's wristband can count the exchange that builds a child's brain,
every day, at home, without keeping a word, and nobody has let a parent
have that number before.

## Gates, in order

A gate is a question with a yes or no answer that decides whether the
next phase happens. Each has a test, a date, and what happens on no.

### Gate 1: the device labels who is speaking (by 2026-10-01)

Everything depends on telling the wearer from the child. On 2026-09-29
every utterance the Bee returned was labelled "Unknown".

- Test: train the wearer's voice in the Bee app; hold one ten-minute
  conversation with another person; read the labels through
  `bee conversations get`. Pass: at least two distinct labels, with the
  wearer's utterances mostly one of them.
- On no: retrain once, retest once. If still no, the project stops and
  `IDEAS.md` records why. Nothing else is built.

### Gate 2: the rule agrees with a person (by 2026-10-09)

The five-second turn rule on Bee text has to agree with a human count
on our own conversations, or the number is not the number the studies
measured.

- Test: five conversations, hand-counted blind by the operator from the
  transcript view in the Bee app, against the counter's output.
  Pass: agreement within the range the literature reports for automated
  against manual counts (see EVIDENCE.md, "How good is the automated
  count").
- On no: the site says the measured disagreement in its own evidence
  section, and the counter's number is presented as an estimate with
  that error bar. The project continues; the claim shrinks to fit.

### Gate 2b: the count holds on recordings we did not make (by 2026-10-09; passed 2026-09-30 on Gleason, see EVIDENCE.md)

The second number, from outside our keyboard.

- Test: run the counter over Playlogue (33 hours of public adult-child
  play from CHILDES, speaker-attributed, time-aligned, CC BY-NC-SA 3.0
  behind the TalkBank ground rules) using its human speaker labels, and
  publish turns per hour, the agreement of the rule with the labelled
  turn structure, zero counts in single-speaker stretches, and the two
  baselines (word count; speaker changes with no window) beside it.
- On no: the number is published as it came out, and the site says what
  it means. There is no version of this gate that hides a result.

Update 2026-09-30: TalkBank put every corpus download behind a free
login, Playlogue is gated on Hugging Face, and childes-db moved to
Redivis behind a token, so no corpus can be fetched by a script. A
second harness, `harness/childes/run.py`, reads any media-linked
corpus in CHAT format and runs the same evaluation, so whichever door
the operator's account opens first, the number lands the same day.
The Gleason corpus (24 families, 2;1 to 5;2, mother-child, father-child
and dinner, audio-linked) is the first to run: it sits inside Volley's
talking-age range.

### Gate 3: a real day, on camera (by 2026-10-13)

- Test: one afternoon of the operator's own Bee data reduced to counts,
  shown on the site's household view, with the one thing for tomorrow.
  With a child of talking age if one is available; between two adults if
  not, and the video says which.
- On no: there is no video and no submission for this project; the four
  others are unaffected.

## Phases and dates

| When | What | Done means |
|---|---|---|
| 2026-09-30 to 10-01 | Gate 1 | Labels split, or the project stops |
| 2026-10-02 to 10-03 | `packages/serve-return`: the counter, the rule, the harness for hand counts, the tests, PyPI | `pip install serve-return` works; the rule is documented against its source |
| 2026-10-06 to 10-07 | `apps/ingest` from Bellwether's client; `apps/server` from Bellwether's server; DynamoDB, Lambda, CloudFront, CDK deployed | A real day posts counts to the live API and a transcript is refused |
| 2026-10-07 to 10-08 | `apps/coach`: the one thing for tomorrow, rules first, Bedrock for wording with a deterministic floor | Every number in a note is traceable to a count; the note reads like a person wrote it |
| 2026-10-08 to 10-09 | Gate 2: hand counts; Gate 2b: the public corpus, the two baselines, the negative controls | Every number measured and published, whichever way it comes out; `volley verify` reproduces them |
| 2026-10-07 to 10-08 | The loop back: the note becomes a reminder in the parent's Bee (`bee todos create --alarm-at`); `bee stream` live counter | A reminder appears in the Bee app at the hour the note names; the counter ticks during a real exchange |
| 2026-10-06 to 10-10 | `apps/web`: the site in SITE.md, light and dark, mobile and desktop, every i-button | A stranger reads it in one pass; Lighthouse accessibility 100 |
| 2026-10-09 to 10-10 | MCP server, the Agent Skill, the live MCP panel, the live privacy panel | A session held from the page; a transcript refused on camera |
| 2026-10-11 to 10-13 | The video: beats, narration, browser camera, terminal camera, captions | Under 3:00, 4K, every claim in it on the site |
| 2026-10-13 | Gate 3: the real day | The counts and the note from the operator's own Bee |
| 2026-10-14 to 10-16 | Feedback on every tool, friction log, submission text, upload | Submitted with a week to spare |

The dates overlap with Bellwether's live shots on 2026-10-13 on purpose:
one session with the band, two projects served.

## Deliverables, each with its test

1. **`serve-return` on PyPI.** The counter as a dependency-free Python
   package under MIT. Tests: the rule against worked examples from its
   published definition; a fixture from the device with placeholder
   words; the hand-count harness with its published agreement.
2. **A local command for the parent.** `volley today` reads the Bee,
   counts, deletes the words, shows the day, and posts counts only.
   Test: run against a transcript full of names and assert none reach
   the output or the wire.
3. **A live API with keys.** Households post counts and read summaries
   with an API key; unknown fields are dropped at the door. Test: post a
   transcript, get it refused. Public interactive docs.
4. **An MCP server and an Agent Skill.** Spec 2025-11-25 over Streamable
   HTTP, seven tools, one of which returns no data by design. Test: a
   conformance run over real HTTP; a walk of every tool asserting no
   tool ever returns a word of speech.
5. **The site.** Everything in SITE.md, with the live panels. Test:
   Lighthouse accessibility 100 on both themes; every published number
   re-derived by a test from committed output.
6. **The video.** Under three minutes, public, English, 4K, captions.
   Test: every sentence in the narration appears on the site.
7. **Feedback, friction log, feature requests.** From the first day,
   starting with the speaker labels.
8. **The benchmark harness.** `harness/playlogue/`: the counter over
   the public corpus with its human labels, the two baselines, the
   negative-control stretches, results committed, and `volley verify`
   to recompute them. Test: the site's figures equal the committed
   results, and a run with a deliberately broken window fails.
9. **The loop back.** The one thing for tomorrow written into the
   parent's Bee as a todo with an alarm at the hour it names, through
   the CLI the product already uses, and readable back through Alexa+.
   Test: the argv is pinned; the text contains the fact's number and no
   other; nothing is written without the parent's setup consent.
10. **The parent's own page.** `volley connect` makes a household and
    prints a link to `/mine`; the page reads the day, the week and the
    note with the household's key from the browser. Test: the link's
    fragment carries the key and `today` posts counts with no word from
    the transcript to the household's own route. Built 2026-09-30.
11. **Two Strands agents.** The coach over Volley's MCP server with a
    gate that refuses any number no tool returned; the Tuesday agent
    holding Bee's MCP server beside Volley's under a five-tool
    allow-list. Test: a scripted model invents a number and the parent
    hears the tool results instead; the transcript tools are never
    offered. Built 2026-09-30; two real runs in AGENT.md.

See [WINNER_PATTERNS.md](WINNER_PATTERNS.md) for the audit the seventh,
eighth and ninth were added from.

## The twelve winner patterns, built in

Each pattern is a deliverable with an acceptance test and a date, not a
note. If a row is not done by its date, the submission page says so in
the same words rather than hiding it.

| # | Pattern | Deliverable in this plan | Acceptance test | By |
|---|---|---|---|---|
| 1 | Two numbers | The corpus figure and the live-Bee figure, side by side in the first sentence of the site and the submission | Both figures come from committed results; a test fails if either is missing | 10-10 |
| 2 | Cases from outside | `harness/playlogue/` over 33 hours of public parent-child recordings with human speaker labels; CHILDES media-linked corpora second | Results JSON committed; TalkBank citation present; no corpus data shipped | 10-09 |
| 3 | A named baseline beaten | Word count versus turns, and naive speaker changes versus the five-second rule, on the same recordings | The table on the site equals the harness output; the baselines are named as what a reasonable engineer builds | 10-09 |
| 4 | The refusal as the headline | Zero counts in single-speaker corpus stretches; zero on an adult-only conversation, a podcast, silence, on the operator's own Bee | Section 11 of the site opens with these numbers; the podcast run is done the day of Gate 1 | 09-30 and 10-09 |
| 5 | The loop closes into the user's system | The one thing for tomorrow written into the parent's Bee as an alarmed todo; Alexa+ reads it back | Argv pinned; a reminder visible in the Bee app in the video; never written without setup consent | 10-08 |
| 6 | Depth on one surface | Every Bee route: list, get, now, changed, stream, sync, Bee's MCP server held by our agent, the Skill | `volley evidence` records each call; `volley live` ticks on camera | 10-08 |
| 7 | Tagline as verbs | The four-verb tagline on the site, the repo and the submission | The same sentence in all three, checked by a test | 10-10 |
| 8 | The demo cannot break | Counting from a `bee sync` export offline; the browser drop zone; committed corpus numbers; recorded fallbacks that say they are recorded | Each path exercised in a test; the video uses live calls | 10-10 |
| 9 | A practitioner's sentence | One quoted sentence from one speech-language pathologist, paediatrician or preschool teacher, named with permission | On the site, or the site says nobody has yet | 10-10 |
| 10 | A shipped surface | `pip install volley-bee` and `pip install serve-return` on PyPI; API keys; a tagged GitHub release | A clean machine installs and runs `volley today` against a sync export | 10-10 |
| 11 | Limits as measured properties | The youngest-session undercount, the label disagreement, the corpus agreement, each a number; the rest named as the next study with its design | No public sentence says "unmeasured" without naming the study | 10-10 |
| 12 | Inspect and rerun | `volley verify`; a hash-chained evidence record; the test total counted on the page | `volley verify` prints no diff on the shipped commit; a broken window fails it | 10-10 |

## What the operator does, and when

- 2026-09-30: train the voice in the Bee app; one ten-minute
  conversation with another person; say so.
- 2026-10-08: hand-count five conversations from the Bee app's
  transcript view, blind to the counter, on a printed sheet.
- By 2026-10-10: one sentence from one practitioner. A speech-language
  pathologist, a paediatrician or a preschool teacher reads the page and
  says what they would do with the number. Their name and role, with
  their permission, on the site. This is the cheapest point on the
  winner-patterns list and only a person can get it.
- 2026-09-30, alongside Gate 1: play a twenty-minute podcast through a
  speaker with the band on and nobody speaking, so the device's own
  negative control is measured before the counter exists.
- 2026-10-13: an afternoon with the band on, with a child of talking age
  if possible; two seconds of phone video of the band on the wrist.
- 2026-10-16: upload the video; put the URL in the submission.

Everything else is built without the operator, including the Appstore of
this project, which is PyPI.

## What is reused, and what is new

Reused from Bellwether, by copying rather than depending, so each
repository stands alone: the Bee client with the device's real shapes,
the FastAPI and Mangum server skeleton, the CDK stack, the MCP transport
and its conformance script, the InfoButton, ThemeToggle, Nav and
McpProof components, the design tokens, and the video pipeline from
Earshot. New: the counter and its rule, the coach, the household model,
the hand-count harness, every word on the site, and the video.

## Risks that are not gates

- The five-second rule on text undercounts a two-year-old, who babbles
  rather than speaks. The stated age range is talking age, about three
  to six, until measured on a younger child.
- The Bee may label a third speaker in a busy home. The setup names the
  child; other speakers are ignored by default and counted as "other"
  on request.
- A parent may wear the band at work. Hours with no child speech count
  nothing, and the day view says so rather than showing zero as a
  failure.
- The coaching note could be read as judgement. It never compares one
  parent with another; the only comparison is the parent's own week and
  one published target, stated as the source's figure.
