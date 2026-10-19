# Feature requests

Each from something we hit building Volley, with the friction log entry
that produced it. Urgency uses the hackathon's scale: **critical**,
**important**, **nice-to-have**.

## Bee

### 1. Carry the enrolled voice through to the developer data as a speaker label

**Critical.** Volley counts back-and-forth between a parent and a child,
so it has to know who said each thing. On this account 1,004 of 1,004
utterances across 25 sessions came back `speaker: "Unknown"` on
2026-10-19, after the app had enrolled the wearer's voice. A
`speaker: "wearer"` or an `is_wearer` boolean would make the count exact
for the parent's side. Volley now reads the roles from the words and the
pauses instead (73.7 percent per utterance, the day's count within 12.2
percent in the median held-out session), and says plainly that one
boolean would beat it. Friction log entries 1, 4 and 5.

### 2. Split utterances where the speaker changes, not only where the speech pauses

**Nice-to-have, downgraded after measuring.** On 2026-10-19 a 190-second parent-child conversation played to the band kept 75 of 75 turns in the Bee's own segmentation, so this did not bite on clean, two-voice audio. It is kept for real rooms with overlap. A two-year-old answers a parent in well under a second.
If the device merges the question and the answer into one utterance,
the turn is gone before any software can count it, labels or no labels.
The CHILDES corpus's own segmentation puts the median reply gap well
inside a second. A boundary at each change of voice, even unlabelled,
would preserve every turn. Friction log entry 5.

### 3. A way to name a speaker in the app, and have the name reach the CLI

**Important.** The app offers no way to say "this voice is my
daughter". Even a per-conversation rename would let a parent correct
the record once and have every later session follow. Friction log
entry 4.

### 4. Times in `bee sync` exports

**Nice-to-have.** The markdown export carries no per-utterance times, so
anything built on it can only estimate the five-second rule. Friction
log entry 3.
