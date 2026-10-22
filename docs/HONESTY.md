# Honesty: privacy, consent, and what it is not

## Privacy by construction

- The Bee makes the transcript and holds it in the parent's own account;
  that is Amazon's promise and the site links Amazon's notice rather
  than restating it.
- Volley reads the transcript on the parent's machine, counts, and drops
  the words from memory. Nothing textual is written to disk; the only
  files written are a cursor and the counts. A test runs the command in
  a temporary home and asserts that.
- The API accepts counts and drops every unknown field at the door. A
  transcript posted by mistake is refused, and the site shows this
  happening live.
- DynamoDB has no column that can hold text longer than a nickname, and
  a test asserts the schema.
- The MCP server has no tool that returns a word of speech, and a test
  walks every tool to prove it.
- The site's demo household is simulated and labelled as such on every
  view until the operator's own day replaces it, and then it is labelled
  as the operator's.

- The Tuesday agent (AGENT.md) is the one place text about the
  parent's day is read by a model: the Bee's own summary of the day,
  fetched on the parent's machine through Bee's MCP server, sent to
  Bedrock in the parent's own account for one answer, and stored
  nowhere. The transcript tools are not offered to that agent, so no
  word a child said can make the trip. Volley's service is not in the
  loop and never sees it.
- The parent's own page (`/mine`) reads counts with the household's key
  from the parent's browser. The key arrives in a link fragment, which
  browsers do not send to servers, and is kept in that browser's local
  storage only.

- The public corpus (CHILDES Gleason) is used under CC BY-NC-SA 3.0
  and the TalkBank ground rules, non-commercially. The transcripts stay
  on the builder's machine and are never committed, uploaded or sent to
  any service. The label-free role model is trained on them and ships
  under the same CC BY-NC-SA 3.0 licence (serve_return/models/NOTICE.md),
  not under the code's MIT licence; a commercial use would need a model
  trained on licensed data. Only counts reach the site. The three citations the rules ask for are on
  the site and in EVIDENCE.md.

## Consent

- The wearer is the adult. The child wears nothing.
- Recording other people is the wearer's responsibility under local law,
  and the setup screen says so in one sentence before anything runs. The
  site does not pretend this is Volley's to grant.
- The child's name is optional, used only to address the parent's note,
  and the site says why it is optional.
- Deleting is two commands: the Bee app deletes the conversation; the
  API deletes the household on request with its key.

## What it is not

- Not a diagnosis, not a screen, not a test of the child. A count, like
  steps. The site never shows a percentile for a child, never compares
  families, never uses "delay", "risk" or "behind".
- Not a promise about outcomes. The studies are associations and one
  coaching trial; the site says so where it cites them.
- Not aware of the television. The by-hour view is where a parent will
  notice quiet hours; the product does not say why they were quiet.

## Scope, stated where the numbers are

- Age. The rule counts utterances the Bee transcribed, so the stated
  range is talking age, about three to six.
- The wearer. The parent wears the band, so the count is of the
  parent's exchanges with the child.
- Speaker labels. The Bee labels every speaker "Unknown", so Volley
  reads the roles from the transcript; a day's count is what it is for,
  and the measured error sits on the site beside every number.
- Other adults. With every speaker "Unknown", two adults talking can
  read as turns; `volley setup --only-with-child yes` sets those
  stretches aside, measured on the Bee at 21 false turns to 0 with all
  66 real turns kept (harness/beeloop/with_child.json).
- Every number here comes from a public corpus and a replay of it on
  the Bee; no real family's words were used, and the site says which
  family is simulated on every card.
