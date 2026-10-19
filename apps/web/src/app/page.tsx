import corpus from "../data/corpus.json";
import blind from "../data/blind.json";
import device from "../data/device.json";
import demo from "../data/demo.json";
import { DayView, clock, type Day } from "../components/DayView";
import { DropZone } from "../components/DropZone";
import { Info } from "../components/Info";
import { McpProof } from "../components/McpProof";
import { Nav } from "../components/Nav";
import { PrivacyProof } from "../components/PrivacyProof";
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
  { title: "Install Volley, from GitHub", body: 'pip install "git+https://github.com/usv240/volley#subdirectory=packages/serve-return" "git+https://github.com/usv240/volley#subdirectory=apps/ingest"', live: true },
  { title: "Count the day", body: "volley setup --blind --child-name Asha --tz 5.5\nvolley today", live: true },
  { title: "See your days in a browser, if you want to", body: "volley connect\nvolley today", live: true, term: "mine" as const },
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
  ["What if my child does not talk yet?", "Volley counts transcribed words, and a baby's babble may not be transcribed. Until that is measured, Volley is for children of talking age, about three to six. The research instrument counts sounds; this does not, and says so."],
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

  return (
    <>
      <a href="#top" className="skip-link">
        Skip to content
      </a>
      <Nav />

      <main id="top" className="mx-auto max-w-[1120px] px-5 pb-28 sm:px-8">
        {/* 1. Hero: the claim, the tagline, the two numbers, today's day. */}
        <section className="grid gap-10 pt-16 lg:grid-cols-[1.05fr_1fr] lg:items-start">
          <div>
            <p className="eyebrow">A step counter for conversations with your child</p>
            <h1 className="display mt-4 max-w-[16ch] text-5xl leading-[1.02] text-ink sm:text-6xl">
              Your child&apos;s brain is built in the back-and-forth. Volley counts it.
            </h1>
            <p className="mt-6 max-w-[58ch] text-lg leading-relaxed text-ink">
              Counts the back-and-forth between you and your child from the Bee on your wrist, keeps the counts and throws the words
              away, and puts one thing to try tomorrow into your Bee as a reminder.
            </p>
            <p className="mt-4 max-w-[62ch] leading-relaxed text-muted">
              A turn <Info term="turn" /> is one exchange <Info term="exchange" />: you say something, your child answers within five
              seconds, or the other way round. The studies that found this number used a research recorder families cannot buy. The Bee
              is the first wearable a parent already owns that can do it, and the words never leave your computer{" "}
              <Info term="onYourComputer" />.
            </p>
            <p className="mt-4 max-w-[62ch] text-sm leading-relaxed text-muted">
              The two numbers a judge should read first: on {corpus.hours} hours of public parent-child recordings we did not make, the
              rule counted <strong className="text-ink">{corpus.turns.toLocaleString("en-US")} turns</strong> from the human speaker
              labels, <strong className="text-ink">zero</strong> inside any stretch where one person spoke alone{" "}
              <Info term="corpus" />; on the operator&apos;s own Bee, the agreement with a blind hand count is{" "}
              <strong className="text-ink">not yet measured</strong>. The second is scheduled and will be published whichever way it
              comes out; this sentence changes only when it is <Info term="validated" />.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#how" className="primary">
                See how it counts
              </a>
              <a href="#yours" className="secondary">
                Count your own
              </a>
            </div>
          </div>
          <DayView day={today} child={demo.child_name} simulated />
        </section>

        {/* 2. Three figures, each with its study on the i. */}
        <dl className="mt-16 grid gap-6 sm:grid-cols-3">
          {STATS.map((s) => (
            <div key={s.figure} className="border-l-2 border-[var(--accent)] pl-4">
              <dt className="display-sm text-3xl text-ink">
                {s.figure} <Info term={s.term} />
              </dt>
              <dd className="mt-2 text-sm leading-relaxed text-muted">{s.label}</dd>
            </div>
          ))}
        </dl>

        <div className="rule my-20" />

        {/* 3. What, why, how. */}
        <section id="what" className="scroll-mt-24">
          <p className="eyebrow">In one screen</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">What it is, why it exists, how it runs.</h2>
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

        <div className="rule my-20" />

        {/* 4. How it counts, watched. */}
        <section id="how" className="scroll-mt-24">
          <p className="eyebrow">Watch the rule</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">How it counts, in twenty seconds.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            Press play. Each bar is something somebody said; the band after it is the five-second window. The number in the corner is
            the same rule that runs on your computer, counting these bars as they arrive.
          </p>
          <div className="mt-10">
            <WorkedExample />
          </div>
        </section>

        <div className="rule my-20" />

        {/* 5. The day and the week, like steps. */}
        <section id="day" className="scroll-mt-24">
          <p className="eyebrow">Like steps</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">A day, an hour at a time, and one thing for tomorrow.</h2>
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
              <blockquote className="mt-4 border-l-2 border-[var(--accent)] pl-4">
                <p className="leading-relaxed text-ink">
                  {today.best_hour !== null
                    ? `Your best hour with ${demo.child_name} was around ${clock(today.best_hour)}, with ${Math.max(...today.hours.map((h) => h.turns))} turns. Keep that one exactly as it is.`
                    : "A first day counted. Wear the band tomorrow and the hours that matter will show."}
                </p>
                <footer className="mt-2 text-xs text-faint">the template layer, from the fact: best hour</footer>
              </blockquote>
              <p className="mt-4 text-sm leading-relaxed text-muted">
                Rules pick the fact; Claude on Bedrock phrases it; every digit must come from the fact or the template is used{" "}
                <Info term="bedrock" />. With your consent the sentence goes into your Bee as a reminder at that hour.
              </p>
            </div>
          </div>
        </section>

        <div className="rule my-20" />

        {/* 6. What it will never say. */}
        <section id="never" className="scroll-mt-24">
          <p className="eyebrow">Said in the same size as the numbers</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">What it will never say.</h2>
          <div className="mt-10 grid gap-x-10 gap-y-8 md:grid-cols-2">
            {NEVER.map((n) => (
              <div key={n.head} className="border-t border-line pt-5">
                <p className="font-semibold text-ink">{n.head}</p>
                <p className="mt-2 leading-relaxed text-muted">{n.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="rule my-20" />

        {/* 7. Privacy, demonstrated. */}
        <section id="privacy" className="scroll-mt-24">
          <p className="eyebrow">Privacy</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">A transcript, refused by the server, while you watch.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            The API accepts counts and drops every field it does not know at the door. That is a claim until it is pressed. What the
            Bee itself keeps is Amazon&apos;s promise, in its own privacy notice, and not ours to restate.
          </p>
          <div className="mt-10">
            <PrivacyProof />
          </div>
        </section>

        <div className="rule my-20" />

        {/* 8. Your Bee, in ten minutes. */}
        <section id="yours" className="scroll-mt-24">
          <p className="eyebrow">Your Bee</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">Your own day, in ten minutes.</h2>
          <ol className="mt-10 grid gap-4 md:grid-cols-2">
            {STEPS.map((s, i) => (
              <li key={s.title} className="card p-5">
                <div className="flex items-baseline gap-3">
                  <span className="display-sm text-2xl text-[var(--accent)]">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-ink">
                      {s.title} {s.term && <Info term={s.term} />}
                    </p>
                    <pre className="mt-2 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                      {s.body}
                    </pre>
                  </div>
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-6 max-w-[66ch] text-sm leading-relaxed text-muted">
            Recording other people is your responsibility under local law; the setup screen says so before anything runs. The child
            wears nothing. Your child&apos;s words never leave your computer.
          </p>
        </section>

        <div className="rule my-20" />

        {/* 9. Bring your own data. */}
        <section id="byo" className="scroll-mt-24">
          <p className="eyebrow">Bring your own data</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">Three doors, each for someone.</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="card p-6">
              <p className="font-semibold text-ink">Parents: your Bee, on your computer</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">The steps above. The only door that reads a transcript, and it reads it where you are; the counts, and nothing else, can go to a page that is yours.</p>
            </div>
            <div className="card p-6">
              <p className="font-semibold text-ink">Anyone curious: a Bee export, in this tab</p>
              <p className="mt-2 text-sm leading-relaxed text-muted">Drop a file below. It is counted in your browser and uploaded nowhere.</p>
            </div>
            <div className="card p-6">
              <p className="font-semibold text-ink">
                Developers: an API key <Info term="apiKey" />
              </p>
              <pre className="mt-2 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
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

        <div className="rule my-20" />

        {/* 10. Alexa+. */}
        <section id="alexa" className="scroll-mt-24">
          <p className="eyebrow">Alexa+</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">Ask it out loud, and it cannot repeat a word.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            An MCP server <Info term="mcp" />, spec 2025-11-25 over Streamable HTTP, with seven tools and an Agent Skill{" "}
            <Info term="skill" />. It can say how the talking went today, what to try tomorrow, the week&apos;s direction and the best
            hour; it can record a day of counts; and it explains the rule. It has no tool that returns speech, because the server never
            receives any, and a test walks every tool to prove it.
          </p>
          <div className="mt-10">
            <McpProof />
          </div>
        </section>

        <div className="rule my-20" />

        {/* 10b. Impact: who has paid for this count already, and what changes at fifty dollars. */}
        <section id="impact" className="scroll-mt-24">
          <p className="eyebrow">Beyond this hackathon</p>
          <h2 className="display-sm mt-3 max-w-[24ch] text-3xl text-ink sm:text-4xl">Cities have paid for this count. Parents have never been able to buy it.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            The case for who this serves, in the order a sceptic would ask it, with the study behind every sentence on its i. What
            it does not claim is at the end, in the same type.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            {IMPACT.map((c) => (
              <div key={c.title} className="card min-w-0 p-6">
                <p className="font-semibold text-ink">
                  {c.title} <Info term={c.term} />
                </p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{c.body}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 max-w-[66ch] text-sm leading-relaxed text-muted">
            Not claimed: that Volley has changed any child&apos;s outcome; that its count equals the research recorder&apos;s; that
            a parent should aim for any number. One family has worn it. Every study above is resolved on PubMed or Crossref in the
            repository&apos;s citations file, with what it showed and what it did not, and a test refuses any citation in this page
            that is not there.
          </p>
        </section>

        <div className="rule my-20" />

        {/* 11. Evidence: refused first, then baselines, then agreement. */}
        <section id="evidence" className="scroll-mt-24">
          <p className="eyebrow">Evidence</p>
          <h2 className="display-sm mt-3 max-w-[24ch] text-3xl text-ink sm:text-4xl">What it refused to count, what it beat, and how close it is to a person.</h2>
          <p className="mt-4 max-w-[66ch] leading-relaxed text-muted">
            Written for somebody who came here to find the weak point. Measured here, read from the literature, and not done yet are
            kept apart on purpose.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="card min-w-0 p-6">
              <p className="eyebrow">Refusals, measured here</p>
              <p className="mt-3 leading-relaxed text-muted">
                On the public corpus, <strong className="text-ink">{corpus.turns_inside_them} turns</strong> inside its{" "}
                {corpus.single_speaker_stretches} stretches of a minute or more where one person spoke alone{" "}
                <Info term="corpus" />. On the device: zero on an adult-only conversation, on a podcast playing to an empty room, and
                on silence. <strong className="text-ink">Not yet measured</strong>; scheduled, and published whichever way it comes
                out.
              </p>
            </div>
            <div className="card min-w-0 p-6">
              <p className="eyebrow">Against the obvious alternatives</p>
              <p className="mt-3 leading-relaxed text-muted">
                Adult word count, which the last consumer device sold: across the corpus&apos;s {corpus.sessions} sessions it ranks
                with turns at Spearman <strong className="text-ink">{corpus.spearman_adult_words_vs_turns}</strong>, and two sessions
                with the same adult words carried turns{" "}
                <strong className="text-ink">{corpus.same_words_different_turns?.ratio} times</strong> apart{" "}
                <Info term="wordsVsTurns" />. A speaker-change count with no window agreed with the rule on{" "}
                {corpus.alternations_within_window_percent} percent of alternations, because the corpus&apos;s aligned timing has no
                gaps <Info term="windowOnCorpus" />; the window&apos;s work is in a day, not a lab session.
              </p>
            </div>
            <div className="card min-w-0 border-[var(--warn)] p-6">
              <p className="eyebrow text-[var(--warn)]">Nobody has done yet</p>
              <p className="mt-3 leading-relaxed text-muted">
                A child under three on this device; a family other than the operator&apos;s; the Bee against a LENA recorder on the
                same afternoon, which is the study to run first with a grant.
              </p>
            </div>
          </div>
          {/*
            The Bee labels every speaker Unknown. This is the answer, measured
            on families the model never saw, with the naive alternative beside it.
          */}
          <div id="blind" className="card mt-6 p-6 sm:p-8">
            <p className="eyebrow">No speaker labels, measured on families it never saw</p>
            <p className="mt-3 max-w-[70ch] leading-relaxed text-muted">
              The Bee labels every speaker &ldquo;Unknown&rdquo;, so Volley reads who is the child and who the adult from the words and
              the pauses, with a model trained on CHILDES and scored only on families it was not trained on. Across{" "}
              {blind.sessions} sessions it counted <strong className="text-ink">{blind.turns_blind.toLocaleString("en-US")} turns</strong>{" "}
              against {blind.turns_true.toLocaleString("en-US")} true ({blind.total_error_pct} percent); the median session was within{" "}
              <strong className="text-ink">{blind.median_abs_session_error_pct} percent</strong>, and turns per hour tracked the truth at a
              correlation of <strong className="text-ink">{blind.correlation_per_hour}</strong>. Treating every pause as a change of speaker
              missed by {Math.abs(blind.naive_total_error_pct)} percent. Each utterance&apos;s role was right{" "}
              {blind.role_accuracy_pct} percent of the time, so a single exchange can be misread; a day, a week and a trend are what it is
              for.
            </p>
            <p className="mt-4 max-w-[70ch] leading-relaxed text-muted">
              <span className="font-semibold text-ink">On the Bee itself.</span> A real mother-and-child conversation from the same
              corpus, voiced by Amazon Polly with an adult and a child voice at its original timing, played to the band for{" "}
              {Math.round(device.played_seconds)} seconds, no person in the room. The Bee wrote {device.utterances_bee} utterances for{" "}
              {device.utterances_played} played and kept <strong className="text-ink">{device.turns_bee_with_true_roles} of{" "}
              {device.turns_true} turns</strong>: its segmentation loses none. Volley, with no labels and a model that never saw this
              family, counted <strong className="text-ink">{device.turns_blind}</strong> ({device.blind_error_pct} percent), with{" "}
              {device.role_accuracy_pct} percent of lines given the right speaker. One session; the corpus says how much one session
              varies.
            </p>
          </div>
          <div className="card mt-6 p-6 sm:p-8">
            <p className="eyebrow">On recordings we did not make, measured 2026-09-30</p>
            <p className="mt-3 max-w-[70ch] leading-relaxed text-muted">
              The CHILDES Gleason corpus: {corpus.sessions} sessions, {corpus.hours} hours, 24 children aged 2;1 to 5;2 with their
              mother, with their father and at the family dinner table, human speaker labels, aligned timing. The rule counted{" "}
              {corpus.turns.toLocaleString("en-US")} turns: {corpus.turns_per_hour_min} to {corpus.turns_per_hour_max} an hour by
              session, median {corpus.turns_per_hour_median}. Dinner {corpus.by_situation.Dinner.turns_per_hour}, with the mother{" "}
              {corpus.by_situation.Mother.turns_per_hour}, with the father {corpus.by_situation.Father.turns_per_hour} an hour.
              Children under three, {corpus.under_36_months.turns_per_hour} an hour across {corpus.under_36_months.sessions} sessions;
              three and over, {corpus.from_36_months.turns_per_hour} across {corpus.from_36_months.sessions}. A fifty-second window
              instead of five changed the count to {corpus.turns_with_50s_window.toLocaleString("en-US")}. {corpus.files_without_time_marks}{" "}
              files had no timing and were skipped by name.
            </p>
            <p className="mt-3 max-w-[70ch] text-sm leading-relaxed text-muted">
              What this shows: the rule, the roles and the alternation logic hold on human-labelled recordings at twenty times the
              published daylong target, which is what half an hour of a parent&apos;s full attention looks like. What it does not show:
              the window, because the aligner&apos;s timing is contiguous; the device&apos;s transcription of a two-year-old, because
              these are human transcripts; and any family&apos;s day. The hand count on the operator&apos;s own Bee is the number
              that answers the last two <Info term="harness" />. <code className="font-mono text-xs">volley verify</code> recomputes
              every figure in this paragraph from the committed results, and from the corpus itself where it is present.
            </p>
          </div>
          <div className="card mt-6 p-6 sm:p-8">
            <p className="eyebrow">Read from the literature</p>
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
          </div>
        </section>

        <div className="rule my-20" />

        {/* 12. Developers. */}
        <section id="developers" className="scroll-mt-24">
          <p className="eyebrow">Developers</p>
          <h2 className="display-sm mt-3 max-w-[22ch] text-3xl text-ink sm:text-4xl">Everything here is a test you can run.</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Run it</p>
              <pre className="mt-3 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
                {"python -m venv .venv\n.venv/Scripts/pip install -e packages/serve-return[dev] -e apps/ingest[dev] -e apps/server[dev]\n.venv/Scripts/python -m pytest packages apps    # every test\ncd apps/web && npm install && npm test && npm run dev"}
              </pre>
            </div>
            <div className="card min-w-0 p-6">
              <p className="font-semibold text-ink">Use the counter</p>
              <pre className="mt-3 overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-3 font-mono text-[12px] leading-relaxed text-ink">
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

        <div className="rule my-20" />

        {/* 13. Questions a parent asks. */}
        <section id="questions" className="scroll-mt-24">
          <p className="eyebrow">Questions a parent asks</p>
          <div className="mt-8 grid gap-x-10 gap-y-6 md:grid-cols-2">
            {FAQ.map(([q, a]) => (
              <div key={q} className="border-t border-line pt-4">
                <p className="font-semibold text-ink">{q}</p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{a}</p>
              </div>
            ))}
          </div>
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
