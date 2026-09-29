# Volley against the twelve winner patterns

Audited 2026-09-29 against the plan, before any code. "What I have" is
the design as written; hours are for one person with Bellwether's and
Earshot's code to reuse. Blunt, as asked.

| # | Pattern | Status | Evidence in the plan | Fix and cost |
|---|---|---|---|---|
| 1 | Two numbers, not one | PARTIAL | One number was planned: agreement with a hand count on the operator's own conversations. That is a demo number | Add a controlled benchmark on a public corpus nobody here wrote (Pattern 2), and keep the live number from the operator's own Bee. 10 h |
| 2 | Cases from outside the builder's keyboard | MISSING | Every case in the plan is the operator's own household | Playlogue on Hugging Face: 33 hours of adult-child play from CHILDES, speaker-attributed and timestamped, diarisation ground truth as RTTM, CC BY-NC-SA 3.0 behind the TalkBank ground rules. Wire the counter to its transcripts and publish turns per hour against the human-labelled speakers. 6 h. Second: CHILDES media-linked corpora through childes-db (`media_start`, `media_end`), same licence, more hours, less structure. 4 h more |
| 3 | A named baseline that got beaten | MISSING | No baseline was planned | Two, both the thing a reasonable engineer builds instead. Word count (what Starling sold, and what the studies showed loses its predictive power after the income adjustment): on the corpus, show sessions with the same adult word count and turn counts that differ threefold. Naive speaker-change count with no window: show how far it overcounts against the five-second rule. 4 h |
| 4 | The negative control is the headline | MISSING | The plan mentions "away" hours only | Three refusals with numbers: an adult-only conversation counts zero child turns; a podcast played for twenty minutes counts zero turns; twenty minutes of silence counts zero. Then the corpus: turns counted in stretches the human labels mark as single-speaker. Measurable the day the counter exists. 3 h |
| 5 | The loop closes back into the user's system | PARTIAL | "One thing for tomorrow" was shown on a page | `bee todos create --text --alarm-at` exists. The note becomes a reminder in the parent's own Bee, alarmed at the hour it names, and Alexa+ can read it back. The product leaves something behind where the parent already lives. 3 h |
| 6 | Depth on one surface beat breadth | PASS, can go deeper | One device, every route into it: list, get, now, changed, sync markdown, the MCP server held by our agent, the Skill | Add `bee stream`: a live counter that ticks as the exchange happens, for the terminal shot and for a parent who wants to see it work. 4 h |
| 7 | The tagline is a chain of verbs or a result | PARTIAL | "A step counter for conversations with your child" is a metaphor, not the loop | "Counts the back-and-forth between you and your child from the Bee on your wrist, keeps the counts and throws the words away, and puts one thing to try tomorrow into your Bee as a reminder." 0 h |
| 8 | The demo could not break | PARTIAL | A deterministic floor under Bedrock; nothing else | The local command counts from a `bee sync` markdown export if the cloud is down; the site's drop zone counts in the browser with no server; the corpus numbers are committed so the evidence panel needs no network; the live panels have a recorded fallback that says it is recorded. 4 h |
| 9 | The author was the practitioner, or adoption stood in | MISSING | Neither. The operator is not a parent of a young child, a speech-language pathologist or an educator | One quoted sentence from one practitioner: a speech-language pathologist, a paediatrician or a preschool teacher who reads the page and says what they would do with the number. The operator's task, and the cheapest point on this list. 1 h of asking, plus their goodwill |
| 10 | A shipped surface beyond a demo URL | PARTIAL | PyPI for the package was planned | `pip install volley` as the whole product, not only the counter; the API with keys as a service; a GitHub release with a tag. 2 h beyond what is planned |
| 11 | Limits disclosed as measured properties | PARTIAL | Limits are stated; two are stated as unmeasured, which reads as unfinished | Measure the toddler undercount on the corpus (Playlogue is preschool age; the youngest sessions give a number), the label disagreement from the harness, and the corpus agreement. Anything still unmeasured is named as the study to run next, with its design, not as a gap. 2 h |
| 12 | Judges can inspect and rerun | PARTIAL | Tests as claims, the evidence record | `volley verify`: recompute the corpus numbers, the negative controls and the harness agreement from committed inputs and print a diff against the site's figures. The evidence record hash-chained per run. Test total on the page, counted. 3 h |

Total to close everything: about 45 hours, inside the build week.

## The three public case sets, and which to wire first

1. **Playlogue v1** (Hugging Face, `playlogue/playlogue-v1`; Kalanadhabhatta et al., IMWUT 2024). Preschool adult-child play, 33 hours, transcripts speaker-attributed and time-aligned, diarisation ground truth, DPICS codes on 4,773 parent and 3,895 child utterances. CC BY-NC-SA 3.0; audio is fetched from CHILDES after accepting the TalkBank ground rules. Fastest to wire: the transcripts already look like Bee utterances (speaker, start, end, text). This is the benchmark.
2. **CHILDES media-linked corpora via childes-db** (`childespy`; `media_start` and `media_end` from CHAT bullets). More hours and ages, less consistent timing. Second, for age coverage.
3. **The operator's own Bee conversations**, hand-counted blind. Not public, but not authored either: the third number, and the one the video shows.

Use of a CC BY-NC-SA corpus is for evidence, not for the product; the
site says so, cites TalkBank as it requires, and ships no corpus data.

## The negative control measurable by tomorrow

With the counter not yet written, the control that can be measured now
is the device's: play a twenty-minute podcast through a speaker with the
band on and nobody speaking. Expected: the Bee transcribes it as
"Unknown" and, once the counter exists, zero turns, because there is no
wearer utterance to pair with. Likely number: zero, with the risk being
that the Bee labels the podcast host as the wearer, which the Reddit
reports describe; if it does, that is a friction log entry and a real
limit with a number.

## The tagline (Pattern 7)

Counts the back-and-forth between you and your child from the Bee on
your wrist, keeps the counts and throws the words away, and puts one
thing to try tomorrow into your Bee as a reminder.

## The first sentence of the submission (Pattern 1)

On 33 hours of public parent-child recordings that we did not make,
Volley's count of conversational turns agrees with the human speaker
labels within N percent and counts zero in the M stretches where only
one person is speaking; on the operator's own Bee, it agreed with a
blind hand count on five conversations within K turns and put tomorrow's
reminder into the Bee.

(N, M and K are measured before the sentence is published, and the
sentence is not published if they are not.)

## The one change that moves the most

Pattern 2, the public corpus. It converts the whole evidence section
from "we counted our own afternoon" into "we counted 33 hours of
recordings that psychologists made, against their labels", and it
supplies Patterns 1, 3, 4 and 11 from the same wiring: the second
number, the baseline columns, the negative control stretches and the
measured limits all fall out of one harness on one dataset. Six hours
that change what the project is.
