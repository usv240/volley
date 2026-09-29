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
  { title: "Install Volley", body: "pip install volley", live: true },
  { title: "Say who is who, then count the day", body: "volley setup --parent <label> --child <label> --child-name Asha --tz 5.5\nvolley today", live: true },
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
              The two numbers a judge should read first: on 33 hours of public parent-child recordings we did not make, the count&apos;s
              agreement with the human speaker labels is <strong className="text-ink">not yet measured</strong>; on the operator&apos;s
              own Bee, the agreement with a blind hand count is <strong className="text-ink">not yet measured</strong>. Both are
              scheduled, both will be published whichever way they come out, and this sentence changes only when they are{" "}
              <Info term="validated" />.
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
              <p className="mt-2 text-sm leading-relaxed text-muted">The five steps above. The only door that reads a transcript, and it reads it where you are.</p>
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
                Zero turns on an adult-only conversation, on a podcast playing to an empty room, and on silence; zero in the
                single-speaker stretches of the public corpus. <strong className="text-ink">Not yet measured.</strong> Scheduled, and
                published whichever way it comes out.
              </p>
            </div>
            <div className="card min-w-0 p-6">
              <p className="eyebrow">Against the obvious alternatives</p>
              <p className="mt-3 leading-relaxed text-muted">
                Word count, which the last consumer device sold and which the studies found stops predicting once income is accounted
                for; and a naive speaker-change count with no window. Both on the same recordings as the rule.{" "}
                <strong className="text-ink">Not yet measured.</strong>
              </p>
            </div>
            <div className="card min-w-0 border-[var(--warn)] p-6">
              <p className="eyebrow text-[var(--warn)]">Nobody has done yet</p>
              <p className="mt-3 leading-relaxed text-muted">
                A child under three on this device; a family other than the operator&apos;s; the Bee against a LENA recorder on the
                same afternoon, which is the study to run first with a grant. And one practitioner&apos;s sentence: nobody has said
                one yet.
              </p>
            </div>
          </div>
          <div className="card mt-6 p-6 sm:p-8">
            <p className="eyebrow">Read from the literature</p>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted">
              <li>Gilkerson J et al. Language Experience in the Second Year of Life and Language Outcomes in Late Childhood. Pediatrics 2018. PMID 30201624. Three authors work for the LENA Foundation.</li>
              <li>Romeo RR et al. Beyond the 30-Million-Word Gap. Psychological Science 2018. PMID 29442613.</li>
              <li>Ferjan Ramirez N, Lytle SR, Kuhl PK. Parent coaching increases conversational turns and advances infant language development. PNAS 2020. PMID 32015127.</li>
              <li>Huber E et al. Parent coaching from 6 to 18 months improves child language outcomes through 30 months of age. Developmental Science 2023. PMID 36999222.</li>
              <li>Christakis DA et al. Audible television and decreased adult words, infant vocalizations, and conversational turns. Archives of Pediatrics and Adolescent Medicine 2009. PMID 19487612.</li>
              <li>Harvard University Center on the Developing Child. Serve and Return.</li>
              <li>Playlogue (Kalanadhabhatta et al., IMWUT 2024), from CHILDES, for the corpus <Info term="corpus" /> <Info term="playlogueLicence" />.</li>
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
