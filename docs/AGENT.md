# The agents: Strands over Volley's MCP server

Two agents in `apps/agent`, built on the Strands Agents SDK, each a
client of the same MCP server Alexa+ would use. They exist to show two
things the MCP server alone cannot: what an assistant does with seven
numeric tools and a rule that it may not say a number they did not
return, and what happens when the parent's own Bee is put beside
Volley without either server learning of the other.

## The coach

`Coach(mcp_url, household_id, api_key)` wraps every MCP tool so the
model sees no credential argument on any of them; the wrapper adds the
household's id and key on the way out. A test asserts the key never
appears in anything the model was given.

Every answer passes a gate before it is returned:

- every number in the answer must have come back from a tool, with an
  hour allowed on either clock (18, or six in the evening) and a date
  allowed in pieces;
- none of the words the coach never uses may appear: delay, behind,
  risk, deficit, disorder, diagnosis, percentile, IQ.

A refused answer is sent back once with the violation named ("numbers
no tool returned: 45"). A second refusal is replaced by the tool
results read out plainly. The result says which of the three happened
(`model`, `model-after-correction`, `plain`) and lists the refused
sentences, so a run is its own evidence.

The model is the same Bedrock ladder the server's note uses, as a
Strands `ModelRouter` with `FallbackStrategy`, which tries the rungs in
order and sinks one that keeps failing.

## The Tuesday agent

"Why was Tuesday quiet" is a question the counts cannot answer and the
parent's own Bee can. `Tuesday` holds Bee's MCP server (`bee mcp
serve`, over stdio, through the CLI the parent signed in) beside
Volley's. What it may reach on the Bee side is a four-tool allow-list:
the daily summaries, the to-do list and creating one to-do. Today's
brief was on it until 2026-10-21, when its definition turned out to
return captured conversations; it is now refused with the transcript
tools, and no recorded run had called it. The transcript, search, photo and location tools are named in a
second list and never offered; a stand-in server with the real 34 tool
names, captured on 2026-09-30, is what the test runs against.

Volley's server sees a household id and a key. Bee's server sees its
own calls. Neither is told the other exists. The one place both sets of
facts meet is the model, in the parent's own AWS account, for the
length of one answer; nothing is stored. The Bee's day summary is text
the Bee wrote about the parent's day, and it does go to the model; no
word a child said can, because the tool that carries it is not
offered.

## Two real runs, 2026-09-30

Sonnet on the ladder's first rung, against the deployed MCP server and
the operator's own signed-in Bee, on the simulated household, because
these runs predate label-free counting and the operator's own Bee had no
labelled day then (see SUBMISSION.md).

```
$ volley-agent coach --demo "how was our talking today, and what should I try tomorrow?"
You and your little one had 157 turns today, your liveliest stretch was at six in
the evening, and the quietest time when your child was around was at four in the
afternoon. Tomorrow, try leaning into that six o'clock window, that's when the two
of you are most in tune, with 38 turns in that hour alone. See if you can bring a
little of that same energy to four o'clock too!
  [model; tools: how_was_our_talking_today, one_thing_for_tomorrow]
```

```
$ volley-agent tuesday --demo "Which day this week was the quietest for talking,
  and what was I doing that day according to my Bee?"
The quietest day this week was September 24, with 156 turns, the lowest of the
seven days. Unfortunately, your Bee doesn't have a summary captured for that day,
so I can't tell you what was filling your time. If you remember what was going on
that day, that context might help explain the lighter count!
  [model; tools: week_trend, bee_list_daily_summaries, bee_get_daily_summary]
```

The Bee has no summary for the 24th because it arrived on the 29th;
the agent said so rather than inventing one. That is why this Tuesday
run failed to explain the quiet day: it paired the simulated
household's counts with a real Bee, and a real Bee holds a real
person's days, not the simulated family's. Even a Bee that had been
worn on the 24th would have described someone else's Thursday.

## A run with a SIMULATED Bee, 2026-10-21

To show the Tuesday agent doing its job without a real person's day
reaching the model, `apps/agent/volley_agent/sim_bee.py` is a
SIMULATED Bee: an MCP server over stdio that offers the five allowed
tools under the names and argument shapes `bee mcp serve` uses (read
from the @beeai/cli 0.7.3 tool definitions), plus
`bee_get_conversation_transcript` so a test can show the allow-list
drops it. It holds fourteen short days written for the simulated
household (Asha, 2026-09-15 to 2026-09-28); the quietest day, the 24th,
has an ordinary reason, a long drive to the grandparents and a late
nap. Every response carries `"simulated": true` and a SIMULATED notice,
and so does every tool description. The real Bee was not started.

Simulated Bee, simulated household, Sonnet
(`us.anthropic.claude-sonnet-4-6`, the ladder's first rung), against
the deployed MCP server. The whole run, tool inputs and results
included, is in `apps/agent/runs/tuesday-sim.json`.

```
$ python -m volley_agent tuesday --sim-bee --record apps/agent/runs/tuesday-sim.json \
    "Which day this week was the quietest for talking, and what was I doing that day according to my Bee?"
Your quietest day was September 24, with 156 turns, the lowest of the week. Your
Bee shows you spent most of that day on a long drive to the grandparents and back,
with Asha napping through much of it. That explains the count perfectly, she was
asleep in the car seat for big stretches of the day!
  [model; tools: week_trend, bee_list_daily_summaries, bee_get_daily_summary]
```

The model's first Bee call asked for 2025-07-14 to 2025-07-20, its own
guess at "this week", made before `week_trend` had answered; the
simulated Bee returned nothing for those dates, and the model then
fetched the 24th by date. "Most of that day" stretches the summary,
which says the drive took the evening.

The first attempt, a minute earlier, is kept in
`apps/agent/runs/tuesday-sim-first-attempt.json`. It passed the gate
and called the 24th a Wednesday; it was a Thursday. The gate checks
numbers, and 24 was a returned number, so a wrong weekday got through,
the same kind of error as Haiku's misread week below. No tool returns
a weekday, so the Tuesday prompt now says to give a date as a month and
day, never with a day of the week, and the run above is the one after
that change.

## What the gate caught before these runs

Two earlier runs are worth recording because they are why two things
changed the same evening:

- Haiku, asked the same question, answered "September 28th was your
  quietest day with 157 turns" when the 28th was not the quietest; the
  number was real, so the gate passed it, and the error was a reading
  of seven rows. `week_trend` now returns `quietest_day` and `best_day`
  so the model is not asked to compute either.
- The coach's third tool call once failed with "Unknown or terminated
  session": the request landed on a second Lambda instance that had
  never seen the session the first one issued. Sessions are now signed
  rather than remembered, valid on every instance, and a test starts a
  second server from nothing and hands it the first one's session.

## Running them

```
pip install -e "apps/agent"
volley-agent coach --demo "what is the best hour this week"
volley-agent tuesday "why was Tuesday quiet"          # your own household, after volley connect
volley-agent tuesday --sim-bee "why was the 24th quiet" # SIMULATED Bee, simulated household
```

`--record PATH` writes the question, the tools offered and called with
their inputs and results, the answer, its layer and the model to PATH.

AWS credentials with Bedrock access are needed for the model; the
tests need none, because they drive the agents with a scripted model
and a Volley server on a free port.
