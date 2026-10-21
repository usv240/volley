"use client";

import { useEffect, useId, useState } from "react";
import { Info } from "./Info";
import { FALLBACK_LABEL, noteSourceLabel, parseNote, type Note } from "./note";

/**
 * Tomorrow's note for the simulated family, read live from
 * GET /v1/households/{id}/note: the same sentence the coach page shows,
 * so one day never has two tomorrows. Rules pick the fact; Claude on
 * Bedrock phrases it; the card says which layer wrote what it shows.
 *
 * It fails quietly, like the plan card: while the note is on its way the
 * card says so; if the service has no note, or cannot be reached, the
 * template sentence for the same day is shown and labelled as the
 * fallback it is.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";

type State = { kind: "loading" } | { kind: "ok"; note: Note } | { kind: "fallback" };

export function TomorrowCard({ id, fallback, className = "" }: { id: string; fallback: string; className?: string }) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const headingId = useId();

  useEffect(() => {
    const ctl = new AbortController();
    setState({ kind: "loading" });
    (async () => {
      try {
        const res = await fetch(`${API_URL}/v1/households/${encodeURIComponent(id)}/note`, { signal: ctl.signal });
        if (!res.ok) return setState({ kind: "fallback" });
        const note = parseNote(await res.json());
        setState(note ? { kind: "ok", note } : { kind: "fallback" });
      } catch {
        if (!ctl.signal.aborted) setState({ kind: "fallback" });
      }
    })();
    return () => ctl.abort();
  }, [id]);

  return (
    <section className={`card p-6 sm:p-8 ${className}`} aria-labelledby={headingId} aria-busy={state.kind === "loading"}>
      <h3 id={headingId} className="font-semibold text-ink">
        Tomorrow, written from the latest day&apos;s counts
      </h3>
      {state.kind === "loading" && (
        <p className="mt-3 text-sm text-muted" role="status">
          Reading the note from the service.
        </p>
      )}
      {state.kind === "ok" && (
        <blockquote className="mt-4 border-l border-[var(--line-strong)] pl-4">
          <p className="leading-relaxed text-ink">{state.note.text}</p>
          <footer className="mt-2 text-xs text-faint">{noteSourceLabel(state.note.source, state.note.fact.kind)}</footer>
        </blockquote>
      )}
      {state.kind === "fallback" && (
        <blockquote className="mt-4 border-l border-[var(--line-strong)] pl-4">
          <p className="leading-relaxed text-ink">{fallback}</p>
          <footer className="mt-2 text-xs text-faint">{FALLBACK_LABEL}</footer>
        </blockquote>
      )}
      <p className="mt-4 text-sm leading-relaxed text-muted">
        Rules pick the fact; Claude on Bedrock phrases it; every digit must come from the fact or the template is used{" "}
        <Info term="bedrock" />. With your consent the sentence goes into your Bee as a reminder at that hour.
      </p>
    </section>
  );
}
