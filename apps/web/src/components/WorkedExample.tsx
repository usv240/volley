"use client";

import { useEffect, useRef, useState } from "react";
import { countTurns, type Utterance } from "../count/rule";
import { Info } from "./Info";

/**
 * How it counts, watched.
 *
 * A twenty-second exchange drawn on a time line, adult above, child
 * below, each utterance a bar. Press play and the rule walks the line:
 * after each utterance a five-second window fades out, and when the
 * other person starts inside it the count ticks up. Nothing here is a
 * recording of a child; the bars are placed by hand to show every case
 * the rule has to get right: a quick reply, a reply just outside the
 * window, a monologue that merges, and a gap that ends the exchange.
 *
 * The count shown is computed by the same TypeScript rule the drop zone
 * uses, which is checked against the Python package by a test. So the
 * number in the corner is not decoration; it is the rule running.
 */

const ROLES = { adult: ["adult"], child: ["child"] };

// seconds from the start, who, how long, what kind of thing was said
const SCRIPT: { at: number; who: "adult" | "child"; len: number; kind: string }[] = [
  { at: 0.0, who: "adult", len: 1.6, kind: "a question" },
  { at: 2.4, who: "child", len: 1.0, kind: "an answer, 0.8s later" },
  { at: 3.8, who: "adult", len: 1.2, kind: "a follow-up" },
  { at: 5.2, who: "adult", len: 1.4, kind: "and another, merged into one block" },
  { at: 7.6, who: "child", len: 0.8, kind: "an answer, 1.0s later" },
  { at: 14.4, who: "adult", len: 1.5, kind: "six seconds of silence first: no turn" },
  { at: 16.6, who: "child", len: 1.2, kind: "a reply, 0.7s later" },
  { at: 18.4, who: "adult", len: 1.3, kind: "a reply, 0.6s later" },
];
const TOTAL = 20;

function toUtterances(upTo: number): Utterance[] {
  return SCRIPT.filter((s) => s.at <= upTo).map((s) => ({
    start: 1_790_700_000 + s.at,
    speaker: s.who,
    text: s.kind.startsWith("a question") ? "what is it?" : "words here",
    end: 1_790_700_000 + s.at + s.len,
  }));
}

export function WorkedExample() {
  const [t, setT] = useState<number>(TOTAL);
  const [playing, setPlaying] = useState(false);
  const raf = useRef<number | null>(null);
  const started = useRef(0);

  useEffect(() => {
    if (!playing) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setT(TOTAL);
      setPlaying(false);
      return;
    }
    started.current = performance.now();
    const tick = (now: number) => {
      const s = (now - started.current) / 1000;
      if (s >= TOTAL) {
        setT(TOTAL);
        setPlaying(false);
        return;
      }
      setT(s);
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [playing]);

  const turns = countTurns(toUtterances(t), ROLES);
  const pct = (s: number) => `${(100 * s) / TOTAL}%`;

  return (
    <div className="card p-6 sm:p-8">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="eyebrow">Twenty seconds, counted</p>
        <p className="flex items-baseline gap-2">
          <span className="display text-4xl text-ink" aria-live="polite">
            {turns}
          </span>
          <span className="text-sm text-muted">turns so far</span>
        </p>
      </div>

      <div className="mt-6 space-y-2">
        {(["adult", "child"] as const).map((who) => (
          <div key={who} className="flex items-center gap-3">
            <span className="w-12 text-sm text-muted">{who}</span>
            <div className="relative h-8 flex-1 rounded" style={{ background: "var(--raised)" }}>
              {SCRIPT.filter((s) => s.who === who).map((s, i) => {
                const visible = s.at <= t;
                const windowEnd = s.at + s.len + 5;
                const windowLeft = Math.max(0, Math.min(1, (windowEnd - t) / 5));
                return (
                  <span key={i}>
                    {visible && t < windowEnd && (
                      <span
                        className="absolute top-0 h-8 rounded-r"
                        style={{
                          left: pct(s.at + s.len),
                          width: pct(Math.min(5, TOTAL - s.at - s.len)),
                          background: "var(--accent-soft)",
                          opacity: 0.35 + 0.65 * windowLeft,
                        }}
                        aria-hidden
                      />
                    )}
                    <span
                      className="absolute top-1 h-6 rounded"
                      style={{
                        left: pct(s.at),
                        width: pct(s.len),
                        background: visible ? "var(--chart-mark)" : "var(--line)",
                        opacity: visible ? 1 : 0.5,
                      }}
                      title={s.kind}
                      aria-hidden
                    />
                  </span>
                );
              })}
            </div>
          </div>
        ))}
        <div className="flex items-center gap-3">
          <span className="w-12" />
          <div className="relative h-4 flex-1">
            <span className="absolute top-0 h-4 w-px" style={{ left: pct(t), background: "var(--ink)" }} aria-hidden />
            <span className="absolute left-0 text-[10px] text-faint">0s</span>
            <span className="absolute right-0 text-[10px] text-faint">20s</span>
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="primary"
          onClick={() => {
            setT(0);
            setPlaying(true);
          }}
          disabled={playing}
        >
          {playing ? "Counting..." : "Play"}
        </button>
        <p className="text-sm text-muted">
          The faint band after each bar is the five-second window <Info term="fiveSeconds" />. A reply that starts inside it is a turn;
          two adult bars close together merge into one; six seconds of silence ends the exchange.
        </p>
      </div>

      <ol className="mt-5 grid gap-1 text-sm text-muted sm:grid-cols-2">
        {SCRIPT.map((s, i) => (
          <li key={i} className={s.at <= t ? "text-ink" : ""}>
            {s.at.toFixed(1)}s, {s.who}: {s.kind}
          </li>
        ))}
      </ol>
    </div>
  );
}
