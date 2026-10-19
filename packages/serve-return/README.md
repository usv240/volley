# serve-return

Count adult-child conversational turns from any speaker-labelled
transcript, by the published five-second rule, and keep no words.

```
pip install "git+https://github.com/usv240/volley#subdirectory=packages/serve-return"
```

No speaker labels? `serve_return.blind` reads who is the child and who the
adult from the transcript itself, with a model trained on the CHILDES
Gleason corpus and shipped in the package. On families it never saw, the
day's turn count came within 9.6 percent of the true count in the median
session (harness/blind in the repository).

```python
from serve_return.blind import relabel
day = count_day(relabel(unlabelled_utterances), Roles.of(adult=["adult"], child=["child"]))
```

```python
from serve_return import Utterance, Roles, count_day

roles = Roles.of(adult=["Ujwal"], child=["Unknown"])
day = count_day([
    Utterance(start=1790714507.0, speaker="Ujwal", text="What did you build today?"),
    Utterance(start=1790714509.5, speaker="Unknown", text="A tower. It fell."),
    Utterance(start=1790714511.0, speaker="Ujwal", text="How tall was it?"),
], roles)

day.turns              # 2
day.questions_adult    # 2
day.words_discarded    # 13
day.to_dict()          # numbers only; nothing here can hold a word
```

A turn is one alternation between an adult and a child within five
seconds: an adult utterance answered by a child within five seconds of
its end, or the reverse. Same-role runs merge first. This is the
conversational turn count the developmental studies used (Gilkerson et
al., Pediatrics 2018; Romeo et al., Psychological Science 2018), as
produced by the LENA system and as hand-counted under "the 5-second
pause rule" in the manual comparison in Child Development (doi
10.1111/cdev.13495). LENA is a registered mark of the LENA Foundation;
this package implements the published definition and is not affiliated.

What comes out, per hour and per day: turns, who served, responses
within the window, median reply time, adult questions, the longest
exchange, seconds spoken by each role, utterance counts, and the number
of words read and discarded. The only text field in the output is a
date.

Labels are yours: a Bee wristband labels the wearer one way and other
voices another; CHILDES uses MOT, FAT, CHI. Anything you do not map is
ignored, which is what a third adult in the room should be.

MIT. Part of Volley, built for the Build, Ship, Shape: Amazon Developer
Hackathon.
