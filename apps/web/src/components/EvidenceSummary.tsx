import corpus from "../data/corpus.json";
import blind from "../data/blind.json";
import device from "../data/device.json";
import controls from "../data/controls.json";

/**
 * The evidence, at a glance, before the prose.
 *
 * One row per measurement: what was measured, the result with a small
 * drawing of it, what it means in a sentence, and whether it holds or is
 * a stated weakness. Every figure is read from the committed results the
 * harness wrote (src/data/*.json), never typed in, so this table and the
 * paragraphs folded under it cannot disagree.
 *
 * Verdicts are a word and a mark, never colour alone. The weak rows sit
 * in the same type as the good ones.
 */

type Verdict = "good" | "weak" | "trade";

const VERDICT: Record<Verdict, { word: string; cls: string }> = {
  good: { word: "Holds", cls: "verdict-good" },
  weak: { word: "Weakness", cls: "verdict-weak" },
  trade: { word: "Trade-off", cls: "verdict-trade" },
};

function Mark({ kind }: { kind: Verdict }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      {kind === "good" ? (
        <path d="M2.5 6.25 5 8.5l4.5-5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      ) : kind === "weak" ? (
        <path d="M6 2.5v4.25M6 9.25v.25" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      ) : (
        <path d="M2 4.5h8M2 7.5h8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      )}
    </svg>
  );
}

function VerdictPill({ kind, word }: { kind: Verdict; word?: string }) {
  const v = VERDICT[kind];
  return (
    <span className={`verdict ${v.cls}`}>
      <Mark kind={kind} />
      {word ?? v.word}
    </span>
  );
}

/** One dot per session; filled when its count was within 20 percent of the truth. */
function SessionDots({ within, total }: { within: number; total: number }) {
  return (
    <div className="mt-3">
      <div className="grid w-fit grid-cols-[repeat(27,8px)] gap-[3px]" role="img" aria-label={`${within} of ${total} sessions within 20 percent`}>
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full"
            style={
              i < within
                ? { background: "var(--chart-mark)" }
                : { boxShadow: "inset 0 0 0 1.5px var(--line-strong)" }
            }
          />
        ))}
      </div>
      <p className="mt-1.5 text-xs text-muted">One dot per session; filled when within 20 percent.</p>
    </div>
  );
}

/** Counts on one shared scale, so a control reads against the real conversation. */
function CountBars({ rows, max }: { rows: { label: string; value: number; real?: boolean }[]; max: number }) {
  return (
    <ul className="mt-3 space-y-1.5" aria-label="Turns counted, on one scale">
      {rows.map((r) => (
        <li key={r.label} className="grid grid-cols-[7.5rem_minmax(0,1fr)_2rem] items-center gap-2 text-xs">
          <span className="text-muted">{r.label}</span>
          <span className="block h-2 rounded-full bg-[var(--chart-track)]">
            {r.value > 0 && (
              <span
                className="block h-2 rounded-full"
                style={{ width: `${(100 * r.value) / max}%`, background: r.real ? "var(--chart-mark)" : "var(--warn)" }}
              />
            )}
          </span>
          <span className="text-right text-ink tabular-nums">{r.value}</span>
        </li>
      ))}
    </ul>
  );
}

function Row({
  what,
  sub,
  figure,
  unit,
  second,
  chart,
  meaning,
  verdict,
  verdictWord,
}: {
  what: string;
  sub: React.ReactNode;
  figure: string;
  unit: string;
  second: React.ReactNode;
  chart?: React.ReactNode;
  meaning: string;
  verdict: Verdict;
  verdictWord?: string;
}) {
  return (
    <li className="ev-row">
      <div data-e="what">
        <p className="font-semibold leading-snug text-ink">{what}</p>
        <p className="mt-1 text-sm leading-snug text-muted">{sub}</p>
      </div>
      <div data-e="fig" className="min-w-0">
        {figure && (
          <p className="flex flex-wrap items-baseline gap-x-2">
            <span className="display-sm text-[1.75rem] leading-none text-ink tabular-nums">{figure}</span>
            <span className="text-sm text-muted">{unit}</span>
          </p>
        )}
        <p className={`${figure ? "mt-1.5 text-muted" : "text-ink"} text-sm leading-snug`}>{second}</p>
        {chart}
      </div>
      <p data-e="mean" className="text-[15px] leading-relaxed text-ink">
        {meaning}
      </p>
      <div data-e="verdict">
        <VerdictPill kind={verdict} word={verdictWord} />
      </div>
    </li>
  );
}

export function EvidenceSummary() {
  const realMax = Math.max(controls.real_turns_same_length, controls.with_child_real);
  return (
    <div className="card mt-10 px-5 py-4 sm:px-8 sm:py-6">
      <div className="ev-row ev-head" aria-hidden="true">
        <span data-e="what">Measured</span>
        <span data-e="fig">Result</span>
        <span data-e="mean">What it means</span>
        <span data-e="verdict">Verdict</span>
      </div>
      <ul aria-label="The measured results">
        <Row
          what="Human-labelled recordings"
          sub={`${corpus.sessions} sessions, ${corpus.hours} hours of public parent-child recordings we did not make`}
          figure={corpus.turns.toLocaleString("en-US")}
          unit="turns counted from the human labels"
          second={`${corpus.turns_inside_them} turns inside ${corpus.single_speaker_stretches} stretches where one person spoke alone`}
          meaning="Told who is speaking, the rule counts the back-and-forth and counts nothing while one person talks alone."
          verdict="good"
        />
        <Row
          what="No speaker labels, families it never saw"
          sub={`${blind.sessions} sessions; who is the child is read from the words and the pauses, as the Bee requires`}
          figure={`${blind.median_abs_session_error_pct}%`}
          unit="median error per session"
          second={`${blind.sessions_within_20pct} of ${blind.sessions} sessions within 20 percent of the true count`}
          chart={<SessionDots within={blind.sessions_within_20pct} total={blind.sessions} />}
          meaning="This is the count a parent actually gets, since the Bee labels everyone Unknown: close over a session, not exact for a single exchange."
          verdict="good"
        />
        <Row
          what="On the Bee itself"
          sub={`One real conversation played to the band for ${Math.round(device.played_seconds)} seconds, no person in the room`}
          figure={`${device.turns_blind} of ${device.turns_true}`}
          unit="turns, with no labels"
          second={`${device.blind_error_pct} percent, on one session`}
          chart={
            <div className="mt-3 max-w-[18rem]" role="img" aria-label={`${device.turns_blind} of ${device.turns_true} turns`}>
              <span className="block h-2 rounded-full bg-[var(--chart-track)]">
                <span
                  className="block h-2 rounded-full bg-[var(--chart-mark)]"
                  style={{ width: `${(100 * device.turns_blind) / device.turns_true}%` }}
                />
              </span>
            </div>
          }
          meaning="The whole chain works on the device and runs a little low. One session is a check, not a study."
          verdict="good"
          verdictWord="Holds, once"
        />
        <Row
          what="Negative controls: no child there"
          sub={`About three minutes each, played to the Bee, against ${controls.real_turns_same_length} turns from a real parent and child of the same length`}
          figure={`${controls.adults_false_turns}`}
          unit="false turns from two adults talking"
          second={`One adult voice ${controls.onevoice_false_turns}, silence ${controls.silence_false_turns}`}
          chart={
            <CountBars
              max={realMax}
              rows={[
                { label: "Parent and child", value: controls.real_turns_same_length, real: true },
                { label: "Two adults", value: controls.adults_false_turns },
                { label: "One adult voice", value: controls.onevoice_false_turns },
                { label: "Silence", value: controls.silence_false_turns },
              ]}
            />
          }
          meaning="Without speaker labels, adults talking to each other look like turns. This is the weak point, stated."
          verdict="weak"
        />
        <Row
          what="The child-present check, opt-in"
          sub={
            <>
              Off by default; on with{" "}
              <code className="font-mono text-[12px] text-ink">
                volley setup <span className="whitespace-nowrap">--only-with-child yes</span>
              </code>
            </>
          }
          figure={`${controls.adults_false_turns} to ${controls.with_child_adults}`}
          unit="false turns from two adults, with the check on"
          second={`One adult voice ${controls.onevoice_false_turns} to ${controls.with_child_onevoice}, and ${controls.with_child_real} of ${controls.with_child_real_every} real turns kept on the Bee. On the corpus, held out by family, it refused ${controls.gate_refused_pct} percent of adults-only stretches and lost ${controls.gate_turns_lost_pct} percent of true turns.`}
          chart={
            <CountBars
              max={realMax}
              rows={[
                { label: "Parent and child", value: controls.with_child_real, real: true },
                { label: "Two adults", value: controls.with_child_adults },
                { label: "One adult voice", value: controls.with_child_onevoice },
              ]}
            />
          }
          meaning="It ends the false turns at a cost in real ones, so the parent chooses which error they would rather have."
          verdict="trade"
        />
        <Row
          what="Not measured yet"
          sub="Said here so nobody has to find it"
          figure=""
          unit=""
          second="A child under three on this device; a family other than the builder's; the Bee beside a LENA recorder on the same afternoon."
          meaning="The last is the study to run first with a grant. Until then the count is checked, not validated."
          verdict="weak"
          verdictWord="Open"
        />
      </ul>
    </div>
  );
}
