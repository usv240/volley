"use client";

import { useEffect, useState } from "react";
import { DayView, clock, type Day } from "./DayView";
import { Info } from "./Info";

/**
 * A parent's own days, read with their key from this browser.
 *
 * The key arrives once, in the fragment of the link `volley connect`
 * printed (`/mine/#h=<household>&k=<key>`). A fragment is never sent to
 * a server, so the site, its CDN and its logs never see it. On first
 * load the component moves it into local storage and clears the
 * address bar, so a copied link afterwards carries nothing. Every
 * request from here on goes straight to the API with the key in a
 * header, the same way the command line posts counts.
 *
 * The page has three honest states: no key in this browser, a key but
 * no days yet, and days. Each says what to run next. Two buttons
 * remove things: one forgets the key here, one deletes the household
 * and every count on the service, and that one asks first.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";
const KEY = "volley-mine";

interface Creds {
  id: string;
  key: string;
}

interface Household {
  household_id: string;
  name: string;
  child_name: string | null;
  created?: string;
}

interface Week {
  days: { date: string; turns: number; best_hour: number | null }[];
  direction: "up" | "down" | "level";
  best_day: string | null;
  target_turns_per_hour: number;
}

interface Note {
  text: string;
  source: "bedrock" | "template";
  fact: { kind: string; hour: number | null; value: number | null };
}

function readCreds(): Creds | null {
  const hash = window.location.hash.replace(/^#/, "");
  if (hash) {
    const params = new URLSearchParams(hash);
    const id = params.get("h");
    const key = params.get("k");
    if (id && key) {
      const creds = { id, key };
      localStorage.setItem(KEY, JSON.stringify(creds));
      history.replaceState(null, "", window.location.pathname);
      return creds;
    }
  }
  try {
    const stored = localStorage.getItem(KEY);
    return stored ? (JSON.parse(stored) as Creds) : null;
  } catch {
    return null;
  }
}

export function Mine() {
  const [creds, setCreds] = useState<Creds | null | undefined>(undefined);
  const [household, setHousehold] = useState<Household | null>(null);
  const [days, setDays] = useState<Day[]>([]);
  const [week, setWeek] = useState<Week | null>(null);
  const [note, setNote] = useState<Note | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setCreds(readCreds());
    // A link pasted into a tab already on this page changes only the
    // fragment, which is not a navigation; read it then too.
    const onHash = () => setCreds(readCreds());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    if (!creds) return;
    const headers = { "x-api-key": creds.key };
    const base = `${API_URL}/v1/households/${creds.id}`;
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError(null);
      try {
        const h = await fetch(base, { headers });
        if (h.status === 401) throw new Error("the key in this browser is not this household's key");
        if (h.status === 404) throw new Error("this household no longer exists on the service");
        if (!h.ok) throw new Error(`the service answered ${h.status}`);
        const d = await fetch(`${base}/days`, { headers });
        const w = await fetch(`${base}/week`, { headers });
        const dayRows = ((await d.json()) as { days: Day[] }).days;
        if (cancelled) return;
        setHousehold((await h.json()) as Household);
        setDays(dayRows);
        setWeek((await w.json()) as Week);
        if (dayRows.length) {
          const n = await fetch(`${base}/note`, { headers });
          if (n.ok && !cancelled) setNote((await n.json()) as Note);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [creds]);

  const forget = () => {
    localStorage.removeItem(KEY);
    setCreds(null);
    setHousehold(null);
    setDays([]);
    setWeek(null);
    setNote(null);
  };

  const remove = async () => {
    if (!creds) return;
    if (!window.confirm("Delete this household and every count on the service? The Bee itself is not touched.")) return;
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/v1/households/${creds.id}`, { method: "DELETE", headers: { "x-api-key": creds.key } });
      if (!res.ok) throw new Error(`the service answered ${res.status}`);
      forget();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  if (creds === undefined) {
    return <p className="text-muted">Looking in this browser for a key.</p>;
  }

  if (creds === null) {
    return (
      <section>
        <p className="eyebrow">Mine</p>
        <h1 className="display mt-4 max-w-[16ch] text-4xl leading-[1.05] text-ink sm:text-5xl">No household in this browser yet.</h1>
        <p className="mt-6 max-w-[60ch] leading-relaxed text-muted">
          This page shows one household&apos;s counts, read with its key <Info term="mine" />. On the computer where your Bee is signed
          in, after the steps on the front page:
        </p>
        <pre className="mt-6 max-w-[60ch] overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-4 font-mono text-[13px] leading-relaxed text-ink">
          {"volley connect\nvolley today"}
        </pre>
        <p className="mt-4 max-w-[60ch] text-sm leading-relaxed text-muted">
          <code className="font-mono text-xs">connect</code> prints a link ending in this page; open it here and the key stays in this
          browser. The words of the transcript never make the trip; only counts do, and the privacy section on the front page lets you
          watch the service refuse anything else.
        </p>
      </section>
    );
  }

  const latest = days.length ? days[days.length - 1] : null;
  const child = household?.child_name ?? null;
  const weekMax = week ? Math.max(1, ...week.days.map((d) => d.turns)) : 1;

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Mine</p>
          <h1 className="display mt-4 max-w-[18ch] text-4xl leading-[1.05] text-ink sm:text-5xl">
            {household ? household.name : "Your household"}
            {child ? `, with ${child}` : ""}
          </h1>
          <p className="mt-3 text-sm text-muted">
            Read from the service with the key in this browser <Info term="mine" />
            {busy ? ", fetching" : ""}.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="ghost" onClick={forget}>
            Forget this browser
          </button>
          <button type="button" className="ghost" onClick={() => void remove()} disabled={busy}>
            Delete everything
          </button>
        </div>
      </div>

      {error && (
        <p className="mt-6 rounded-lg border border-line bg-[var(--raised)] p-4 text-sm text-ink" role="alert">
          {error}. If the household was deleted, forget this browser; otherwise run <code className="font-mono text-xs">volley connect --again</code>.
        </p>
      )}

      {!error && !busy && !latest && (
        <div className="card mt-10 p-6 sm:p-8">
          <p className="eyebrow">Connected, nothing counted yet</p>
          <p className="mt-3 max-w-[60ch] leading-relaxed text-muted">
            The household exists and holds no days. Wear the Bee, then on the computer where it is signed in:
          </p>
          <pre className="mt-4 max-w-[60ch] overflow-x-auto rounded-lg border border-line bg-[var(--raised)] p-4 font-mono text-[13px] leading-relaxed text-ink">
            volley today
          </pre>
        </div>
      )}

      {latest && (
        <div className="mt-10">
          <DayView day={latest} child={child} simulated={false} label="Your own day, from your Bee" />
        </div>
      )}

      {latest && week && (
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="card p-6 sm:p-8">
            <p className="eyebrow">
              {week.days.length === 1 ? "One day so far" : `${week.days.length} days`}, going {week.direction}
            </p>
            <ul className="mt-4 space-y-2" aria-label="Turns per day">
              {week.days.map((d) => (
                <li key={d.date} className="flex items-center gap-3 text-sm">
                  <span className="w-24 text-faint">{d.date.slice(5)}</span>
                  <span className="ew-track flex-1">
                    <span className="ew-bar" style={{ width: `${Math.round((100 * d.turns) / weekMax)}%` }} />
                  </span>
                  <span className="w-12 text-right text-ink">{d.turns}</span>
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-muted">
              Best day {week.best_day ?? "none yet"}
              {latest.best_hour !== null ? `; today's best hour ${clock(latest.best_hour)}` : ""}. The published target{" "}
              <Info term="target" /> is {week.target_turns_per_hour} an hour; Volley shows it and sets none of its own{" "}
              <Info term="noPercentile" />.
            </p>
          </div>
          <div className="card p-6 sm:p-8">
            <p className="eyebrow">Tomorrow, written from today&apos;s counts</p>
            {note ? (
              <blockquote className="mt-4 border-l-2 border-[var(--accent)] pl-4">
                <p className="leading-relaxed text-ink">{note.text}</p>
                <footer className="mt-2 text-xs text-faint">
                  the {note.source} layer, from the fact: {note.fact.kind.replace(/_/g, " ")}
                </footer>
              </blockquote>
            ) : (
              <p className="mt-4 text-sm text-muted">No note yet.</p>
            )}
            <p className="mt-4 text-sm leading-relaxed text-muted">
              The same sentence <code className="font-mono text-xs">volley today</code> printed, and, with your consent, placed in your
              Bee as a reminder <Info term="bedrock" />.
            </p>
          </div>
        </div>
      )}

      <p className="mt-10 max-w-[66ch] text-sm leading-relaxed text-muted">
        Nothing on this page is stored anywhere but this browser and the household&apos;s own rows on the service, which hold counts
        and the two names you chose <Info term="household" />. Delete everything removes those rows; the Bee&apos;s own record is
        Bee&apos;s, deleted in its app.
      </p>
    </section>
  );
}
