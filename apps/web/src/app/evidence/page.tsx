import type { Metadata } from "next";
import Link from "next/link";
import demo from "../../data/demo.json";
import tuesdaySim from "../../data/tuesday-sim.json";
import { Footer, REPO } from "../../components/Footer";
import { Info } from "../../components/Info";
import { Nav } from "../../components/Nav";

export const metadata: Metadata = {
  title: "Volley: the evidence",
  description:
    "The two agents that may only say what a tool returned, the programmes that already pay for this count, and every test you can run.",
};

/**
 * What sits behind the home page, for the reader who checks: the agents,
 * the case for who this serves, and the commands that rerun every test.
 * Moved here intact so the home page reads in one pass for a parent; the
 * sections keep their ids, so /evidence/#agents and the rest still land.
 */

// The simulated household's latest day, which every "today" in the runs below means.
const LATEST = demo.days[demo.days.length - 1].date;
const RUN_DATE = "2026-09-30";

// The Coach is quoted from docs/AGENT.md, "Two real runs, 2026-09-30", word for word.
// Tuesday is read from its run record, apps/agent/runs/tuesday-sim.json, copied to src/data.
const AGENTS = [
  {
    name: "The Coach",
    body: "Answers a parent the way Alexa+ would, over Volley's seven MCP tools; the model never sees the household's key. It is also deployed on Amazon Bedrock AgentCore Runtime, so Alexa+, a scheduled job or another agent can invoke it.",
    command: 'volley-agent coach --demo "how was our talking today, and what should I try tomorrow?"',
    answer:
      "You and your little one had 157 turns today, your liveliest stretch was at six in the evening, and the quietest time when your child was around was at four in the afternoon. Tomorrow, try leaning into that six o'clock window, that's when the two of you are most in tune, with 38 turns in that hour alone. See if you can bring a little of that same energy to four o'clock too!",
    tools: "model; tools: how_was_our_talking_today, one_thing_for_tomorrow",
    asked: `Asked on ${RUN_DATE} about the simulated day dated ${LATEST}; "today" in the answer means ${LATEST}, not the day you read it.`,
    caption: `A real run, Sonnet on the first rung, against the deployed server, on the simulated household.`,
  },
  {
    name: "Tuesday",
    body: "Why was Tuesday quiet is a question the counts cannot answer and the parent's own Bee can. Tuesday holds Bee's own MCP server beside Volley's, behind a four-tool allow-list: the daily summaries, a list of them, the to-do list and creating one to-do. The transcript, search, photo and location tools are never offered, and neither server is told the other exists.",
    command: tuesdaySim.command,
    answer: tuesdaySim.answer,
    tools: `${tuesdaySim.layer}; tools: ${tuesdaySim.tools_called.join(", ")}`,
    asked: `Simulated Bee, simulated household, ${tuesdaySim.date.slice(0, 10)}: a stand-in Bee server with synthetic days written for the simulated family, asked about the week ending ${LATEST}.`,
    caption: `Read word for word from the run's record. An earlier real run on ${RUN_DATE} found no Bee summary for that day, and the agent said so rather than inventing one.`,
  },
];

const IMPACT = [
  {
    title: "Somebody has already paid for it, at city scale",
    term: "paidFor" as const,
    body: "Providence won a Bloomberg Philanthropies grand prize to put the research recorder in families' homes with coaching, and community classes built on the same instrument raised turns in an evaluation. The demand is proven. The barrier is that the instrument is a programme, not a purchase.",
  },
  {
    title: "It is coachable, in randomised trials, at this age",
    term: "coachable" as const,
    body: "A nine-week family intervention with four-to-six-year-olds raised turns, and the change in turns carried the gains in language. Home-visit gains faded when the visits ended, which is the argument for a count that is there every day rather than a course.",
  },
  {
    title: "The number is about more than words",
    term: "moreThanWords" as const,
    body: "Turns at 18 months predicted how children handled feelings a year later, with the direction running from turns outward; and turns, not the amount adults spoke, related to the wiring of the brain's language pathway.",
  },
  {
    title: "It does not rest on the word gap",
    term: "wordGap" as const,
    body: "The thirty-million-word figure did not replicate as stated, and the field's reply was that responsive talk is what matters. Volley counts turns because turns kept predicting outcomes after income was accounted for, when words did not.",
  },
  {
    title: "The quietest hour usually has a phone in it",
    term: "phone" as const,
    body: "One interrupted phone call was enough to stop a two-year-old learning a word said just as often. Volley cannot see the phone. It shows the hour, and the note names the quietest one with your child present, which is the only nudge it makes.",
  },
  {
    title: "The research instrument's own turn count is imperfect",
    term: "imperfectInstrument" as const,
    body: "A thorough evaluation found its turn count more problematic than its word count, and a comparison with hand counts earned a word of caution. There is no gold standard, which is why this page will print its own agreement rather than assume it.",
  },
  {
    title: "The scale, and who is asked to act on it",
    term: "scale" as const,
    body: "About one child in ten arrives at school with a language disorder, most with no known cause, and nearly nine in ten of them fall behind. Paediatricians are asked to promote talk at every well visit and have no instrument a parent can bring. Volley is not a screen; it is the count a parent could bring.",
  },
  {
    title: "What changes at fifty dollars on the wrist",
    term: "fiftyDollars" as const,
    body: "The Bee costs about fifty dollars and is already worn for other reasons. The difference is not a better count; it is the first one a parent can own, on their own computer, with the words never leaving it.",
  },
];

export default function EvidencePage() {
  return (
    <>
      <a href="#top" className="skip-link">
        Skip to content
      </a>
      <Nav />

      <main id="top" className="mx-auto max-w-[1120px] px-5 pb-28 sm:px-8">
        <header className="pt-8 sm:pt-12 lg:pt-14">
          <h1 className="display max-w-[20ch] text-[2.25rem] leading-[1.06] text-ink sm:text-5xl sm:leading-[1.04]">
            The agents, who already pays for this count, and every test.
          </h1>
          <p className="mt-5 max-w-[62ch] leading-relaxed text-muted">
            The parts a sceptic or a developer checks, kept off the home page so a parent can read it in one pass. The measured
            results, what it refused to count and how close it is to a person, stay on{" "}
            <Link prefetch={false} href="/#evidence" className="text-[var(--accent)] underline underline-offset-4">
              the home page
            </Link>
            .
          </p>
        </header>

        <div className="rule my-12 sm:my-20" />

        {/* The agents: two clients of the same MCP server, held to the numbers a tool returned. */}
        <section id="agents" className="scroll-mt-24">
          <h2 className="display-sm max-w-[24ch] text-3xl text-ink sm:text-4xl">Two agents that may only say what a tool returned.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            Both are built on the Strands Agents SDK, phrase with Claude on Amazon Bedrock, and reach Volley only through the MCP server
            Alexa+ would use. Every number in an answer must have come back from a tool, and the words the coach never uses (delay,
            behind, risk, deficit, disorder, diagnosis, percentile, IQ) may not appear. A refused answer goes back once with the
            violation named; a second refusal is replaced by the tool results read out plainly.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            {AGENTS.map((a) => (
              <figure key={a.name} className="card flex min-w-0 flex-col p-6">
                <p className="font-semibold text-ink">{a.name}</p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{a.body}</p>
                <AgentRun a={a} />
              </figure>
            ))}
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* Impact: who has paid for this count already, and what changes at fifty dollars. */}
        <section id="impact" className="scroll-mt-24">
          <h2 className="display-sm max-w-[24ch] text-3xl text-ink sm:text-4xl">Cities have paid for this count. Parents have never been able to buy it.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            The case for who this serves, in the order a sceptic would ask it, with the study behind every sentence on its i. What
            it does not claim is at the end, in the same type.
          </p>
          <div className="mt-10 hidden gap-6 md:grid md:grid-cols-2">
            {IMPACT.map((c) => (
              <div key={c.title} className="card min-w-0 p-6">
                <p className="font-semibold text-ink">
                  {c.title} <Info term={c.term} />
                </p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{c.body}</p>
              </div>
            ))}
          </div>
          {/* A phone reads the eight claims as a list and opens the one it doubts. */}
          <div className="fold-list mt-8 border-y border-line md:hidden">
            {IMPACT.map((c) => (
              <details key={c.title} className="fold">
                <summary>
                  {c.title}
                  <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </summary>
                <p className="pb-5 text-sm leading-relaxed text-muted">
                  {c.body} <Info term={c.term} />
                </p>
              </details>
            ))}
          </div>
          <p className="mt-6 max-w-[66ch] text-sm leading-relaxed text-muted">
            Not claimed: that Volley has changed any child&apos;s outcome; that its count equals the research recorder&apos;s; that
            a parent should aim for any number. Every study above is resolved on PubMed or Crossref in the
            repository&apos;s citations file, with what it showed and what it did not, and a test refuses any citation in this page
            that is not there.
          </p>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* Developers. */}
        <section id="developers" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Everything here is a test you can run.</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Run it</p>
              <pre tabIndex={0} className="mt-3 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                {"python -m venv .venv\n.venv/Scripts/pip install -e packages/serve-return[dev] -e apps/ingest[dev] -e apps/server[dev]\n.venv/Scripts/python -m pytest packages apps    # every test\ncd apps/web && npm install && npm test && npm run dev"}
              </pre>
            </div>
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Use the counter</p>
              <pre tabIndex={0} className="mt-3 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                {'from serve_return import Utterance, Roles, count_day\n\nroles = Roles.of(adult=["MOT"], child=["CHI"])\nday = count_day(utterances, roles)\nday.turns, day.best_hour, day.words_discarded'}
              </pre>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                <code className="font-mono text-xs">serve-return</code> is the open-source deliverable: the published rule as a
                dependency-free package, for anyone who cannot afford the research recorder.
              </p>
            </div>
          </div>
          <p className="mt-6 text-sm leading-relaxed text-muted">
            <a className="text-[var(--accent)] underline underline-offset-4" href={REPO}>
              Repository
            </a>
            {" · "}
            <a className="text-[var(--accent)] underline underline-offset-4" href={`${REPO}/blob/main/docs/EVIDENCE.md`}>
              The evidence, with sources
            </a>
            {" · "}
            <a className="text-[var(--accent)] underline underline-offset-4" href={`${REPO}/blob/main/docs/PRIOR_ART.md`}>
              Prior art
            </a>
            {" · "}
            <a className="text-[var(--accent)] underline underline-offset-4" href={`${REPO}/blob/main/FRICTION_LOG.md`}>
              Friction log
            </a>
            {" · "}
            <a className="text-[var(--accent)] underline underline-offset-4" href={`${REPO}/blob/main/skills/volley/SKILL.md`}>
              Agent Skill
            </a>
          </p>
        </section>

        <Footer />
      </main>
    </>
  );
}

/** One agent's run, word for word. A desk shows it open; a phone folds it under one line. */
function AgentRun({ a }: { a: (typeof AGENTS)[number] }) {
  const run = (
    <>
      <div className="rounded-lg border border-line bg-[var(--raised)] p-4">
        <p className="text-[13px] leading-snug text-ink">{a.asked}</p>
        <p className="mt-3 font-mono text-[12px] leading-relaxed break-words text-muted">$ {a.command}</p>
        <blockquote className="mt-3 text-[15px] leading-relaxed text-ink">{a.answer}</blockquote>
        <p className="mt-3 font-mono text-[12px] leading-relaxed break-words text-muted">[{a.tools}]</p>
      </div>
      <p className="mt-3 text-xs leading-relaxed text-muted">{a.caption}</p>
    </>
  );
  return (
    <>
      <div className="mt-5 hidden md:block">{run}</div>
      <details className="fold mt-4 border-t border-line md:hidden">
        <summary>
          The run, word for word
          <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </summary>
        <div className="pb-2">{run}</div>
      </details>
    </>
  );
}
