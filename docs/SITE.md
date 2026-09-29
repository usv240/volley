# The site

One page, read top to bottom in one pass by somebody who has never heard
of any of this, and by a judge with three minutes. Two audiences, never
mixed in one sentence: the parent reads the page; the developer and the
researcher read the i-buttons and the sections at the end.

## Principles, and the reason for each

- **One idea per screen.** Each section answers one question and its
  heading is the answer. A visitor who reads only headings still gets
  the whole story.
- **Progressive disclosure.** The page says the simple thing; the
  i-button beside it says the precise thing with its source. Nobody is
  made to read the precise thing to understand the simple one.
- **Show, do not claim.** Every claim on the page has a panel that does
  it live: the counter running on a real exchange, a transcript refused
  by the API, an MCP session held from the page.
- **The first fifteen seconds.** Above the fold: what it is, why it
  matters, and what to press. Tested by asking one person who knows
  nothing to say what the product is after fifteen seconds.
- **Reading measure 60 to 75 characters**, Inter at 17 px for body,
  Fraunces for display, a type scale with four sizes and no fifth.
- **Colour never carries meaning alone.** Every state has a word or a
  shape too. Contrast AA everywhere, AAA for body text.
- **Light by default, dark by choice**, both palettes chosen, not
  inverted, and every chart mark validated on both surfaces.
- **Mobile first.** Every section works at 360 px wide; the day view is
  a vertical list of hours on a phone and a bar row on a desk. Touch
  targets 44 px. No hover-only behaviour anywhere.
- **Reduced motion respected**; focus always visible; a skip link;
  semantic headings in order; every i-button a real button.
- **No jargon without an i.** The i-buttons are a glossary the visitor
  opens where the word is, not a page they have to find.

## The sections, in order, with copy outline

### 1. Hero: the claim and today's number

- Eyebrow: "A step counter for conversations with your child"
- Heading: "Your child's brain is built in the back-and-forth. Volley
  counts it."
- The tagline, a chain of verbs, under the heading: "Counts the
  back-and-forth between you and your child from the Bee on your wrist,
  keeps the counts and throws the words away, and puts one thing to try
  tomorrow into your Bee as a reminder."
- The first sentence a judge reads, the two numbers: "On 33 hours of
  public parent-child recordings we did not make, the count agrees with
  the human speaker labels within N percent and counts zero where only
  one person is speaking; on the operator's own Bee it agreed with a
  blind hand count within K turns." (N and K are filled by the harness
  and the sentence does not ship without them.)
- Right: today's day view for the demo household, labelled "A
  simulated family, until the operator's own day replaces it": turns
  today, best hour, one thing for tomorrow. Two buttons: "See how it
  counts" (scrolls to the worked example) and "Count your own"
  (scrolls to bring your own data).
- i-buttons: "exchange", "turn", "why counts and not words".

### 2. Three figures, with their sources on the i

- "14 to 27 percent": of the variance in IQ and vocabulary at ages 9 to
  14 explained by conversational turns at 18 to 24 months, after
  adjusting for family income (Gilkerson, Pediatrics 2018).
- "Turns, not words": the brain's language area responded to turns, not
  to the number of words heard (Romeo, Psychological Science 2018).
- "Coachable": parents shown their own recordings raised turns and their
  children's language, and the gain held to 30 months (Ferjan Ramirez,
  PNAS 2020; Huber, Developmental Science 2023).
- Each figure's i says what the study did, what it did not show, and
  that it is the study's number, not ours.

### 3. What it is, why it exists, how it runs

Three short columns, plain words.

- What: "A count of the back-and-forth between you and your child, by
  the hour, every day."
- Why: "The studies that found this number used a research recorder
  families cannot buy. You already own the wearable that can do it."
- How: "Your Bee transcribes the day. Volley reads the transcript on
  your computer, counts, and deletes the words. Only the counts leave."
- i-buttons: "Bee", "on your computer", "what leaves".

### 4. How it counts, watched

The worked example: a real twenty-second exchange (from the operator's
own day, with the words replaced by "adult" and "child" bars) drawn on
a time line, with each turn marked as it is counted, the five-second
window shown as a fading band after each utterance, and the count
ticking up. A "Play" button, not autoplay. Below it, the rule in one
sentence with its source on the i, and a link to the package.

### 5. The day, like steps

The full day view: hours across, turns per hour as bars in one hue,
the best hour labelled, hours with no child present shown as "away",
not zero. A weekly strip beneath. Under it the one thing for tomorrow
in a quote block, "written from today's counts", with an i that shows
the structured fact it was written from and says a template is used if
the model is unavailable.

### 6. What it will never say

Four cards, the honesty section, in the same type size as the numbers:
"It is not a test of your child." "It does not compare you with other
families." "It never keeps a word." "It does not know what the
television was doing." The last card cites the finding that television
hours reduce turns and says the by-hour view is the only place a parent
will see it, because nothing in this product watches the television.

### 7. Privacy, demonstrated

`PrivacyProof`: a button that posts a transcript full of made-up names
to the live API and shows the response with every text field gone and
only counts accepted. The request and the response, on screen, timed.
Beneath: what the Bee itself keeps, in Amazon's words, linked, because
that is not ours to promise.

### 8. Your Bee, in ten minutes

Five steps, each badged "works today" or "needs your Bee": install the
CLI, enable Developer Mode (tap the version five times), `bee login`,
`pip install volley`, `volley setup` and `volley today`. The exact
commands, copyable, and what the screen shows at each step.

### 9. Bring your own data

Three doors, side by side, with who each is for:

- Parents: "Your Bee, on your computer" (the steps above).
- Anyone curious: "Drop a Bee export here": the drop zone that counts
  in the browser and uploads nothing unless asked.
- Developers: "An API key": create a household, post counts, read the
  week; interactive docs; the schema that drops unknown fields, shown.

### 10. Alexa+: ask it out loud

`McpProof`: a real session from the page, every request timed, the tool
called being the one that returns the rule and no data. The seven tools
listed with one line each and an i that says what each returns and
never returns. The Agent Skill linked.

### 11. What it refused to count

The negative controls as the headline of the evidence, before any
agreement figure: zero turns in the single-speaker stretches of the
public corpus (with the count of stretches), zero on an adult-only
conversation, zero on a podcast, zero on silence, each with what the
device actually did. A measured refusal is worth more to a judge than a
measured success, and the section is built in that order.

### 11b. Against the obvious alternatives

Two columns, measured on the same recordings: word count (what the last
consumer device counted, and what the studies found stops predicting
once income is accounted for) against turns, with the sessions where
the same word count hides a threefold difference in turns; and a naive
speaker-change count with no window against the five-second rule, with
the overcount. The point of the product in one table.

### 11c. For researchers

The `serve-return` package, the rule and its source, the corpus harness
and its results, and the hand-count table: five conversations, the
person's count, the package's count, the agreement, stated whichever
way it came out, next to the published agreement for the research
instrument. `volley verify` reruns all of it.

### 11d. One practitioner

One quoted sentence from one speech-language pathologist, paediatrician
or preschool teacher who read this page, with their name and role, and
what they would do with the number. If nobody has said one by the
deadline, the section says that nobody has yet, in the same type size.

### 12. Evidence, read from the literature and measured here

Three cards kept apart on purpose: measured here (the harness), read
from the literature (the studies, with what each does and does not
show), and nobody has done yet (a real child under three; a family other
than the operator's).

### 13. For developers

Run it: the commands. Use the engine: six lines of Python. Links to the
repository, the method, the prior art, the friction log, the skill.

### 14. Questions a parent asks

Eight questions in the parent's words, each answered in two sentences:
"Is a low day bad?", "Does it listen to my child?", "What if my child
does not talk yet?", "Do I need to talk all day?", "What is a good
number?", "Who can see this?", "What about the television?", "Can I
delete it?"

### 15. Footer

Open source, MIT. The repository. The Bee's own privacy notice. "Not a
diagnosis, not a test, a count."

## The i-button glossary (every term, one paragraph each, with source)

turn; serve; return; volley; the five-second rule; exchange versus word
count; parentese; response time; question; best hour; "away" hours;
percentile (and why the site never shows one for a child); SES and why
the studies adjusted for it; LENA; Bee; Developer Mode; on your
computer; counts only; API key; household; MCP; Agent Skill; Bedrock
and the deterministic floor; the hand-count harness; what "validated"
means and what is not validated here.

## Light and dark

Both palettes chosen from the shared tokens; a blocking script sets the
theme before paint; the toggle is two states with `aria-pressed`; every
chart colour validated on its own surface; images and the worked
example redrawn in both.

## Mobile and desktop

360 px to 1440 px, tested at 360, 768, 1024 and 1440. The day view
becomes a list under 640 px. The nav collapses to a menu under 1280 px.
Tables get a horizontal scroll with a visible edge. The i-button popover
becomes a bottom sheet under 640 px.

## The first-time test

Before the site ships, three people who have never seen it read it on a
phone with no help. Each is asked, after fifteen seconds and after two
minutes: what is this, who is it for, what would you press. Their
answers, and what was changed because of them, are recorded in the
friction log, because that is also feedback on how the product explains
itself.
