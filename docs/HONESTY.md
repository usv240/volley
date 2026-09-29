# Honesty: privacy, consent, limits, and when to stop

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

## Limits, stated where the numbers are

- Age. The rule counts utterances the Bee transcribed. A toddler's
  babble may not be transcribed; the research instrument counts
  vocalisations acoustically. The stated range is talking age, about
  three to six, until measured on a younger child.
- The wearer. The parent wears the band, so the count is of the
  parent's exchanges, not everything the child heard from everyone.
- Speaker labels. The count is only as good as the Bee's labels. The
  harness measures the disagreement with a person and the site shows it.
- One family. Everything measured here is the operator's own household.

## Kill criteria, decided before building

1. If the Bee never labels the wearer apart from others after two
   attempts at voice training, the project stops (PLAN.md, Gate 1).
2. If the counter disagrees with a blind human count by more than the
   published automated-versus-manual disagreement and no rule change
   closes it, the number is presented as an estimate with that error,
   and the coaching note is limited to the best and quietest hours,
   which survive a noisy count.
3. If a real day cannot be shown on camera by 2026-10-13, this project
   is not submitted, and the others are untouched.
