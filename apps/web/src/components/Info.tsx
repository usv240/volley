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
    text: "Playlogue: 33 hours of adult-child play recorded by researchers, drawn from CHILDES, with human speaker labels and timing. Used to check the count against recordings nobody here made; never shipped, cited as its licence requires.",
  },
  validated: {
    label: "validated",
    text: "The word is used here only for the published instrument and its studies. Volley's own count is checked against a hand count and against a public corpus, and the results are on this page. It has not been validated on children other than the corpus's, and the page says so.",
  },
  playlogueLicence: {
    label: "CC BY-NC-SA",
    text: "The corpus is shared for non-commercial use with attribution under the TalkBank ground rules. Volley uses it as evidence about the counter, not as a part of the product, and cites TalkBank as required.",
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
