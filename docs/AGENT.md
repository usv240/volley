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
Volley's. What it may reach on the Bee side is a five-tool allow-list:
the daily summaries, today's brief, the to-do list and creating one
to-do. The transcript, search, photo and location tools are named in a
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
the operator's own signed-in Bee, on the simulated household because
the operator's own has no labelled day yet (see SUBMISSION.md).

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
the agent said so rather than inventing one.

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
```

AWS credentials with Bedrock access are needed for the model; the
tests need none, because they drive the agents with a scripted model
and a Volley server on a free port.
