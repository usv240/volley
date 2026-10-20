# The product path, on the Bee, 2026-10-19

`harness/beeloop` scores the Bee's transcript against the truth. This is
the other half: the command a parent runs, `volley today`, on that same
Bee session, end to end, with nothing in between.

The session is 11418600: a real CHILDES mother-child conversation voiced
by Amazon Polly, an adult and a child voice at the original timing,
played to the band for 190 seconds with no person in the room. The Bee
recorded it, transcribed it and labelled every speaker "Unknown".

```
volley setup --blind --tz -4 --reminders yes
volley today --conversation 11418600
```

`--conversation` reads that one session and nothing else. A Bee worn all
day also hears work and strangers, and counting those as family talk
would be wrong twice.

## What it printed

```
2026-10-19: 66 turns with your child
  15:00   66  ########################
  best hour 15:00; longest exchange 58 turns; 25 questions asked
  517 words read and thrown away

Tomorrow: Your best hour with your child was around 3 in the afternoon, with 66 turns. Keep that one exactly as it is.  [template]
  placed in your Bee as a reminder
  517 words read on this machine, 0 kept
```

## What it did

- **Read** the session through `bee conversations get 11418600 --json`,
  on this machine.
- **Counted** 66 turns with no speaker labels, the same 66 that
  `harness/beeloop` reports against 75 true turns, so the scorer and the
  product agree.
- **Threw the words away**: 517 read, 0 kept. The only file written is
  `~/.volley/counts/2026-10-19.json`, numbers only: turns 66, questions
  25, longest exchange 58, best hour 15, adult talk 136.1 s, child talk
  20.4 s, median response 0.38 s.
- **Closed the loop**: the sentence went into the wearer's own Bee as a
  reminder (todo 29196370) with its alarm at 15:00 the next day, the hour
  the sentence names. `[template]` means the rules wrote it without a
  model; the Bedrock phrasing is the layer above, behind the same gate.

- **Showed it to the parent**: after `volley connect --name ours`, the
  same command posted the counts (HTTP 200) to the household's own page,
  `/mine`, which reads them back from the API with the household's key
  and marks them `"simulated": false`. The service phrased that day's
  note on Bedrock from the fact `best_hour 15, 66`. Run twice, the
  reminder was written once.

## What it is not

One session, voiced, not a family's day. It shows the product path runs
on live Bee data and agrees with the harness; how close the count is to
the truth is what `harness/beeloop` and `harness/blind` measure.
