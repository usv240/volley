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

- The harness agreement, from `harness/handcount/results.json`.
- Counts from the device fixture, from `packages/serve-return/tests`.
- The number of tests, the number of friction log entries, the number of
  MCP tools, each counted rather than remembered.

## What nobody has done yet, said on the front page

A child under three on this device; a family other than the operator's;
a comparison of the Bee's turn count with a LENA recorder on the same
afternoon, which is the study we would run first with a grant.
