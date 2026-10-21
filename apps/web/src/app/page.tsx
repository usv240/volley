import corpus from "../data/corpus.json";
import blind from "../data/blind.json";
import device from "../data/device.json";
import controls from "../data/controls.json";
import demo from "../data/demo.json";
import tuesdaySim from "../data/tuesday-sim.json";
import { DayView, bestHourNote, clock, type Day } from "../components/DayView";
import { DropZone } from "../components/DropZone";
import { EvidenceSummary } from "../components/EvidenceSummary";
import { Info } from "../components/Info";
import { McpProof } from "../components/McpProof";
import { Nav } from "../components/Nav";
import { PrivacyProof } from "../components/PrivacyProof";
import { StepsHandoff } from "../components/StepsHandoff";
import { VoiceAsk } from "../components/VoiceAsk";
import { WorkedExample } from "../components/WorkedExample";

/**
 * One page, read top to bottom in one pass by somebody who has never
 * heard of any of this, and by a judge with three minutes. The parent
 * reads the page; everyone else reads the i-buttons. Each section
 * answers one question and its heading is the answer.
 *
 * Every number with a source has its source on the i. Every claim has a
 * panel that does it live. Anything not yet measured says so in the same
 * type size as the numbers, and names the study that would measure it.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";
const REPO = "https://github.com/usv240/volley";

const STATS = [
  {
    figure: "14 to 27%",
    label: "of the variance in IQ and vocabulary at ages 9 to 14, explained by conversational turns at 18 to 24 months, after adjusting for family income (Gilkerson, Pediatrics 2018)",
    term: "countsNotWords" as const,
  },
  {
    figure: "Turns, not words",
    label: "predicted activity in the brain's language area, independent of income and IQ (Romeo, Psychological Science 2018)",
    term: "ses" as const,
  },
  {
    figure: "Coachable",
    label: "parents shown their own recordings raised turns and their children's language, and the gain held to 30 months (Ferjan Ramirez, PNAS 2020; Huber, Developmental Science 2023)",
    term: "serve" as const,
  },
];

const NEVER = [
  { head: "It is not a test of your child.", body: "A count, like steps. No score, no percentile, no comparison with other children, ever." },
  { head: "It does not compare you with other families.", body: "The only comparison is with your own days and one published target, stated as its source's figure." },
  { head: "It never keeps a word.", body: "The words are read on your computer, counted, and gone. The server refuses a transcript, and you can watch it do so above." },
  {
    head: "It does not know what the television was doing.",
    body: "A 2009 study of 329 children found each hour of audible television cut turns by about a fifth of a standard deviation. Volley cannot see the set; the by-hour view is the only place a quiet hour will show, and it will not say why.",
  },
];

const STEPS = [
  { title: "Install Bee's command line tool", body: "npm install -g @beeai/cli", live: true },
  { title: "Turn on Developer Mode in the Bee app", body: "Settings, then tap the version number five times.", live: true, term: "developerMode" as const },
  { title: "Sign in the tool to your Bee", body: "bee login, then approve it in the app.", live: true },
  { title: "Install Volley", body: 'pip install serve-return "volley-bee @ git+https://github.com/usv240/volley#subdirectory=apps/ingest"', live: true },
  { title: "Count the day", body: "volley setup --blind --child-name Asha\nvolley today", live: true },
  { title: "See your days in a browser, if you want to", body: "volley connect\nvolley today", live: true, term: "mine" as const },
];

const SETUP_OPTIONS =
  "Two setup options: volley setup --daily 20:30 counts every evening without typing, and --only-with-child yes sets aside stretches where no voice sounds like a child (the evidence on the page says what that costs).";

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

const FAQ = [
  ["Is a low day bad?", "No. It is a count of one day. The note names your best hour so you keep what already works, and one thing to try tomorrow. That is all it does."],
  ["Does it listen to my child?", "The Bee on your wrist transcribes what it hears, including your child. Volley reads that transcript on your computer, counts, and deletes the words. Nothing your child said is ever stored by Volley."],
  ["What if my child does not talk yet?", "Volley counts transcribed words, and a baby's babble may not be transcribed. Until that is measured, Volley is for children of talking age, about two to five. The research instrument counts sounds; this does not, and says so."],
  ["Do I need to talk all day?", "No. Turns are exchanges, not volume. Ten good minutes at bath time count more than an hour of narration the child does not answer."],
  ["What is a good number?", "LENA, whose recorder the studies used, publishes forty turns an hour as a target. Volley shows that figure as theirs and sets none of its own."],
  ["Who can see this?", "You, with your key. The simulated family on this page is public and says so. There is no account with Volley beyond a name you chose."],
  ["What about the television?", "Volley cannot see it. If an hour is quiet, the by-hour view will show it; what was happening is yours to notice."],
  ["Can I delete it?", "Yes. The Bee app deletes the conversation; one request with your key deletes the household and every count."],
];

export default function Home() {
  const days = demo.days as Day[];
  const today = days[days.length - 1];
  const week = days.slice(-7);
  const bestWeekHour = (() => {
    const by: Record<number, number> = {};
    for (const d of week) for (const h of d.hours) by[h.hour] = (by[h.hour] ?? 0) + h.turns;
    return Object.entries(by).sort((a, b) => b[1] - a[1])[0];
  })();

  // The nudge drawing, read from the same simulated fortnight: the week's
  // usual best hour and its average, and the evening that hour was
  // quietest, drawn up to the moment that hour is under way.
  const nudge = (() => {
    if (!bestWeekHour) return null;
    const hour = Number(bestWeekHour[0]);
    const usual = Math.round(bestWeekHour[1] / week.length);
    const at = (d: Day, h: number) => d.hours.find((x) => x.hour === h);
    const quiet = days
      .filter((d) => (at(d, hour)?.utterances_child ?? 0) > 0)
      .reduce((a, b) => ((at(b, hour)?.turns ?? 0) < (at(a, hour)?.turns ?? 0) ? b : a));
    const cols = [hour - 3, hour - 2, hour - 1, hour, hour + 1].map((h) => ({
      hour: h,
      turns: h < hour ? (at(quiet, h)?.turns ?? 0) : h === hour ? (at(quiet, h)?.turns ?? 0) : null,
    }));
    const soFar = at(quiet, hour)?.turns ?? 0;
    const max = Math.max(usual, ...cols.map((c) => c.turns ?? 0));
    return { hour, usual, date: quiet.date, soFar, cols, max };
  })();

  return (
    <>
      <a href="#top" className="skip-link">
        Skip to content
      </a>
      <Nav />

      <main id="top" className="mx-auto max-w-[1120px] px-5 pb-28 sm:px-8">
        {/* 1. Hero: the claim, the tagline, the two numbers, today's day. */}
        <section className="grid gap-10 pt-8 sm:pt-12 lg:grid-cols-[1.05fr_1fr] lg:items-start lg:pt-14">
          <div>
            <h1 className="display max-w-[16ch] text-[2.5rem] leading-[1.04] text-ink sm:text-6xl sm:leading-[1.02]">
              Your child&apos;s language grows with the <span className="whitespace-nowrap">back-and-forth.</span> Volley counts it.
            </h1>
            <p className="mt-5 max-w-[58ch] text-[17px] leading-relaxed text-ink sm:mt-6 sm:text-lg">
              A step counter for conversations with your child. Volley counts the back-and-forth from the Bee on your wrist, throws the
              words away on your own computer <Info term="onYourComputer" />, and puts one thing to try tomorrow into your Bee as a
              reminder.
            </p>
            <p className="mt-4 max-w-[58ch] leading-relaxed text-muted">
              A turn <Info term="turn" /> is you saying something and your child answering within five seconds, or the other way round.
            </p>
            <div className="mt-7 flex flex-wrap gap-3 sm:mt-8">
              <a href="#how" className="primary">
                See how it counts
              </a>
              <a href="#yours" className="secondary">
                Count your own
              </a>
            </div>
          </div>
          <DayView
            day={today}
            child={demo.child_name}
            simulated
            footnote={
              <>
                Generated counts, not a day a Bee heard. On real recordings with no speaker labels, the median session&apos;s count was{" "}
                {blind.median_abs_session_error_pct} percent from the true one, across{" "}
                <a href="#blind" className="underline underline-offset-2">
                  {blind.sessions} sessions
                </a>
                .
              </>
            }
          />
        </section>

        {/* 1b. The two measured numbers, said once, under the claim they test. */}
        <section aria-label="Measured" className="mt-14 border-y border-line py-6">
            <p className="max-w-[86ch] leading-relaxed text-muted">
              Measured, not claimed: on {corpus.hours} hours of public parent-child recordings we did not make, the
              rule counted <strong className="text-ink">{corpus.turns.toLocaleString("en-US")} turns</strong> from the human speaker
              labels, <strong className="text-ink">zero</strong> inside any stretch where one person spoke alone{" "}
              <Info term="corpus" />; on the builder&apos;s own Bee, hearing a real parent-child conversation voiced by Amazon Polly
              with no person in the room, Volley counted <strong className="text-ink">{device.turns_blind} of {device.turns_true} turns</strong>{" "}
              with no speaker labels at all. Neither is a hand count by a person, and the page says what that leaves{" "}
              <Info term="validated" />.
            </p>
        </section>

        {/* 2. Three figures, each with its study on the i. */}
        <dl className="mt-16 grid gap-6 sm:grid-cols-3">
          {STATS.map((s) => (
            <div key={s.figure} className="border-t border-line pt-4">
              <dt className="display-sm text-3xl text-ink">
                {s.figure} <Info term={s.term} />
              </dt>
              <dd className="mt-2 text-sm leading-relaxed text-muted">{s.label}</dd>
            </div>
          ))}
        </dl>

        <div className="rule my-12 sm:my-20" />

        {/* 3. What, why, how. */}
        <section id="what" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">What it is, why it exists, how it runs.</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="card p-6">
              <p className="font-semibold text-ink">What</p>
              <p className="mt-2 leading-relaxed text-muted">A count of the back-and-forth between you and your child, by the hour, every day, and one thing to try tomorrow.</p>
            </div>
            <div className="card p-6">
              <p className="font-semibold text-ink">Why</p>
              <p className="mt-2 leading-relaxed text-muted">
                This is the number that predicted language and IQ a decade later and survived the income adjustment that word counts did
                not <Info term="countsNotWords" />. The instrument that measures it, LENA <Info term="lena" />, is sold to programmes and
                clinics, not to parents. You already wear the device that can.
              </p>
            </div>
            <div className="card p-6">
              <p className="font-semibold text-ink">How</p>
              <p className="mt-2 leading-relaxed text-muted">
                Your Bee <Info term="bee" /> transcribes the day. Volley reads the transcript on your computer, counts by the published
                rule, deletes the words, and shows the day. Only the counts <Info term="whatLeaves" /> can leave, and only if you ask.
              </p>
            </div>
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 4. How it counts, watched. */}
        <section id="how" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">How it counts, in twenty seconds.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            Press play. Each bar is something somebody said; the band after it is the five-second window. The number in the corner is
            the same rule that runs on your computer, counting these bars as they arrive.
          </p>
          <div className="mt-10">
            <WorkedExample />
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 5. The day and the week, like steps. */}
        <section id="day" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">A day, an hour at a time, and one thing for tomorrow.</h2>
          <div className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            <div className="card p-6 sm:p-8">
              <p className="eyebrow">This week, simulated</p>
              <ul className="mt-4 space-y-2" aria-label="Turns per day">
                {week.map((d) => (
                  <li key={d.date} className="flex items-center gap-3 text-sm">
                    <span className="w-24 text-faint">{d.date.slice(5)}</span>
                    <span className="ew-track flex-1">
                      <span className="ew-bar" style={{ width: `${Math.round((100 * d.turns) / Math.max(...week.map((x) => x.turns)))}%` }} />
                    </span>
                    <span className="w-12 text-right text-ink">{d.turns}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm text-muted">
                Best hour this week: {bestWeekHour ? `${clock(Number(bestWeekHour[0]))}, ${bestWeekHour[1]} turns` : "none yet"}. The
                published target <Info term="target" /> is forty an hour; Volley shows it and sets none of its own{" "}
                <Info term="noPercentile" />.
              </p>
            </div>
            <div className="card p-6 sm:p-8">
              <p className="eyebrow">Tomorrow, written from today&apos;s counts</p>
              <blockquote className="mt-4 border-l border-[var(--line-strong)] pl-4">
                <p className="leading-relaxed text-ink">{bestHourNote(today, demo.child_name)}</p>
                <footer className="mt-2 text-xs text-faint">the template layer, from the fact: best hour</footer>
              </blockquote>
              <p className="mt-4 text-sm leading-relaxed text-muted">
                Rules pick the fact; Claude on Bedrock phrases it; every digit must come from the fact or the template is used{" "}
                <Info term="bedrock" />. With your consent the sentence goes into your Bee as a reminder at that hour.
              </p>
            </div>
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 5b. In the moment: the nudge inside the hour that usually talks most. */}
        {nudge && (
          <>
            <section id="nudge" className="scroll-mt-24">
              <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Coaching in the moment, not the morning after.</h2>
              <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.2fr] lg:items-start">
                <div>
                  <p className="max-w-[60ch] text-[17px] leading-relaxed text-ink">
                    During the hour the family usually talks most,{" "}
                    <code className="font-mono text-[15px]">volley live --nudge</code> watches the Bee&apos;s live stream, and if that
                    hour is going quiet it puts a nudge into the Bee then; with <code className="font-mono text-[15px]">--say</code>, a
                    speaker in the room says it aloud, a stand-in for an Echo.
                  </p>
                  <p className="mt-4 max-w-[60ch] leading-relaxed text-muted">
                    The note above is written for tomorrow. This one arrives while the hour can still be had.
                  </p>
                  <pre
                    tabIndex={0}
                    className="mt-6 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink"
                  >
                    {"volley live --nudge\nvolley live --nudge --say"}
                  </pre>
                </div>

                <figure className="card min-w-0 p-6 sm:p-8">
                  <p className="font-semibold text-ink">One evening, simulated</p>
                  <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <dt className="text-muted">usual hour</dt>
                      <dd className="font-semibold text-ink">{clock(nudge.hour)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted">usually</dt>
                      <dd className="font-semibold text-ink tabular-nums">{nudge.usual} turns</dd>
                    </div>
                    <div>
                      <dt className="text-muted">so far</dt>
                      <dd className="font-semibold text-ink tabular-nums">{nudge.soFar} turns</dd>
                    </div>
                  </dl>
                  <div
                    className="nudge-cols mt-8"
                    style={{ ["--cols" as string]: nudge.cols.length }}
                    role="img"
                    aria-label={`Simulated evening: ${nudge.cols
                      .filter((c) => c.turns !== null)
                      .map((c) => `${clock(c.hour)} ${c.turns} turns`)
                      .join(", ")}; ${clock(nudge.hour)} usually has ${nudge.usual}, and the nudge goes into the Bee while that hour is under way.`}
                  >
                    {nudge.cols.map((c) => {
                      const now = c.hour === nudge.hour;
                      return (
                        <div key={c.hour} className="nudge-col" aria-hidden="true">
                          <span className="h-4 text-xs leading-4 text-muted tabular-nums">{c.turns === null || now ? "" : c.turns}</span>
                          <div className="nudge-track">
                            {now && <span className="nudge-usual" style={{ height: `${(100 * nudge.usual) / nudge.max}%` }} />}
                            {now && (
                              <span className="nudge-pin" style={{ bottom: `calc(${(100 * nudge.usual) / nudge.max}% + 0.5rem)` }}>
                                <span>nudge</span>
                              </span>
                            )}
                            {c.turns === null ? (
                              <span className="nudge-empty" />
                            ) : (
                              <span className="nudge-bar" style={{ height: `${Math.max(2, (100 * c.turns) / nudge.max)}%` }} />
                            )}
                          </div>
                          <span className={`h-4 text-xs leading-4 ${now ? "font-semibold text-ink" : "text-muted"}`}>{clock(c.hour)}</span>
                          <span className="h-4 whitespace-nowrap text-[11px] leading-4 text-muted">{now ? "now" : c.turns === null ? "not yet" : ""}</span>
                        </div>
                      );
                    })}
                  </div>
                  <ul className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted" aria-hidden="true">
                    <li className="flex items-center gap-2">
                      <span className="inline-block h-3 w-3 rounded-sm bg-[var(--chart-mark)]" />
                      turns
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="inline-block h-3 w-3 rounded-sm border-[1.5px] border-dashed border-[var(--muted)]" />
                      usual for that hour, the week&apos;s average
                    </li>
                  </ul>
                  <figcaption className="mt-4 text-xs leading-relaxed text-muted">
                    Simulated: the simulated family&apos;s {nudge.date}, its quietest {clock(nudge.hour)} of the fortnight, against that
                    hour&apos;s average for the week ending {LATEST}. The drawing stops at the moment the nudge goes in; when exactly it
                    fires is the command&apos;s rule, not the drawing&apos;s.
                  </figcaption>
                </figure>
              </div>
            </section>

            <div className="rule my-12 sm:my-20" />
          </>
        )}

        {/* 6. What it will never say. */}
        <section id="never" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">What it will never say.</h2>
          <div className="mt-10 grid gap-x-10 gap-y-8 md:grid-cols-2">
            {NEVER.map((n) => (
              <div key={n.head} className="border-t border-line pt-5">
                <p className="font-semibold text-ink">{n.head}</p>
                <p className="mt-2 leading-relaxed text-muted">{n.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 6b. Questions a parent asks. */}
        <section id="questions" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Questions a parent asks.</h2>
          <div className="mt-8 hidden gap-x-10 gap-y-6 md:grid md:grid-cols-2">
            {FAQ.map(([q, a]) => (
              <div key={q} className="border-t border-line pt-4">
                <p className="font-semibold text-ink">{q}</p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{a}</p>
              </div>
            ))}
          </div>
          {/* A phone gets the same answers, one question a line, opened on tap. */}
          <div className="fold-list mt-6 border-y border-line md:hidden">
            {FAQ.map(([q, a]) => (
              <details key={q} className="fold">
                <summary>
                  {q}
                  <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                      <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </summary>
                <p className="pb-5 text-sm leading-relaxed text-muted">{a}</p>
              </details>
            ))}
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 7. Privacy, demonstrated. */}
        <section id="privacy" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">A transcript, refused by the server, while you watch.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            The API accepts counts and drops every field it does not know at the door. That is a claim until it is pressed. What the
            Bee itself keeps is Amazon&apos;s promise, in its own privacy notice, and not ours to restate.
          </p>
          <div className="mt-10">
            <PrivacyProof />
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 8. Your Bee, in ten minutes. */}
        <section id="yours" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Your own day, in ten minutes.</h2>
          <StepsHandoff steps={STEPS} note={SETUP_OPTIONS} />
          <ol className="mt-8 grid grid-cols-1 gap-4 md:mt-10 md:grid-cols-2">
            {STEPS.map((s, i) => (
              <li key={s.title} className="card min-w-0 p-5">
                <div className="flex items-baseline gap-3">
                  <span className="display-sm text-2xl text-[var(--accent)]">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-ink">
                      {s.title} {s.term && <Info term={s.term} />}
                    </p>
                    <pre tabIndex={0} className="mt-2 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                      {s.body}
                    </pre>
                  </div>
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-6 max-w-[66ch] text-sm leading-relaxed text-muted">
            Two setup options: <code className="font-mono text-xs text-ink">volley setup --daily 20:30</code> counts every evening
            without typing, and <code className="font-mono text-xs text-ink">--only-with-child yes</code> sets aside stretches where
            no voice sounds like a child;{" "}
            <a href="#evidence" className="text-[var(--accent)] underline underline-offset-4">
              the evidence
            </a>{" "}
            says what that costs.
          </p>
          <p className="mt-3 max-w-[66ch] text-sm leading-relaxed text-muted">
            Recording other people is your responsibility under local law; the setup screen says so before anything runs. The child
            wears nothing. Your child&apos;s words never leave your computer.
          </p>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 9. Bring your own data. */}
        <section id="byo" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Three doors, each for someone.</h2>
          <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Parents: your Bee, on your computer</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">The steps above. The only door that reads a transcript, and it reads it where you are; the counts, and nothing else, can go to a page that is yours.</p>
            </div>
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Anyone curious: a Bee export, in this tab</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">Drop a file below. It is counted in your browser and uploaded nowhere.</p>
            </div>
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">
                Developers: an API key <Info term="apiKey" />
              </p>
              <pre tabIndex={0} className="mt-2 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                {`curl -X POST ${API_URL}/v1/households \\\n  -H 'content-type: application/json' \\\n  -d '{"name":"ours","child_name":"Asha"}'`}
              </pre>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Then POST counts to <code className="font-mono text-xs">/v1/households/{"{id}"}/days</code> with X-Api-Key, and read{" "}
                <code className="font-mono text-xs">/days</code>, <code className="font-mono text-xs">/week</code>,{" "}
                <code className="font-mono text-xs">/note</code>.{" "}
                <a className="text-[var(--accent)] underline underline-offset-4" href={`${API_URL}/v1/docs`}>
                  Interactive docs
                </a>
                . The schema drops what it does not know; the privacy section shows it.
              </p>
            </div>
          </div>
          <div className="mt-8">
            <DropZone />
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 10. Alexa+. */}
        <section id="alexa" className="scroll-mt-24">
          <h2 className="display-sm max-w-[22ch] text-3xl text-ink sm:text-4xl">Ask it out loud, and it cannot repeat a word.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            An MCP server <Info term="mcp" />, spec 2025-11-25 over Streamable HTTP, with seven tools and an Agent Skill{" "}
            <Info term="skill" />. It can say how the talking went today, what to try tomorrow, the week&apos;s direction and the best
            hour; it can record a day of counts; and it explains the rule. It has no tool that returns speech, because the server never
            receives any, and a test walks every tool to prove it.
          </p>
          <div className="mt-10">
            <McpProof />
            <VoiceAsk />
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 10a. The agents: two clients of the same MCP server, held to the numbers a tool returned. */}
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

        {/* 10b. Impact: who has paid for this count already, and what changes at fifty dollars. */}
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

        {/* 11. Evidence: the results at a glance, then the prose folded beneath, then the literature. */}
        <section id="evidence" className="scroll-mt-24">
          <h2 className="display-sm max-w-[24ch] text-3xl text-ink sm:text-4xl">What it refused to count, what it beat, and how close it is to a person.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            Written for somebody who came here to find the weak point. Measured here, read from the literature, and not done yet are
            kept apart on purpose. Every figure below is read from the results the harness committed.
          </p>
          <EvidenceSummary />
          <div className="mt-8 border-y border-line">
            <details className="fold">
              <summary>
                The weak point in full: one voice, two adults, and the opt-in check
              <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
              <div className="pb-6">
                <p className="max-w-[70ch] leading-relaxed text-muted">
                  On the public corpus, <strong className="text-ink">{corpus.turns_inside_them} turns</strong> inside its{" "}
                  {corpus.single_speaker_stretches} stretches of a minute or more where one person spoke alone{" "}
                  <Info term="corpus" />, from the human speaker labels. Without labels it is the weak point: two adults from a real
                  family dinner, no child, played to the Bee for {controls.adults_seconds} seconds, gave{" "}
                  <strong className="text-ink">{controls.adults_false_turns} false turns</strong>, and one adult voice gave{" "}
                  {controls.onevoice_false_turns}, against {controls.real_turns_same_length} for a real parent and child of the same
                  length. On the corpus, removing the child leaves false turns at {controls.corpus_false_as_pct_of_real} percent of the
                  real count.
                </p>
                <p className="mt-3 max-w-[70ch] leading-relaxed text-muted">
                  A check that a child is present now ships as an opt-in setting,{" "}
                  <code className="font-mono text-xs text-ink">volley setup --only-with-child yes</code>. On the Bee it kept{" "}
                  <strong className="text-ink">
                    {controls.with_child_real} of {controls.with_child_real_every}
                  </strong>{" "}
                  turns of the real conversation, took two adults from {controls.adults_false_turns} false turns to{" "}
                  <strong className="text-ink">{controls.with_child_adults}</strong>, and one adult voice from{" "}
                  {controls.onevoice_false_turns} to <strong className="text-ink">{controls.with_child_onevoice}</strong>. On the corpus,
                  held out by family, it refused {controls.gate_refused_pct} percent of adults-only stretches and lost{" "}
                  {controls.gate_turns_lost_pct} percent of true turns. That loss is the trade, and it is why the check is a choice and
                  not the default. The Bee&apos;s own speaker label would end this.
                </p>
              </div>
            </details>
            <details className="fold border-t border-line">
              <summary>
                Against the obvious alternatives: adult word count and a bare speaker-change count
              <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
              <p className="max-w-[70ch] pb-6 leading-relaxed text-muted">
                Adult word count, which the last consumer device sold: across the corpus&apos;s {corpus.sessions} sessions it ranks
                with turns at Spearman <strong className="text-ink">{corpus.spearman_adult_words_vs_turns}</strong>, and two sessions
                with the same adult words carried turns{" "}
                <strong className="text-ink">{corpus.same_words_different_turns?.ratio} times</strong> apart{" "}
                <Info term="wordsVsTurns" />. A speaker-change count with no window agreed with the rule on{" "}
                {corpus.alternations_within_window_percent} percent of alternations, because the corpus&apos;s aligned timing has no
                gaps <Info term="windowOnCorpus" />; the window&apos;s work is in a day, not a lab session.
              </p>
            </details>
            {/*
              The Bee labels every speaker Unknown. This is the answer, measured
              on families the model never saw, with the naive alternative beside it.
            */}
            <details id="blind" className="fold scroll-mt-24 border-t border-line">
              <summary>
                No speaker labels: how roles are read, and the run on the Bee
              <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
              <div className="pb-6">
                <p className="max-w-[70ch] leading-relaxed text-muted">
                  The Bee labels every speaker &ldquo;Unknown&rdquo;, so Volley reads who is the child and who the adult from the words
                  and the pauses, with a model trained on CHILDES and scored only on families it was not trained on. Across{" "}
                  {blind.sessions} sessions it counted <strong className="text-ink">{blind.turns_blind.toLocaleString("en-US")} turns</strong>{" "}
                  against {blind.turns_true.toLocaleString("en-US")} true ({blind.total_error_pct > 0 ? "+" : ""}
                  {blind.total_error_pct} percent); the median session was within{" "}
                  <strong className="text-ink">{blind.median_abs_session_error_pct} percent</strong>, and turns per hour tracked the truth
                  at a correlation of <strong className="text-ink">{blind.correlation_per_hour}</strong>. Treating every pause as a
                  change of speaker missed by {Math.abs(blind.naive_total_error_pct)} percent. Misread roles merge exchanges, so a raw
                  blind count runs low by a steady {Math.round((1 - 1 / blind.turn_scale_min) * 100)} to{" "}
                  {Math.round((1 - 1 / blind.turn_scale_max) * 100)} percent; Volley scales for it with a factor learned only from other
                  families, which took the median session error from {blind.uncalibrated_median_abs_session_error_pct} to{" "}
                  {blind.median_abs_session_error_pct} percent. Each utterance&apos;s role was right {blind.role_accuracy_pct} percent of
                  the time, so a single exchange can be misread; a day, a week and a trend are what it is for.
                </p>
                <p className="mt-4 max-w-[70ch] leading-relaxed text-muted">
                  <span className="font-semibold text-ink">On the Bee itself.</span> A real mother-and-child conversation from the same
                  corpus, voiced by Amazon Polly with an adult and a child voice at its original timing, played to the band for{" "}
                  {Math.round(device.played_seconds)} seconds, no person in the room. The Bee wrote {device.utterances_bee} utterances
                  for {device.utterances_played} played and kept{" "}
                  <strong className="text-ink">
                    {device.turns_bee_with_true_roles} of {device.turns_true} turns
                  </strong>
                  : its segmentation loses none. Volley, with no labels and a model that never saw this family or its scale, counted{" "}
                  <strong className="text-ink">{device.turns_blind}</strong> ({device.blind_error_pct} percent), with{" "}
                  {device.role_accuracy_pct} percent of lines given the right speaker. One session; the corpus says how much one session
                  varies.
                </p>
              </div>
            </details>
            <details className="fold border-t border-line">
              <summary>
                The public corpus, every rate, measured 2026-09-30
              <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
              <div className="pb-6">
                <p className="max-w-[70ch] leading-relaxed text-muted">
                  The CHILDES Gleason corpus: {corpus.sessions} sessions, {corpus.hours} hours, 24 children aged 2;1 to 5;2 with their
                  mother, with their father and at the family dinner table, human speaker labels, aligned timing. The rule counted{" "}
                  {corpus.turns.toLocaleString("en-US")} turns: {corpus.turns_per_hour_min} to {corpus.turns_per_hour_max} an hour by
                  session, median {corpus.turns_per_hour_median}. Dinner {corpus.by_situation.Dinner.turns_per_hour}, with the mother{" "}
                  {corpus.by_situation.Mother.turns_per_hour}, with the father {corpus.by_situation.Father.turns_per_hour} an hour.
                  Children under three, {corpus.under_36_months.turns_per_hour} an hour across {corpus.under_36_months.sessions}{" "}
                  sessions; three and over, {corpus.from_36_months.turns_per_hour} across {corpus.from_36_months.sessions}. A
                  fifty-second window instead of five changed the count to {corpus.turns_with_50s_window.toLocaleString("en-US")}.{" "}
                  {corpus.files_without_time_marks} files had no timing and were skipped by name.
                </p>
                <p className="mt-3 max-w-[70ch] text-sm leading-relaxed text-muted">
                  What this shows: the rule, the roles and the alternation logic hold on human-labelled recordings at twenty times the
                  published daylong target, which is what half an hour of a parent&apos;s full attention looks like. What it does not
                  show: the window, because the aligner&apos;s timing is contiguous; the device&apos;s transcription of a two-year-old,
                  because these are human transcripts; and any family&apos;s day. No person has hand-counted a day on the Bee, and
                  that count is what would answer the last two <Info term="harness" />.{" "}
                  <code className="font-mono text-xs">volley verify</code> recomputes every figure in this paragraph from the committed
                  results, and from the corpus itself where it is present.
                </p>
              </div>
            </details>
            <details className="fold border-t border-line">
              <summary>
                Read from the literature: every study on this page
              <svg className="fold-mark" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted">
              <li>Gilkerson J et al. Language Experience in the Second Year of Life and Language Outcomes in Late Childhood. Pediatrics 2018. PMID 30201624. Three authors work for the LENA Foundation.</li>
              <li>Romeo RR et al. Beyond the 30-Million-Word Gap. Psychological Science 2018. PMID 29442613.</li>
              <li>Ferjan Ramirez N, Lytle SR, Kuhl PK. Parent coaching increases conversational turns and advances infant language development. PNAS 2020. PMID 32015127.</li>
              <li>Huber E et al. Parent coaching from 6 to 18 months improves child language outcomes through 30 months of age. Developmental Science 2023. PMID 36999222.</li>
              <li>Christakis DA et al. Audible television and decreased adult words, infant vocalizations, and conversational turns. Archives of Pediatrics and Adolescent Medicine 2009. PMID 19487612.</li>
              <li>Romeo RR et al. Language Exposure Relates to Structural Neural Connectivity in Childhood. Journal of Neuroscience 2018. PMID 30104336.</li>
              <li>Romeo RR et al. Neuroplasticity associated with changes in conversational turn-taking following a family-based intervention. Developmental Cognitive Neuroscience 2021. PMID 34052580.</li>
              <li>Suskind DL et al. A parent-directed language intervention for children of low socioeconomic status: a randomized controlled pilot study. Journal of Child Language 2016. PMID 26041013.</li>
              <li>Leung CYY, Hernandez MW, Suskind DL. Enriching home language environment among families from low-SES backgrounds: A randomized controlled trial of a home visiting curriculum. Early Childhood Research Quarterly 2020. doi 10.1016/j.ecresq.2018.12.005.</li>
              <li>Elmquist M et al. Parent education to improve early language development: A preliminary evaluation of LENA Start. Journal of Child Language 2021. PMID 32921333.</li>
              <li>Wong K, Thomas C, Boben M. Providence talks: A citywide partnership to address early childhood language development. Studies in Educational Evaluation 2020. doi 10.1016/j.stueduc.2019.100818.</li>
              <li>Gomez E, Strasser K. Language and socioemotional development in early childhood: The role of conversational turns. Developmental Science 2021. PMID 33825290.</li>
              <li>Sperry DE, Sperry LL, Miller PJ. Reexamining the Verbal Environments of Children From Different Socioeconomic Backgrounds. Child Development 2019. PMID 29707767; and the reply, Golinkoff RM et al., PMID 30102419.</li>
              <li>Reed J, Hirsh-Pasek K, Golinkoff RM. Learning on hold: Cell phones sidetrack parent-child interactions. Developmental Psychology 2017. PMID 28650177.</li>
              <li>Radesky JS et al. Patterns of mobile device use by caregivers and children during meals in fast food restaurants. Pediatrics 2014. PMID 24616357.</li>
              <li>Cristia A et al. A thorough evaluation of the Language Environment Analysis (LENA) system. Behavior Research Methods 2020. PMID 32728916.</li>
              <li>Ferjan Ramirez N, Hippe DS, Kuhl PK. Comparing Automatic and Manual Measures of Parent-Infant Conversational Turns: A Word of Caution. Child Development 2021. doi 10.1111/cdev.13495.</li>
              <li>Norbury CF et al. The impact of nonverbal ability on prevalence and clinical presentation of language disorder. Journal of Child Psychology and Psychiatry 2016. PMID 27184709.</li>
              <li>Council on Early Childhood. Literacy promotion: an essential component of primary care pediatric practice. Pediatrics 2014. PMID 24962987. Garner A, Yogman M. Preventing Childhood Toxic Stress: Partnering With Families and Communities to Promote Relational Health. Pediatrics 2021. PMID 34312296.</li>
              <li>Harvard University Center on the Developing Child. Serve and Return.</li>
              <li>
                The corpus: Gleason JB, CHILDES English Gleason Corpus, doi 10.21415/T5101R, used under the TalkBank ground rules{" "}
                <Info term="playlogueLicence" />, and cited as they require through Masur EF, Gleason JB. Parent-child interaction and
                the acquisition of lexical information during play. Developmental Psychology 1980. doi 10.1037/0012-1649.16.5.404.
                The database, cited as the rules also ask: MacWhinney B. The CHILDES Project: Tools for analyzing talk. Third edition.
                Mahwah, NJ: Lawrence Erlbaum Associates, 2000; CHILDES is supported by NICHD grant HD082736. Retrieved and analysed
                2026-09-30. Playlogue (Kalanadhabhatta et al., IMWUT 2024), the corpus first planned, is gated behind the same rules
                on Hugging Face; the harness for it is in the repository and runs the day access opens.
              </li>
            </ul>
              <div className="pb-6" />
            </details>
          </div>
        </section>

        <div className="rule my-12 sm:my-20" />

        {/* 12. Developers. */}
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


        <footer className="mt-24 border-t border-line pt-8 text-sm text-muted">
          <p>
            Open source, MIT.{" "}
            <a className="text-[var(--accent)] underline underline-offset-4" href={REPO}>
              The repository
            </a>{" "}
            carries the evidence, the prior art, and every number on this page as a test. LENA is a registered mark of the LENA
            Foundation; Volley implements the published definition and is not affiliated.
          </p>
          <p className="mt-3">Not a diagnosis, not a test, a count. Built for the Build, Ship, Shape: Amazon Developer Hackathon.</p>
        </footer>
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
