# Friction log

Each entry: the task, the steps, what was expected against what
happened, a severity, the workaround, and an actionable suggestion.
Entries are dated. Two are about the Bee; one is about us.

## Entry 1: the Bee labels every speaker "Unknown" until the wearer's voice is trained, and nothing says so (2026-09-29)

- Task: count turns between the wearer and another person, which needs at least "the wearer" apart from "not the wearer".
- Steps: bee-cli 0.7.3, three conversations recorded on the day the device arrived, read with `bee conversations get --json`, realtime and post-processed transcriptions alike.
- Expected: speaker labels, which the readme promises ("Conversation transcripts with speaker identification") and whose stream events carry `speaker: speaker_1`.
- Actual: every one of 177 utterances across three conversations was labelled "Unknown". Nothing in the CLI, its readme, or the developer docs says that labels depend on a voice-training step in the phone app, or that "Unknown" is the label before it. The answer was found in a user forum.
- Severity: high for this product, because without labels there is no count, and the failure is silent: the transcript looks complete.
- Workaround: train the voice in the app, then hold one conversation and read the labels before anything else is built; it is Gate 1 in the plan, and the site says the count depends on the device's labels.
- Suggestion: return a machine-readable reason with the label ("Unknown: no voice profile enrolled") and put the voice-training step in the CLI's first-run text, where a developer will see it before spending a day on a parser.

## Entry 2: the CLI's real response shapes differ from its readme in three ways, and the first returns nothing (2026-09-29, carried from Bellwether)

- Task: read a conversation's utterances with times.
- Steps: `bee conversations list --json`, then `get`, then `now` and `changed`.
- Expected: what the readme describes.
- Actual: `list` carries an `utterances_count` and no utterances, so a parser fed the list reduces a full afternoon to zero with no error; `get` wraps its record in `{"conversation": ..., "timezone": ...}` where `now` and `changed` return bare records; each utterance carries `spoken_at` and `created_at` in epoch milliseconds beside `start` and `end` in seconds into the conversation, which a time parser reads as 1970.
- Severity: high for anyone building on the CLI; low for us, because the sibling project's first session found it and the shapes are pinned in tests here too.
- Workaround: fetch rows without utterances one by one with `get`, unwrap, read `spoken_at` first, never read an integer too small to be an instant as one. The `end` offset is what makes the five-second rule measurable from the end of an utterance, which is the published definition; it is the one thing the Bee gives that a `sync` export does not.
- Suggestion: one example response per command in the readme, with its wrapper, and the unit of every time field.

## Entry 3: a `bee sync` export has no times, so the browser drop zone can only estimate (2026-09-29, ours as much as theirs)

- Task: let a visitor count a day from an export without running anything.
- Steps: read the markdown `bee sync` writes: "### Transcription" then "- Speaker 1: ..." lines.
- Expected: something to anchor the five-second rule to.
- Actual: no timestamps in the export. The drop zone spaces utterances at an average speaking rate and says the count is an estimate; the command on the parent's machine uses the Bee's real times.
- Severity: low. The honest path exists and the estimate is labelled.
- Workaround: as above.
- Suggestion: a `--with-times` flag on `bee sync`, or `spoken_at` in the markdown front matter per utterance.

<!-- Add new entries above this line as they happen. -->

## Entry 4: the phone app offers no way to name a speaker, so "Unknown" cannot be corrected by the user (2026-09-30)

- Steps: with every utterance labelled "Unknown" for two days (entry 1), open conversations in the Bee app on the phone, open a transcript, look for any way to name a speaker or mark a line as the wearer; look under Settings for voice training, voice ID or speaker recognition.
- Expected: something like "This is me" on a transcript line, or a voice enrolment step, since the CLI readme promises transcripts "with speaker identification" and stream events carry `speaker: speaker_1`.
- Actual: nothing to tap. Transcript lines are read-only; Settings has no voice item. The label is decided server-side and the user has no lever. A 270-utterance conversation on 2026-09-30 was still entirely "Unknown".
- Cost: every feature that needs to know who spoke (Volley's whole count; Bellwether's "the wearer's own speech") cannot run on real data; the developer can only wait.
- Workaround: none in the product. Volley's fallback is a labelled two-adult conversation if labels ever split, or a demonstration that says on camera the device gave one label.
- Suggestion: a "This is me" action on any transcript line that enrols the wearer's voice, and a documented statement of when speaker labels are produced at all.

## Entry 5: three weeks on, every speaker is still "Unknown", so Volley stopped waiting for labels (2026-10-19)

- Task: count a day of parent-child turns from the Bee, the whole product.
- Steps: read every utterance in the last 25 sessions on the account (`bee conversations list`, then `get`) and tallied the `speaker` field.
- Expected: by now, at least two labels in a conversation with two voices, since the readme promises transcripts "with speaker identification".
- Actual: 1,004 of 1,004 utterances labelled "Unknown", including sessions with two adult voices and a session where a synthetic voice and the wearer alternated. The device also decides utterance boundaries by pause, and on 2026-10-19 it merged three consecutive lines from one voice into one utterance; how often it merges two voices was then measured on the device (harness/beeloop): a 190-second CHILDES mother-child conversation voiced by Polly kept 75 of 75 turns in the Bee's own segmentation. Reading that session also found a bug of ours: `start_time` was 33 seconds after the audio began, and start (from `spoken_at`) and end (from `start_time` plus the offset) came from different clocks; both now come from the offsets, anchored once on `spoken_at`, with a regression test.
- Severity: critical for any count of who-talked-to-whom on this device.
- Workaround: read the roles from the transcript. `serve_return.blind` is an averaged perceptron over each utterance's words, its neighbours' words and the pauses either side, trained on the CHILDES Gleason corpus. Scored only on families it never saw (six folds by child): 73.7 percent of 42,004 utterances get the right role, the day's turn count lands within 9.6 percent of the true count in the median session once a scale learned on other families corrects its steady undercount, turns per hour track the truth at a correlation of 0.874, and the naive alternative (every pause is a change of speaker) misses 87.3 percent of turns. `volley setup --blind` uses it; harness/blind/results.json has every session.
- Suggestion: carry the enrolled voice through as `speaker: "wearer"` or an `is_wearer` boolean, and split utterances at a change of voice even when no label is assigned. Either would make this workaround unnecessary. Feature requests 1 and 2.
