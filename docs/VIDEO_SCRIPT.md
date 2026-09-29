# Demo video script

Under three minutes, public, English. Judges are not required to watch
past 3:00, so the strongest material is first and nothing is held back
for a reveal.

The one sentence this video has to land, in the first fifteen seconds:
**your child's brain is built in the back-and-forth, and no parent has
ever been able to count it.**

This file is written by `python video/beats.py --script` from the same
data the recorders and the assembler read, and a test fails if the two
ever disagree. Edit `video/beats.py`, not this file.

---

## Shot list

**0:00, claim, the website, in a real browser**

The front page: the claim, the tagline, and a simulated family's day beside it.

> Your child's brain is built in the back-and-forth. Not in how many words they hear. In how often they say something and you answer within five seconds. That number predicted their vocabulary and IQ a decade later, and no parent has ever been able to count it.

**0:19, stakes, the website, in a real browser**

The three figures under the claim, pointed to in turn.

> Fourteen to twenty-seven percent of the variance in IQ at age ten, after adjusting for income. Turns, not words, is what the brain's language area responded to. And it's coachable: parents shown their own recordings raised it, and the gain held to thirty months.

**0:36, rule, the website, in a real browser**

The twenty-second exchange played, the five-second windows fading, the count ticking up.

> Here is the rule, counting. Each bar is something somebody said. A reply that starts inside the five-second window is a turn. Two adult bars close together merge. Six seconds of silence ends the exchange. Five turns in twenty seconds.

**0:52, term-today, a terminal, a real run rendered**

A terminal: volley today against the operator's own Bee, the day printed as bars, the words counted and thrown away.

> On my own Bee, this morning. One command reads the day, counts, and deletes the words. The only files it writes are the counts and a cursor.

**1:03, day, the website, in a real browser**

The day like steps, the week beneath, and tomorrow's one thing beside it.

> The day, an hour at a time. Hours with no child are away, not zero. And one thing for tomorrow, written from the counts and, with your consent, placed in your Bee as a reminder at that hour.

**1:18, term-reminder, a terminal, a real run rendered**

A terminal: the reminder appears in the Bee's todo list with its alarm, then the counter ticking during a live exchange.

> It landed in the Bee. And if you want to watch it work, it counts live as you talk.

**1:26, refused, the website, in a real browser**

A transcript full of names sent to the live server; every text field dropped; the counts kept.

> The server never sees a word. Here a transcript with a name, a doctor, an address and an account number is sent to the real intake route. Every one of them is dropped at the door. The counts survive.

**1:41, agent, the website, in a real browser**

A session held against the MCP server from the page, every request timed, the tool that returns no data.

> For Alexa Plus, an MCP server, held to a real session from this page. It can say how the talking went and what to try tomorrow, and it cannot repeat a word, because it never has one.

**1:56, honest, the website, in a real browser**

The evidence section: what it refused, what it beat, what nobody has done yet, each stated as measured or not yet.

> What is not yet measured says so on the front page, in the same size as the numbers. Nothing here is a test of a child. It is a count, like steps.

**2:08, close, the website, in a real browser**

What it will never say.

> You already talk to your child. Now you can see it.

Estimated 2:13 of a 3:00 ceiling. The real narration decides the
final cut, and `python video/beats.py` exits non-zero if the plan is
over before a frame is recorded.

---

## The terminal beats

Two beats show real commands against the operator's own Bee. They are
recorded by `record_term.py`, which runs the commands for real, keeps
their output, and renders it in a terminal frame the same 4K recorder
captures, typed at a human pace; the frame says it is a rendering of a
real run. Nothing is invented and nothing is sped up. They need the
device's speaker labels (Gate 1 in PLAN.md); until then the assembler
cuts the web beats on their own and says which beats it dropped.

## What not to do

Do not name a condition, a percentile or a child's standing. Do not say
the count predicts anything about this child. Do not show a word of
any transcript, even the operator's own.
