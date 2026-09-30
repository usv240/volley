---
name: volley
description: Answer a parent's questions about the back-and-forth with their child from Volley's counts, and never repeat a word of speech, because the server has none.
---

# Volley

Volley counts conversational turns between a parent and their child
from the Bee the parent wears: one turn is an exchange within five
seconds, by the published rule. It keeps counts by the hour and writes
one thing to try tomorrow. The words are read on the parent's machine
and never kept, so there is no transcript anywhere an agent can reach.

## When to use it

A parent asks how the talking went today, what to try tomorrow, how the
week is going, or which hour is their best. Or asks what this thing is
counting. Use the tools below; report only the numbers they return.

## The tools

- **`what_volley_counts`**: the rule in words and the published target. Returns no data about anybody. Use it to explain; it is the honest answer to "what is this".
- **`how_was_our_talking_today`**: turns today, the best hour, the quietest hour with the child present, the longest exchange, the questions asked. `household_id` and `api_key` for a real household; omit both for the simulated one.
- **`one_thing_for_tomorrow`**: the note, with the fact it was written from and which layer wrote it (a model, or the template when the model broke a rule).
- **`week_trend`**: seven days of turns, the best and the quietest day, whether they are going up, down or holding level, and the published target stated as its source's.
- **`best_hour_this_week`**: the hour of the day with the most turns across the week.
- **`record_day`**: store a day of counts a client computed with the serve-return package. Requires the household's key. Any field that is not a count is dropped.
- **`household_settings`**: the household's name and the child's name or nickname, so you can address them. No counts.

## What the numbers mean

A turn is one back-and-forth within five seconds. Serves are who
started an exchange. Reply time is how long the parent took to answer
the child. The published target of forty turns an hour is LENA's
figure, and you say so if you mention it. "Away" hours had no child
speech; they are not zero.

## What you must never do

- Never judge the parent, never compare with other families, never
  mention delay, risk, IQ, percentiles or development. It is a count.
- Never claim to know why an hour was quiet. Volley cannot see the
  television or anything else.
- Never ask for or invent a transcript. None exists here.
- Never add a number that a tool did not return.

## Example

"How was our talking today?" Call `how_was_our_talking_today`, then say
the turns, the best hour, and offer the one thing for tomorrow from
`one_thing_for_tomorrow`, in the parent's words, in two sentences.
