"use client";

import { useEffect, useId, useState } from "react";
import { Info } from "./Info";
import { parsePlan, planFactsLine, planLineLabels, planSourceLabel, type Plan } from "./plan";

/**
 * This week's plan: three lines a home visitor would write from the
 * week's counts. Keep the best hour, one idea for the quiet hour, one
 * for the weekend. The rules pick the hours; Claude on Bedrock writes
 * the lines behind the same number gate as the note, and a template is
 * the floor. The card says which one wrote what it shows.
 *
 * It reads the plan with the same header as the days (a key for the
 * owner, a share for a coach, nothing for the simulated family), and
 * fails quietly: no days yet, or the service out of reach, is one plain
 * sentence, never an alarm.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";

type State = { kind: "loading" } | { kind: "ok"; plan: Plan } | { kind: "none" } | { kind: "error" };

export function PlanCard({
  id,
  header,
  secret,
  coach = false,
  simulated,
  className = "",
}: {
  id: string;
  /** "x-api-key" for the owner, "x-share-token" for a coach; omitted for the simulated family. */
  header?: string;
  secret?: string;
  coach?: boolean;
  /** Mark the card as the simulated family's before the plan arrives; the service's own flag also counts. */
  simulated?: boolean;
  className?: string;
}) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const headingId = useId();

  useEffect(() => {
    const ctl = new AbortController();
    const headers: Record<string, string> = header && secret ? { [header]: secret } : {};
    setState({ kind: "loading" });
    (async () => {
      try {
        const res = await fetch(`${API_URL}/v1/households/${encodeURIComponent(id)}/plan`, { headers, signal: ctl.signal });
        if (res.status === 404) return setState({ kind: "none" });
        if (!res.ok) return setState({ kind: "error" });
        const plan = parsePlan(await res.json());
        setState(plan ? { kind: "ok", plan } : { kind: "error" });
      } catch {
        if (!ctl.signal.aborted) setState({ kind: "error" });
      }
    })();
    return () => ctl.abort();
  }, [id, header, secret]);

  const plan = state.kind === "ok" ? state.plan : null;
  const isSimulated = simulated || plan?.simulated;
  // A coach reads the plan as the family does: it is addressed to the
  // parent, and its imperatives do not survive a third-person retelling.
  const lines = plan ? plan.lines : [];
  const labels = plan ? planLineLabels(plan.facts, lines.length) : [];

  return (
    <section className={`card p-6 sm:p-8 ${className}`} aria-labelledby={headingId} aria-busy={state.kind === "loading"}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <h3 id={headingId} className="font-semibold text-ink">
          This week&apos;s plan
        </h3>
        {isSimulated && <span className="coach-pill">The simulated family</span>}
      </div>

      {state.kind === "loading" && (
        <p className="mt-3 text-sm text-muted" role="status">
          Reading the week&apos;s plan from the service.
        </p>
      )}
      {state.kind === "none" && (
        <p className="mt-3 max-w-[60ch] text-sm leading-relaxed text-muted">
          No plan yet. It is written from days with the child there, and none are counted.
        </p>
      )}
      {state.kind === "error" && (
        <p className="mt-3 max-w-[60ch] text-sm leading-relaxed text-muted">
          The plan could not be read from the service just now. The counts are untouched; reload the page to try again.
        </p>
      )}

      {plan && (
        <>
          <p className="mt-2 text-sm text-muted tabular-nums">{planFactsLine(plan.facts)}</p>
          <ol className="plan-lines mt-6 grid gap-6 lg:grid-cols-3 lg:gap-8">
            {lines.map((line, i) => (
              <li key={i} className="min-w-0">
                <p className="text-sm font-semibold text-muted tabular-nums">{labels[i]}</p>
                <p className="mt-2 max-w-[48ch] leading-relaxed text-ink">{line}</p>
              </li>
            ))}
          </ol>
          <p className="mt-6 border-t border-line pt-4 text-xs leading-relaxed text-faint">
            {planSourceLabel(plan.source)}
            {coach ? "; shown as the family reads it" : ""} <Info term="bedrock" />
          </p>
        </>
      )}
    </section>
  );
}
