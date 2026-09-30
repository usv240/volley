# Evidence

What the science says, what each number is and is not, and the exact
form in which the site is allowed to say it. Every sentence on the site
that carries a number traces to a row here, and a test checks that the
number matches.

## What is measured

A conversational turn is an adult utterance answered by a child within
five seconds, or the reverse. The count per hour and per day is the
quantity used in the studies below, produced by the LENA system from
daylong recordings. Volley counts the same quantity from the Bee's
transcript by the same rule. Whether the two agree is the subject of
the hand-count harness, and until it is measured the site calls the
number an estimate.

## The studies, in the order the site uses them

| Claim on the site | Source | What it showed | What it did not show |
|---|---|---|---|
| Turns at 18 to 24 months explained 14 to 27 percent of the variance in IQ, verbal comprehension and vocabulary at ages 9 to 14, after adjusting for family income | Gilkerson J et al., Language Experience in the Second Year of Life and Language Outcomes in Late Childhood, Pediatrics 2018, PMID 30201624. 146 children, monthly daylong recordings, follow-up a decade later. Three authors work for the LENA Foundation, and the site says so | An association that survived the income adjustment, where adult word counts did not | Causation. The site never says turns cause IQ |
| The brain's language area responded to turns, not to words heard | Romeo RR et al., Beyond the 30-Million-Word Gap, Psychological Science 2018, PMID 29442613. 36 children, 4 to 6, home recordings and fMRI | Turns predicted left inferior frontal activation independent of income, IQ and utterance count | Anything about children under four, or about outcomes |
| Coaching parents raised turns and the children's language | Ferjan Ramirez N, Lytle SR, Kuhl PK, Parent coaching increases conversational turns and advances infant language development, PNAS 2020, PMID 32015127. Randomised, 71 families, 6 to 18 months | An intervention effect on turn-taking and on language at 18 months, correlated | Effect sizes are in the paper, not the abstract; the site quotes the paper when built |
| The gain held to 30 months, and turns at 14 months carried it | Huber E et al., Developmental Science 2023, PMID 36999222 | Vocabulary growth to 30 months greater in the coached group; 14-month turn-taking mediated it | A randomised design in that follow-up alone |
| Each hour of audible television reduced turns by 0.22 SD and child vocalisations by 0.26 SD | Christakis DA et al., Audible television and decreased adult words, infant vocalizations, and conversational turns, Archives of Pediatrics and Adolescent Medicine 2009, PMID 19487612. 329 children, 2 to 48 months | A dose association in home recordings | That a particular family's quiet hour was the television; the site never infers it |
| 40 turns an hour is the published target; below it, each two turns an hour associated with one IQ point | LENA, Every Interaction Counts, citing its Inside Early Talk report | LENA's own summary of its longitudinal data | A study the site can cite directly; the site names it as LENA's figure and links it |
| Serve and return builds brain architecture, and its absence is a threat to development | Harvard University Center on the Developing Child, Serve and Return | The framing the field uses | A number; it is not used for one |

## How good is the automated count

The research instrument's own agreement with human counters is
imperfect and published. The site cites the comparison of automatic and
manual parent-infant turn counts in Child Development (the "word of
caution" paper, doi 10.1111/cdev.13495), which hand-counted turns under
the five-second rule to check the algorithm, and reports our own
harness in the same form: five conversations, a blind human count, the
package's count, and the agreement, whichever way it comes out. If our
agreement is worse than the published one, the site says so and the
number on every screen carries the measured error.

## What the site may say, and may not

May:
- "the studies that found this number", with the studies named
- "associated with", "explained a share of the variance in"
- "LENA's target", "LENA's figure"
- "an estimate, within X of a hand count on our own conversations"

May not:
- "predicts", "improves your child's IQ", "your child is behind"
- any percentile for a child
- "validated on children" for anything measured only on the operator
- "the television" as the reason for any particular hour

A test holds both lists against every public document and the site's
source.

## Numbers measured here, re-derived by tests

- The corpus result, from `harness/childes/results.json`, summarised
  into `apps/web/src/data/corpus.json` by the harness itself; a test
  re-derives the summary and `volley verify` recounts the corpus when
  the zip is present.
- The harness agreement, from `harness/handcount/results.json`, when
  the hand count is done.
- Counts from the device fixture, from `packages/serve-return/tests`.
- The number of tests, the number of friction log entries, the number of
  MCP tools, each counted rather than remembered.

## The corpus result, 2026-09-30

The CHILDES Gleason corpus (Jean Berko Gleason, Boston University, doi
10.21415/T5101R): 24 children aged 2;1 to 5;2 from middle-class Boston
families in the 1970s, each recorded with their mother, with their
father and at the family dinner; transcribed by researchers with
speaker labels; time-aligned by TalkBank's aligner in 2026. Used under
the TalkBank ground rules, never shipped, and cited as they require
(Masur and Gleason, Developmental Psychology 1980, doi
10.1037/0012-1649.16.5.404). Downloaded with the operator's TalkBank
account; the harness at `harness/childes/run.py` reads any corpus in
CHAT format the same way.

What the rule produced, with the corpus's own speaker labels:

- 54 sessions, 26.59 hours, 20,344 turns;
  13 files had no time marks and were
  skipped by name; one file carried diarised labels and no child code
  and was skipped for roles.
- Turns per hour by session: 171.2 to
  1326.1, median 808.3;
  dinner 672.4, with the mother
  710.0, with the father
  892.0. That is twenty times
  the published daylong target of forty, which is what half an hour of
  a parent's full attention looks like; a day's forty is that
  concentration spread thin.
- Children under three: 776.3 an hour
  across 13 sessions; three and over,
  761.3 across
  41. On human transcripts the rule counts
  the youngest at the same rate; whether the Bee transcribes a
  two-year-old is a different question the corpus cannot answer.
- Negative control: 0 turns inside the
  34 stretches of a minute or more in which
  one role spoke alone.
- Baseline, words: adult word count ranks with turns at Spearman
  0.51 across the sessions. One
  mother's play session (2,456 adult words,
  574 turns) and one family dinner
  (2,337 adult words, 159
  turns): the same words, 3.61 times the back-and-forth.
- Baseline, a speaker-change count with no window: 20,486
  against the rule's 20,344; 99.3
  percent of labelled alternations fall within five seconds, and the
  median gap is 0.0 seconds, because the aligner
  hands each utterance's end to the next one's start.
- The window check: a fifty-second window gives
  20,483, a change of under one percent, for the
  same reason.

What this shows: the rule, the role mapping and the alternation logic
hold on human-labelled recordings nobody here made, at the rate a
concentrated session produces. What it does not show: the window,
because contiguous timing gives it nothing to reject; the device's
transcription of young children, because these are human transcripts;
any family's day. Playlogue, the corpus first planned, has segment-level
timing from a forced aligner too, so it would have shown the same
thing; it is gated on Hugging Face behind the same rules, and its
harness is in the repository. The number that answers what the corpus
cannot is the blind hand count on the operator's own Bee, which is Gate
2 and still not measured.

## What nobody has done yet, said on the front page

A child under three on this device; a family other than the operator's;
a comparison of the Bee's turn count with a LENA recorder on the same
afternoon, which is the study we would run first with a grant.

## The case that it serves people beyond this hackathon, in the order a sceptic would ask

Every study below is resolved on PubMed or Crossref in
[citations.json](citations.json), with what it showed and what it did
not; a test asserts nothing is cited in public text that is not there.

**Somebody has already paid for this count, at city scale.** Providence
won the 2013 Bloomberg Philanthropies Mayors Challenge grand prize for
Providence Talks, which put LENA recorders in families' homes with
coaching (Wong, Thomas and Boben, Studies in Educational Evaluation
2020, doi 10.1016/j.stueduc.2019.100818; the programme's own site
claims 55 percent of families raised their daily adult word count).
LENA Start, the same instrument in a community parent-education
programme, produced significant between-group gains in conversational
turns and child vocalisations, though not in adult words, in a
nonequivalent-groups evaluation (Elmquist et al., Journal of Child
Language 2021, PMID 32921333). The demand is proven; the barrier is
that the instrument is a programme, not a purchase.

**It is coachable, in randomised trials, in the age range Volley
serves.** Beyond the infant trials the front page cites (Ferjan Ramirez
2020, Huber 2023), a nine-week family intervention with 52 children
aged 4 to 6 raised turns, the change in turns mediated the gains in
language and executive function, and across the sample the change in
turns correlated with cortical thickening in language regions (Romeo et
al., Developmental Cognitive Neuroscience 2021, PMID 34052580). An
eight-visit home programme raised turns during the visits and the gain
faded afterwards (Suskind et al., Journal of Child Language 2016, PMID
26041013; the full Thirty Million Words curriculum was then tested in a
randomised trial measured with the same recorder, Leung, Hernandez and
Suskind, Early Childhood Research Quarterly 2020, doi
10.1016/j.ecresq.2018.12.005), which is the argument for a count that
is there every day rather than a course that ends.

**The number is about more than words.** Turns at 18 months predicted
socioemotional competence at 30 months, controlling for warmth, risk
and the child's own vocalisations, with the direction running from turns
to competence (Gomez and Strasser, Developmental Science 2021, PMID
33825290). Turns, independent of income and of how much adults spoke,
related to white matter connectivity in the left arcuate fasciculus
near Broca's area, and no other tract (Romeo et al., Journal of
Neuroscience 2018, PMID 30104336).

**Volley does not rest on the word gap.** The thirty-million-word
figure did not replicate as stated (Sperry, Sperry and Miller, Child
Development 2019, PMID 29707767); the reply holds that responsive,
child-directed talk is what the evidence supports whatever the gap's
size (Golinkoff et al., Child Development 2019, PMID 30102419). Turns
are the measure that survived the income adjustment in Gilkerson 2018
when words did not, which is why Volley counts them and not words.

**The phone is the mechanism the quietest hour points at.** When a
mother's teaching of a new word was interrupted by a phone call, the
two-year-old did not learn it, though the word was said as often (Reed,
Hirsh-Pasek and Golinkoff, Developmental Psychology 2017, PMID
28650177). Of 55 caregivers observed at meals with young children, 40
used a device, and the depth of absorption shaped how the child's bids
were met (Radesky et al., Pediatrics 2014, PMID 24616357). Volley
cannot see a phone or a television; it shows the hour, and the site
says the rest is the parent's to notice.

**The research instrument's own turn count is imperfect, which is why
Volley publishes its agreement rather than assuming it.** Against
manual annotation in three populations, LENA's adult word and child
vocalisation counts were reasonably accurate and its conversational
turn count was "more problematic" (Cristia et al., Behavior Research
Methods 2020, PMID 32728916); an automatic count and a hand count under
the five-second rule disagreed enough to earn "a word of caution"
(Ferjan Ramirez, Hippe and Kuhl, Child Development 2021, doi
10.1111/cdev.13495). An open count with its hand-count agreement on the
front page is not a step down from a gold standard; there is no gold
standard, and the front page says what this one's error is once it is
measured.

**The scale of the need, and who is asked to act on it.** At school
entry, 9.92 percent of children in a population study had a language
disorder, 7.58 percent of them with no known cause, and 88 percent of
those children did not make expected academic progress (Norbury et al.,
Journal of Child Psychology and Psychiatry 2016, PMID 27184709). The
American Academy of Pediatrics asks paediatricians to promote talking
and reading with young children at well visits from infancy (Council on
Early Childhood, Pediatrics 2014, PMID 24962987) and names serve-and-
return relationships as the thing paediatric care should protect
(Garner and Yogman, Pediatrics 2021, PMID 34312296). Neither policy
names an instrument a parent can bring to the visit, because none has
been sold to one. Volley is not a screen for language disorder and the
site says so; it is the count a parent could bring.

**What changes at fifty dollars on the wrist.** The Bee Pioneer Edition
lists at 49.99 dollars and ships only to the United States on the day
this was written; Bee also runs on an Apple Watch. The research
instrument is sold to programmes and researchers. The difference is not
a better count; it is the first count a parent can own, on a device
that is already worn for other reasons, with the words never leaving
their computer.

**What this section does not claim.** That Volley has changed any
child's outcome; that its count equals LENA's; that a parent should aim
for any number. One family has worn it. The first study to run with a
grant is the Bee against a LENA recorder on the same afternoon.
