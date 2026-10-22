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

Black, the words thirty million words, then the first screen under them; the headline pointed to on the back-and-forth.

> You have heard of the thirty-million-word gap. For years, parents were told: talk more. Then researchers looked inside children's brains, and the words were not the point. The back-and-forth was.

**0:15, volley, the website, in a real browser**

The first screen: the day card's number, then the lede, then a hold on the day card.

> Meet Volley: a step counter for conversations with your child. On the Bee you already wear, it counts the exchanges, shows the hour they happen, and nudges you when your best hour goes quiet. The numbers, never the words.

**0:30, how, the website, in a real browser**

How it counts, in twenty seconds: Play pressed, the bars appearing, replies inside five seconds lit, the count reaching five.

> Here is how. A parent speaks. A child answers inside five seconds. That is one turn. Volley reads who is talking from the words and the pauses, and keeps only the count.

**0:44, term-count, a terminal, a real run rendered**

A terminal, labelled real Bee, a replayed research conversation: volley today on the builder's own Bee; the bar, sixty-six turns, the words thrown away, the reminder placed.

> Now Volley on my actual Bee. We played a real family's recorded conversation to the band. One command reads it, finds sixty-six turns, deletes every word on my own computer, and places one thing to try tomorrow into the Bee itself.

**1:00, term-reminder, a terminal, a real run rendered**

A terminal: the reminder in the Bee's todo list, with its alarm at three the next afternoon and its sentence.

> There it is, in the Bee, for three in the afternoon, with something to do.

**1:09, term-nudge, a terminal, a real run rendered**

A terminal, labelled live Bee stream, a speaker standing in for an Echo: volley live watching the usual hour, the hour going quiet, the nudge printed and placed in the Bee. The real run.

> But Volley does not only count yesterday. During the hour we usually talk most, it watches the Bee's live stream, and if that hour goes quiet, a nudge reaches the Bee right then. A speaker in the room says it, the way an Echo could. While there is still time to connect.

**1:30, plan, the website, in a real browser**

The day, an hour at a time; then the week's plan, written by Claude on Amazon Bedrock, the three lines pointed to in turn.

> Over a week, patterns appear: a busy evening, a quiet afternoon with the child right there. Claude on Amazon Bedrock turns them into a plan the way a home visitor would: keep the hour that works, one idea for the quiet one, one for the weekend. A gate in code refuses any number the counts did not hold.

**1:53, proof, the website, in a real browser**

The evidence table: the corpus row, the Bee row, then the child-present row where two adults count as zero beside the real conversation's sixty-six.

> Does it hold up? On twenty-six hours of independent family recordings: twenty thousand turns, and none where one person was talking alone. On the Bee, sixty-six of seventy-five. And with the child-present check on, two adults talking with no child in the room count as zero, while a real conversation keeps all sixty-six.

**2:13, ecosystem, the website, in a real browser**

Ask out loud: a question tapped, the tool call, the answer read aloud. Then the agents section on the evidence page, simulated Bee data labelled first.

> Parents can ask out loud. Volley's MCP server answers Alexa Plus from the counts alone; it never had a word to repeat. Two Strands agents on Bedrock, one hosted on AgentCore, explain a quiet day from the Bee's own summary. This one runs on simulated Bee data.

**2:32, beyond, the website, in a real browser**

The coach's list of families; then the install line and the cost.

> For families with a home visitor, a read-only view carries the coaching between visits. The counter is open source on PyPI. Four cents a family a month, on a band they already wear.

**2:45, close, the website, in a real browser**

The first screen again, resting on the headline; the pointer hidden; the last line held.

> Volley is not about counting every word. It is about making room for the conversations that matter. You already talk to your child. Now you can see it.

Estimated 2:56 of a 3:00 ceiling. The real narration decides the
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
