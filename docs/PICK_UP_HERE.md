# Pick up here: Volley

Written 2026-09-30, after the Bee app was checked for a way to name
speakers and had none (friction log entry 4).

## Where things stand

- Repository: main at `b36d084`, CI green, 103 Python tests + 7 web.
- Site: https://da78ygi6ol1oi.cloudfront.net (and `/mine/`); API and
  MCP at https://6gm5fp5kuipgvjgr5zmhghq63u0hmmvd.lambda-url.us-east-1.on.aws.
- Measured: the CHILDES Gleason corpus (Gate 2b), on the hero and the
  evidence section; every citation resolved in `docs/citations.json`.
- Built and tested but never run on a real day: `volley today`, the
  reminder into the Bee, the Mine page with the operator's own counts,
  the two terminal beats of the video, the hand count (Gate 2), the
  device negative controls, the two Strands agents on a real household.
- Video: `video/build/volley-demo-captioned.mp4`, 1:52, web beats only.
  Does not yet satisfy the Bee track rule (live Bee data on camera).

## The blocker

Every utterance the Bee produces for this account is labelled
"Unknown". The phone app has no way to name a speaker or enrol a voice.
Checked 2026-09-29 (177 utterances) and 2026-09-30 (270 utterances).
Nothing in the CLI, the docs or the app changes it.

## What to check, each day, in one command

    cd volley && MSYS_NO_PATHCONV=1 cmd /c "bee conversations list --limit 3 --json"

then `bee conversations get <id> --json` on the newest and look at
`transcriptions[0].utterances[*].speaker`. The moment any value is not
"Unknown", the label split and the rest is below.

## When labels split

1. `volley setup --parent <label for Ujwal> --child <label for the other person> --child-name <name> --tz 5.5 --reminders yes`
2. `volley connect`, then `volley today --now`; open the link it prints.
3. `cd video && python record_term.py capture`, then `render`, then
   `assemble.py` and `subtitle.py`; check stills at the two terminal
   beats; the video is now the Bee track's proof.
4. Gate 2: five conversations hand-counted blind from the app's
   transcript view against `serve-return`; commit
   `harness/handcount/results.json`; the hero's second number fills.
5. Negative controls on the device: a twenty-minute podcast to an empty
   room, twenty minutes of silence, one adult-only conversation; commit
   the counts (all should be zero).
6. `volley-agent coach "how was our talking today"` on the real
   household; paste the answer into `docs/AGENT.md`.

## If labels never split

By 2026-10-16, record the fallback: a labelled conversation is not
available, so the video shows `volley today` on the real transcript
with both people under one label, the count refusing (zero turns, one
role), and the CHAT harness on the public corpus as the count working.
The site's hero already says the hand count is not yet measured; the
submission says why in one sentence and cites friction entry 4. This is
honest and weaker; it is the last resort, not the plan.

## Independent of the blocker

- A PyPI token from the operator publishes `serve-return` and
  `volley-bee`; the site's install step names them now.
- One practitioner's sentence by 2026-10-10 (SLP, paediatrician,
  preschool teacher); it goes on the evidence section's third card.
- Flip the repository public at submission; set topics; tag v0.1.0.
