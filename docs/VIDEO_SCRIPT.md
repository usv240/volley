# Demo video script

Under three minutes, public, English. Judges are not required to watch
past 3:00, so the strongest material is first and nothing is held back
for a reveal.

The one sentence this video has to land, in the first fifteen seconds:
**the words were not the point; the back-and-forth was, and Volley
counts it on the Bee you already wear.**

This file is written by `python video/beats.py --script` from the same
data the recorders and the assembler read, and a test fails if the two
ever disagree. Edit `video/beats.py`, not this file.

---

## Shot list

**0:00, hook, the website, in a real browser**

Black, the words Steps. Sleep. Heartbeats.; then the first screen under them: the headline, the lede, the day card's number.

> We count our steps, our sleep, even our heartbeats. But what about the conversations that help children grow? Meet Volley: a step counter for the back-and-forth between you and your child. On the Bee you already wear, it counts the exchanges, finds your best hour, and nudges you when that hour goes quiet. The numbers, never the words.

**0:23, how, the website, in a real browser**

How it counts, in twenty seconds: Play pressed, the bars appearing, replies inside five seconds lit, the count reaching five.

> Here is how. A parent speaks. A child answers inside five seconds. That is one turn. Volley reads who is talking from the words and the pauses, and keeps only the count.

**0:36, term-count, a terminal, a real run rendered**

A terminal on the builder's own Bee: volley today; three captions in turn, REAL BEE DATA, 66 TURNS DETECTED, REMINDER CREATED; under them, a research conversation replayed through a physical Bee.

> Now on my own Bee. We played a real family's recorded conversation to the band. One command reads it, finds sixty-six turns, deletes every word on my own computer, and places one thing to try tomorrow into the Bee itself.

**0:52, term-reminder, a terminal, a real run rendered**

A terminal: the reminder in the Bee's todo list, its alarm at three the next afternoon, its sentence; caption IN THE BEE, DUE AT 3PM.

> There it is, in the Bee, for three in the afternoon, with something to do.

**1:01, term-nudge, a terminal, a real run rendered**

A terminal labelled live Bee stream: volley live watching the usual hour, the hour going quiet, the nudge printed and placed in the Bee; its sentence held large for the rest of the beat. The real run.

> Volley does not only count yesterday. During the hour we usually talk most, it watches the Bee's live stream. If that hour goes quiet, the nudge reaches the Bee right then, and a speaker in the room says it, the way an Echo could. One idea, while there is still time to connect.

**1:22, plan, the website, in a real browser**

The day, an hour at a time; then the week's plan, written by Claude on Amazon Bedrock, the three lines pointed to in turn, then the gate line.

> Over a week, patterns appear: a busy evening, a quiet afternoon with the child right there. Claude on Amazon Bedrock turns them into practical coaching, the way a home visitor would: keep the hour that works, one idea for the quiet one, one for the weekend. A gate in code refuses any number the counts did not hold.

**1:45, proof, the website, in a real browser**

Three large numbers, one at a time: 26.59 hours, 20,344 turns, 66 of 75; then the evidence row where two adults count as zero beside the real conversation's sixty-six.

> Does it hold up? Twenty-six hours of independent family recordings. Twenty thousand turns counted, and none where one person spoke alone. On the Bee, sixty-six of seventy-five: an undercount, and we publish it. And with the child-present check on, two adults with no child in the room count as zero.

**2:04, ecosystem, the website, in a real browser**

Ask out loud: a question tapped, the tool call line, the answer read aloud. Then the agents section on the evidence page, simulated Bee data labelled first.

> Parents can ask out loud. Volley's MCP server lets Alexa Plus answer from the counts alone; it never had a word to repeat. Two Strands agents explain a quiet day from the Bee's own summary, one hosted on AgentCore. This one runs on simulated Bee data.

**2:22, beyond, the website, in a real browser**

The coach's list of families; then the install line and the cost.

> For families with a home visitor, a read-only view carries the coaching between visits: counts and the note, never a word of speech. Open source on PyPI. Four cents a family a month, on a band they already wear.

**2:38, close, the website, in a real browser**

The first screen, pointer hidden; then the final card: Volley, a step counter for conversations with your child, built on Bee and AWS.

> Volley does not ask parents to talk more. It helps them notice when to connect. Because what matters is not how many words we say. It is the conversations we share.

Estimated 2:50 of a 3:00 ceiling. The real narration decides the
final cut, and `python video/beats.py` exits non-zero if the plan is
over before a frame is recorded.

---

## The terminal beats

Three beats show real commands against the builder's own Bee. They are
recorded by `record_term.py`, which runs the commands for real, keeps
their output, and renders it in a terminal frame the same 4K recorder
captures, typed at a human pace; the frame says it is a rendering of a
real run. Nothing is invented and nothing is sped up. The nudge beat is
the real afternoon run, captured when the family's usual hour comes;
until it exists the assembler cuts without it and says so.

## What not to do

Do not name a condition, a percentile or a child's standing. Do not say
the count predicts anything about this child. Do not show a word of
any transcript, even the builder's own. Do not present anything as a
problem, a bug or a limit: the video shows what works; the written
feedback carries the findings.
