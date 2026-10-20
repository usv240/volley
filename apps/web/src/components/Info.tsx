"use client";

import { useId, useState } from "react";

/**
 * A small (i) beside a term a newcomer will not know.
 *
 * Not hover-only. Many of the people this page is for are on a phone,
 * and some of the rest use a keyboard, so the explanation opens on
 * click, on Enter, and on focus, and closes on Escape. It is a real
 * button with a real label rather than a title attribute, because title
 * attributes are invisible to touch and to screen readers.
 *
 * The explanation is written once, here, so the same term reads the same
 * everywhere it appears. Every entry with a number names its source.
 */

export const TERMS = {
  turn: {
    label: "a turn",
    text: "One back-and-forth: you say something and your child answers within five seconds, or the other way round. The studies that found this number counted exactly this, using a research recorder called LENA. Volley counts it from your Bee's transcript by the same rule.",
  },
  exchange: {
    label: "serve and return",
    text: "Harvard's Center on the Developing Child's name for the back-and-forth between a child and a caring adult, like a game of tennis. It is the interaction they say builds brain architecture, and whose absence they call a threat to development.",
  },
  countsNotWords: {
    label: "why counts and not words",
    text: "In the Pediatrics 2018 study, the number of turns at 18 to 24 months explained 14 to 27 percent of the variance in IQ and vocabulary a decade later after adjusting for family income; the number of words heard was much weaker after the same adjustment. In the 2018 fMRI study, turns and not words predicted activity in the brain's language area.",
  },
  fiveSeconds: {
    label: "the five-second rule",
    text: "A reply counts as a turn if it starts within five seconds of the other person finishing. That window is the published one; a test in the code pins it, and a deliberately wrong window makes the count change, so it cannot be silently ignored.",
  },
  bee: {
    label: "Bee",
    text: "A wristband from Amazon that transcribes the day for the person wearing it, with speaker labels. It stores no audio. Volley reads its transcript on your computer through Bee's own command line tool and never sends it anywhere.",
  },
  onYourComputer: {
    label: "on your computer",
    text: "The counting runs in a program on your laptop, or in this browser tab if you drop an export here. The words are read there, counted, and gone. Only the counts, integers by the hour, are ever sent, and only if you set that up.",
  },
  whatLeaves: {
    label: "what leaves",
    text: "Per hour: turns, who started each exchange, how quickly you replied, how many questions you asked, the longest exchange, seconds spoken, and how many words were read and thrown away. There is no field in the counts that can hold a word, and the privacy section shows a transcript being refused by the server.",
  },
  serve: {
    label: "serve",
    text: "Who started an exchange. The coaching trial found that adults responding to the child, rather than only talking, is the part that moved language; so the count keeps track of who served and how fast the reply came.",
  },
  latency: {
    label: "reply time",
    text: "How long, typically, between your child finishing and you answering. Shorter is the coachable thing; a reply within a breath keeps the exchange alive even if it is one word.",
  },
  question: {
    label: "a question",
    text: "A parent utterance that asks something, counted by its shape: it ends in a question mark or starts with a question word. Questions are the one habit that reliably produces a return, which is why the day view counts them.",
  },
  bestHour: {
    label: "best hour",
    text: "The hour of the day with the most turns. The note names it so a parent keeps what already works rather than being told to do more.",
  },
  away: {
    label: "away",
    text: "An hour in which no child speech was heard. Shown as away rather than zero, because zero would read as a failure and it is usually a nap or a nursery.",
  },
  target: {
    label: "forty an hour",
    text: "LENA's published target from its Inside Early Talk report, stated here as their figure: at least forty turns an hour, and below that each two turns an hour associated with one IQ point in their longitudinal data. Volley does not set a target of its own.",
  },
  noPercentile: {
    label: "no percentile",
    text: "Volley never shows where a child sits against other children. The only comparison is with the same family's own days and the one published target. A count is not a test.",
  },
  ses: {
    label: "adjusted for income",
    text: "The studies compared families with different incomes, and richer families talk more in some ways. Turn counts kept their predictive power after that was taken into account; word counts did not. This is why Volley counts turns.",
  },
  lena: {
    label: "LENA",
    text: "The research instrument behind the studies: a recorder in a vest on the child, audio uploaded to LENA's cloud, reports of adult words and conversational turns, 250 peer-reviewed studies. Sold to programmes, clinics and researchers, not to parents. A registered mark of the LENA Foundation; Volley is not affiliated and implements the published definition.",
  },
  developerMode: {
    label: "Developer Mode",
    text: "In the Bee app, tap the version number five times under Settings. It unlocks the command line tool that Volley reads through. Nothing about this changes what Bee itself records.",
  },
  apiKey: {
    label: "an API key",
    text: "A secret shown once when you create a household. It lets your computer post counts and lets you read them back. Only its hash is stored, so nobody at Volley can read your counts without it.",
  },
  mine: {
    label: "this page",
    text: "It reads your household's counts from the service with your key, straight from your browser. The key arrived in the link volley connect printed, in the part after the # that a browser never sends to any server, and it now lives only in this browser's local storage. Forget it here and the page shows nothing.",
  },
  household: {
    label: "a household",
    text: "A name you chose and, if you want, your child's first name or a nickname so the note can address them. Nothing else. Delete it in one request and every count goes with it.",
  },
  mcp: {
    label: "MCP server",
    text: "The way an assistant like Alexa+ talks to Volley: seven tools, one of which returns no data by design. It can say how the talking went and what to try tomorrow; it cannot return a word of speech, because the server never has one, and a test walks every tool to prove it.",
  },
  skill: {
    label: "Agent Skill",
    text: "A short document that teaches an assistant what Volley's numbers mean, what it must never say, and that there is no transcript to ask for. Pinned to the server's tools by a test.",
  },
  bedrock: {
    label: "the note's two layers",
    text: "Rules pick the fact from the counts; Claude on Amazon Bedrock phrases it. Every digit in the sentence must come from the fact and no forbidden word may appear, or a plain template is used instead and the page says which layer wrote it.",
  },
  harness: {
    label: "the hand count",
    text: "Five of the operator's own conversations counted blind by a person from the Bee app's transcript view, against the program's count. Reported whichever way it comes out, next to the published agreement for the research instrument.",
  },
  corpus: {
    label: "the public corpus",
    text: "The CHILDES Gleason corpus: 24 children aged 2;1 to 5;2 recorded in the 1970s with their mother, with their father and at dinner, transcribed by researchers with speaker labels and time-aligned in 2026 by TalkBank's aligner. Fifty-four sessions, 26.59 hours. Volley ran the rule over it with the corpus's own labels on 2026-09-30 and published every number it produced; the corpus is never shipped and is cited as the TalkBank rules require.",
  },
  windowOnCorpus: {
    label: "why the window barely shows here",
    text: "The corpus's timing comes from a forced aligner, which hands each utterance's end to the next one's start, so the gap between a question and its answer is usually zero by construction. On such timing the five-second rule and a bare speaker-change count agree on 99.3 percent of alternations, and a fifty-second window changes the count by under one percent. The window's work is in a day with real silences, which the Bee's timing has and this corpus does not.",
  },
  wordsVsTurns: {
    label: "words against turns",
    text: "Adult word count is what the last consumer device sold and what the studies found stops predicting once income is accounted for. On the corpus the two rank together only moderately (Spearman 0.51 across 54 sessions), and one mother's play session and one family dinner with the same number of adult words, about 2,400, carried 574 and 159 turns. Same words; three and a half times the back-and-forth.",
  },
  validated: {
    label: "validated",
    text: "The word is used here only for the published instrument and its studies. Volley's own count is checked against a public corpus, and on the operator's own Bee against a real corpus conversation played to it, both on this page. No person has hand-counted a day, because no real people are part of this entry. It has not been validated on children other than the corpus's, and the page says so.",
  },
  paidFor: {
    label: "already paid for",
    text: "Providence won the 2013 Bloomberg Philanthropies Mayors Challenge grand prize for Providence Talks, which put LENA recorders in families' homes with coaching; the programme's own site says 55 percent of families raised their daily adult word count (Wong, Thomas and Boben, Studies in Educational Evaluation 2020, doi 10.1016/j.stueduc.2019.100818). LENA Start, the same instrument in a community class, produced significant gains in turns and child vocalisations but not adult words, in a nonequivalent-groups evaluation (Elmquist et al., Journal of Child Language 2021, PMID 32921333).",
  },
  coachable: {
    label: "coachable at this age",
    text: "A nine-week family intervention with 52 children aged 4 to 6, randomised against no contact, raised turns; the change in turns mediated gains in language and executive function, and correlated with cortical thickening in language regions (Romeo et al., Developmental Cognitive Neuroscience 2021, PMID 34052580). Eight home visits raised turns while they lasted and the gain faded after (Suskind et al., Journal of Child Language 2016, PMID 26041013), which is the case for a daily count over a course that ends.",
  },
  moreThanWords: {
    label: "more than language",
    text: "Turns at 18 months predicted socioemotional competence at 30 months, controlling for warmth, social risk and the child's own vocalisations, and the direction ran from turns to competence (Gomez and Strasser, Developmental Science 2021, PMID 33825290). Turns, independent of income and of how much adults spoke, related to white matter connectivity near Broca's area and to no other tract (Romeo et al., Journal of Neuroscience 2018, PMID 30104336).",
  },
  wordGap: {
    label: "the word gap",
    text: "The thirty-million-word figure did not replicate as stated (Sperry, Sperry and Miller, Child Development 2019, PMID 29707767); the reply holds that responsive, child-directed talk is what the evidence supports whatever the gap's size (Golinkoff et al., Child Development 2019, PMID 30102419). Volley does not rest on the gap. It counts turns because turns survived the income adjustment in Gilkerson 2018 when words did not.",
  },
  phone: {
    label: "the phone",
    text: "When a mother's teaching of a new word was interrupted by a phone call, her two-year-old did not learn it, though the word was said as often (Reed, Hirsh-Pasek and Golinkoff, Developmental Psychology 2017, PMID 28650177). Of 55 caregivers observed at meals with young children, 40 used a device (Radesky et al., Pediatrics 2014, PMID 24616357). Volley cannot see a phone; it shows the hour, and what was happening in it is yours to notice.",
  },
  imperfectInstrument: {
    label: "the instrument's own error",
    text: "Against manual annotation in three populations, the research recorder's word and child-vocalisation counts were reasonably accurate and its conversational turn count was, in the authors' words, more problematic (Cristia et al., Behavior Research Methods 2020, PMID 32728916); an automatic and a hand count under the five-second rule disagreed enough to earn a word of caution (Ferjan Ramirez, Hippe and Kuhl, Child Development 2021, doi 10.1111/cdev.13495). There is no gold standard. That is why this page publishes its own agreement rather than assuming it.",
  },
  scale: {
    label: "the scale",
    text: "In a population study of 7,267 children screened at school entry in England, 9.92 percent had a language disorder, 7.58 percent with no known cause, and 88 percent of them did not make expected academic progress (Norbury et al., Journal of Child Psychology and Psychiatry 2016, PMID 27184709). Volley is not a screen for any of this and never says a child is behind; it is the count a parent could bring to the visit where that conversation happens.",
  },
  wellVisit: {
    label: "the well visit",
    text: "The American Academy of Pediatrics asks paediatricians to promote talking and reading with young children at well visits from infancy (Council on Early Childhood, Pediatrics 2014, PMID 24962987) and names serve-and-return relationships as what paediatric care should protect (Garner and Yogman, Pediatrics 2021, PMID 34312296). Neither policy names an instrument a parent can bring, because none has been sold to one.",
  },
  fiftyDollars: {
    label: "fifty dollars",
    text: "The Bee Pioneer Edition listed at 49.99 dollars on 2026-09-30 and ships only to the United States; Bee also runs on an Apple Watch. The research recorder is sold to programmes and researchers. The difference Volley makes is not a better count; it is the first count a parent can own, on a device already worn for other reasons, with the words never leaving their computer.",
  },
  playlogueLicence: {
    label: "CC BY-NC-SA",
    text: "TalkBank shares its corpora under CC BY-NC-SA 3.0 and its ground rules, which forbid putting the data into a product or a model and allow using it to develop and evaluate algorithms. Volley does the allowed thing only: the transcripts evaluate the counter on the operator's machine, are never shipped, uploaded or trained on, and what reaches this page is the counts. The rules ask for three citations: the corpus's own reference, its DOI with the year retrieved, and MacWhinney (2000) for CHILDES with its NICHD grant; all three are in the list.",
  },
} as const;

export type Term = keyof typeof TERMS;

export function Info({ term }: { term: Term }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const { label, text } = TERMS[term];

  return (
    <span className="relative inline-block align-baseline">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false);
        }}
        aria-expanded={open}
        aria-controls={id}
        aria-label={`What does ${label} mean`}
        className="info-btn"
      >
        i
      </button>
      {open && (
        <span id={id} role="note" className="info-pop card-lift" onClick={() => setOpen(false)}>
          <strong className="block text-ink">{label}</strong>
          <span className="mt-1 block text-sm leading-relaxed text-muted">{text}</span>
        </span>
      )}
    </span>
  );
}
