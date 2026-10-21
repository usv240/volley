"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mine } from "./Mine";
import { bestHourNote, type Day } from "./DayView";
import demo from "../data/demo.json";
import {
  addFamily,
  nameFamily,
  parseOpenFamily,
  parseShareLink,
  readFamilies,
  removeFamily,
  shortDate,
  weekDirection,
  writeFamilies,
  type Family,
} from "./coachList";

/**
 * The programme view: every family a home visitor follows, one row each.
 *
 * A parent's share link (`/coach/#h=<household>&s=<share>`) opened here
 * adds that family to a list kept in this browser's local storage, and
 * the address bar is cleared, as on the parent's own page. Each row is
 * read with that family's own share, straight from the API: the last
 * seven days as small bars, the week's direction by the service's rule,
 * the latest day's turns and the note's sentence. Selecting a row opens
 * the single-family view (Mine in coach mode) at `#family=<id>`, so the
 * browser's Back returns to the list where it was.
 *
 * Nothing here writes to the service. "Remove from this browser" edits
 * the local list only, and offers an undo. A family that ended its share
 * gets a 401, which the row says in words rather than as an error.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";
// The service seeds the same simulated household under the same id and
// lets anyone read it, so the example row opens the real view too.
const DEMO_ID = demo.household_id;

type Direction = "up" | "down" | "level";

interface Summary {
  name: string;
  child: string | null;
  week: { date: string; turns: number }[];
  direction: Direction;
  note: string | null;
}

type RowState =
  | { kind: "loading" }
  | { kind: "ok"; summary: Summary }
  | { kind: "ended" }
  | { kind: "gone" }
  | { kind: "error" };

const DEMO_WEEK = (demo.days as Day[]).slice(-7);
const DEMO: Summary = {
  name: demo.name,
  child: demo.child_name,
  week: DEMO_WEEK.map((d) => ({ date: d.date, turns: d.turns })),
  direction: weekDirection(DEMO_WEEK.map((d) => d.turns)),
  note: bestHourNote(DEMO_WEEK[DEMO_WEEK.length - 1], demo.child_name),
};

async function readFamily(f: Family, signal: AbortSignal): Promise<RowState> {
  const headers = { "x-share-token": f.share };
  const base = `${API_URL}/v1/households/${encodeURIComponent(f.id)}`;
  try {
    const h = await fetch(base, { headers, signal });
    if (h.status === 401) return { kind: "ended" };
    if (h.status === 404) return { kind: "gone" };
    if (!h.ok) return { kind: "error" };
    const household = (await h.json()) as { name: string; child_name: string | null };
    const w = await fetch(`${base}/week`, { headers, signal });
    if (w.status === 401) return { kind: "ended" };
    if (!w.ok) return { kind: "error" };
    const week = (await w.json()) as { days: { date: string; turns: number }[]; direction: Direction };
    let note: string | null = null;
    if (week.days.length) {
      const n = await fetch(`${base}/note`, { headers, signal });
      if (n.ok) note = ((await n.json()) as { text: string }).text;
    }
    return {
      kind: "ok",
      summary: { name: household.name, child: household.child_name, week: week.days, direction: week.direction, note },
    };
  } catch (e) {
    if (signal.aborted) throw e;
    return { kind: "error" };
  }
}

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function Coach() {
  const [families, setFamilies] = useState<Family[] | null>(null);
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [open, setOpen] = useState<string | null>(null);
  const [added, setAdded] = useState<string | null>(null);
  const [removed, setRemoved] = useState<{ family: Family; index: number } | null>(null);
  const [readAt, setReadAt] = useState<Date | null>(null);
  const [round, setRound] = useState(0);
  const listScroll = useRef(0);
  const fromList = useRef(false);

  const save = useCallback((next: Family[]) => {
    setFamilies(next);
    const s = storage();
    if (s) writeFamilies(s, next);
  }, []);

  // The address bar: a share link joins the list; #family=<id> opens one.
  useEffect(() => {
    const sync = () => {
      const s = storage();
      let list = s ? readFamilies(s) : [];
      const link = parseShareLink(window.location.hash);
      if (link) {
        list = addFamily(list, link);
        if (s) writeFamilies(s, list);
        history.replaceState(null, "", window.location.pathname);
        setAdded(link.id);
        setOpen(null);
      } else {
        setOpen(parseOpenFamily(window.location.hash));
      }
      setFamilies(list);
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  // One read per family, in parallel. A refresh keeps the rows on screen
  // and replaces each as its answer lands.
  const shares = families?.map((f) => `${f.id}:${f.share}`).join("|") ?? "";
  useEffect(() => {
    if (!families || !families.length) return;
    const ctl = new AbortController();
    setRows((r) => Object.fromEntries(families.map((f) => [f.id, r[f.id] ?? { kind: "loading" }])));
    Promise.all(
      families.map(async (f) => {
        const state = await readFamily(f, ctl.signal);
        setRows((r) => ({ ...r, [f.id]: state }));
        return [f.id, state] as const;
      }),
    )
      .then((done) => {
        setReadAt(new Date());
        // Remember each name, so a share ended later still says whose it was.
        setFamilies((list) => {
          if (!list) return list;
          let next = list;
          for (const [id, state] of done)
            if (state.kind === "ok") next = nameFamily(next, id, state.summary.name, state.summary.child);
          const s = storage();
          if (s) writeFamilies(s, next);
          return next;
        });
      })
      .catch(() => {});
    return () => ctl.abort();
    // `shares` stands for the list's ids and tokens; names alone do not refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shares, round]);

  // The example row starts from the committed simulated data and then
  // takes the service's own answer, so its note is the one the opened
  // view shows. Offline, the committed data stands.
  const [demoRow, setDemoRow] = useState<Summary>(DEMO);
  const empty = families !== null && families.length === 0;
  useEffect(() => {
    if (!empty) return;
    const ctl = new AbortController();
    readFamily({ id: DEMO_ID, share: "" }, ctl.signal)
      .then((state) => {
        if (state.kind === "ok" && state.summary.week.length) setDemoRow(state.summary);
      })
      .catch(() => {});
    return () => ctl.abort();
  }, [empty]);

  useEffect(() => {
    if (open === null && listScroll.current) window.scrollTo(0, listScroll.current);
  }, [open]);

  const openFamily = (id: string) => {
    listScroll.current = window.scrollY;
    fromList.current = true;
    window.location.hash = `family=${encodeURIComponent(id)}`;
    window.scrollTo(0, 0);
  };

  const backToList = () => {
    if (fromList.current) {
      fromList.current = false;
      history.back();
    } else {
      history.replaceState(null, "", window.location.pathname);
      setOpen(null);
    }
  };

  const remove = (id: string) => {
    if (!families) return;
    const index = families.findIndex((f) => f.id === id);
    if (index === -1) return;
    setRemoved({ family: families[index], index });
    save(removeFamily(families, id));
    if (open === id) backToList();
  };

  const undo = () => {
    if (!removed || !families) return;
    const next = families.slice();
    next.splice(Math.min(removed.index, next.length), 0, removed.family);
    save(next);
    setRemoved(null);
  };

  if (families === null) {
    return <p className="text-muted">Looking in this browser for the families you follow.</p>;
  }

  if (open !== null) {
    const fam = families.find((f) => f.id === open);
    const isDemo = open === DEMO_ID && !fam;
    return (
      <div>
        <button type="button" className="coach-back" onClick={backToList}>
          <Chevron dir="left" />
          All families
        </button>
        <div className="mt-6">
          {isDemo ? (
            <Mine key={open} mode="coach" family={{ id: DEMO_ID, key: "" }} />
          ) : fam ? (
            <Mine key={open} mode="coach" family={{ id: fam.id, key: fam.share }} onRemove={() => remove(fam.id)} />
          ) : (
            <p className="max-w-[60ch] leading-relaxed text-muted">
              That family is not in this browser&apos;s list. Open the share link the family made, and it will be.
            </p>
          )}
        </div>
      </div>
    );
  }

  const n = families.length;
  const states = families.map((f) => rows[f.id]);
  const tally = (pred: (s: RowState | undefined) => boolean) => states.filter(pred).length;
  const up = tally((s) => s?.kind === "ok" && s.summary.week.length >= 6 && s.summary.direction === "up");
  const down = tally((s) => s?.kind === "ok" && s.summary.week.length >= 6 && s.summary.direction === "down");
  const ended = tally((s) => s?.kind === "ended");
  const finding = [up && `${up} going up this week`, down && `${down} going down this week`, ended && `${ended} ended the share`]
    .filter(Boolean)
    .join(", ");

  return (
    <section aria-labelledby="coach-title">
      <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
        <div className="min-w-0">
          <h1 id="coach-title" className="display-sm text-[1.875rem] text-ink sm:text-[2.125rem]">
            Families you follow
          </h1>
          <p className="mt-2 max-w-[64ch] text-[15px] leading-relaxed text-muted">
            {n === 0
              ? "No family has shared with this browser yet."
              : `${n} ${n === 1 ? "family" : "families"}, each read with the share link the family made for you${finding ? `; ${finding}` : ""}.`}
          </p>
        </div>
        {n > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <span className="tabular-nums">
              {readAt ? `Read at ${readAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Reading"}
            </span>
            <button type="button" className="ghost min-h-11" onClick={() => setRound((r) => r + 1)}>
              Refresh
            </button>
          </div>
        )}
      </div>

      {removed && (
        <p role="status" className="coach-notice mt-6">
          <span>
            Removed {removed.family.name ?? "a family"} from this browser. Their share still works wherever else it was opened.
          </span>
          <button type="button" className="coach-text-btn" onClick={undo}>
            Undo
          </button>
        </p>
      )}

      {n === 0 && (
        <div className="mt-8 grid gap-x-10 gap-y-4 text-[15px] leading-relaxed text-muted md:grid-cols-2">
          <p>
            A share link is the read-only link a family makes for the person coaching them, with{" "}
            <span className="text-ink">Share with your coach</span> on their own page or{" "}
            <code className="font-mono text-[13px] text-ink">volley share</code> on their computer. It ends in{" "}
            <code className="break-all font-mono text-[13px] text-ink">/coach/#h=&hellip;&amp;s=&hellip;</code>.
          </p>
          <p>
            Open it in this browser and the family joins this list, one row each, for as many families as you visit. The list is
            kept in this browser only, the part after the # never reaches a server, and a family can end its share at any time; its
            row then says so.
          </p>
        </div>
      )}

      {n === 0 && (
        <p className="mt-10 text-sm text-muted">How a family appears here, shown with the simulated family from the front page:</p>
      )}

      <div className={`card ${n === 0 ? "mt-3" : "mt-6"} overflow-hidden`}>
        <div className="coach-row coach-head" aria-hidden="true">
          <span data-a="name">Family</span>
          <span data-a="bars">Last 7 days</span>
          <span data-a="dir">This week</span>
          <span data-a="latest" className="text-right">
            Latest day
          </span>
          <span data-a="note">Tomorrow&apos;s note</span>
          <span data-a="act" />
        </div>
        <ul aria-label={n === 0 ? "An example family" : "Families you follow"}>
          {n === 0 ? (
            <Row state={{ kind: "ok", summary: demoRow }} simulated onOpen={() => openFamily(DEMO_ID)} />
          ) : (
            families.map((f) => (
              <Row
                key={f.id}
                cached={f}
                state={rows[f.id] ?? { kind: "loading" }}
                isNew={f.id === added}
                onOpen={() => openFamily(f.id)}
                onRemove={() => remove(f.id)}
                onRetry={() => setRound((r) => r + 1)}
              />
            ))
          )}
        </ul>
      </div>

      <p className="mt-5 max-w-[70ch] text-sm leading-relaxed text-muted">
        Read-only. Each row is read with that family&apos;s own share, and the service refuses anything from it that would write.
        Counts and the note only, never a word of speech. Remove takes a row off this browser and nothing else.
      </p>
    </section>
  );
}

function Row({
  state,
  cached,
  simulated,
  isNew,
  onOpen,
  onRemove,
  onRetry,
}: {
  state: RowState;
  cached?: Family;
  simulated?: boolean;
  isNew?: boolean;
  onOpen: () => void;
  onRemove?: () => void;
  onRetry?: () => void;
}) {
  const summary = state.kind === "ok" ? state.summary : null;
  const name = summary?.name ?? cached?.name ?? "A family that shared with you";
  const child = summary ? summary.child : (cached?.child ?? null);
  const message =
    state.kind === "ended"
      ? "This family ended the share. Nothing more can be read with it."
      : state.kind === "gone"
        ? "This family deleted its household, and every count went with it."
        : state.kind === "error"
          ? "Could not reach the service just now."
          : null;

  return (
    <li className="coach-row" data-state={state.kind}>
      <div data-a="name" className="min-w-0">
        {state.kind === "ended" || state.kind === "gone" ? (
          <p className="coach-name truncate">{name}</p>
        ) : (
          <button type="button" className="coach-open coach-name" onClick={onOpen}>
            <span className="truncate">{name}</span>
            <Chevron dir="right" />
          </button>
        )}
        <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px] text-muted">
          {child && <span>with {child}</span>}
          {simulated && <span className="coach-pill">Simulated example</span>}
          {isNew && <span className="coach-pill">Just added</span>}
        </p>
      </div>

      {message ? (
        <div data-a="msg" className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
          <span className={state.kind === "ended" ? "text-ink" : undefined}>{message}</span>
          {state.kind === "error" && onRetry && (
            <button type="button" className="coach-text-btn" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      ) : (
        <>
          <WeekBars week={summary?.week ?? null} />
          <div data-a="dir" className="text-sm">
            {summary ? <DirectionLabel summary={summary} /> : <span className="coach-skel h-3 w-16" />}
          </div>
          <div data-a="latest" className="text-right">
            {summary ? (
              summary.week.length ? (
                <>
                  <p className="text-xl leading-tight text-ink tabular-nums">
                    {summary.week[summary.week.length - 1].turns}
                    <span className="sr-only"> turns</span>
                  </p>
                  <p className="text-xs text-muted">{shortDate(summary.week[summary.week.length - 1].date)}</p>
                </>
              ) : (
                <p className="text-sm text-muted">No days yet</p>
              )
            ) : (
              <span className="coach-skel ml-auto h-5 w-10" />
            )}
          </div>
          <div data-a="note" className="min-w-0">
            {summary ? (
              <p className="coach-note text-sm leading-snug text-ink">
                <span className="coach-note-label">Tomorrow&apos;s note: </span>
                {summary.note ?? <span className="text-muted">none until a day is counted</span>}
              </p>
            ) : (
              <>
                <span className="coach-skel h-3 w-full" />
                <span className="coach-skel mt-2 h-3 w-2/3" />
              </>
            )}
          </div>
        </>
      )}

      <div data-a="act">
        {onRemove && (
          <button type="button" className="coach-remove" onClick={onRemove} aria-label={`Remove ${name} from this browser`}>
            <span className="coach-remove-short">Remove</span>
            <span className="coach-remove-long">Remove from this browser</span>
          </button>
        )}
      </div>
    </li>
  );
}

function WeekBars({ week }: { week: { date: string; turns: number }[] | null }) {
  const slots: ({ date: string; turns: number } | null)[] = Array(7).fill(null);
  const last = (week ?? []).slice(-7);
  last.forEach((d, i) => (slots[7 - last.length + i] = d));
  const max = Math.max(1, ...last.map((d) => d.turns));
  const label = week
    ? last.length
      ? `Turns over the last ${last.length} ${last.length === 1 ? "day" : "days"}: ${last.map((d) => `${shortDate(d.date)} ${d.turns}`).join(", ")}`
      : "No days counted yet"
    : "Reading";
  return (
    <div data-a="bars" className="coach-bars" role="img" aria-label={label}>
      {slots.map((d, i) =>
        week === null ? (
          <span key={i} className="coach-bar coach-bar-wait" />
        ) : d ? (
          <span key={i} className="coach-bar" style={{ height: `${Math.max(2, Math.round((28 * d.turns) / max))}px` }} />
        ) : (
          <span key={i} className="coach-bar coach-bar-none" />
        ),
      )}
    </div>
  );
}

function DirectionLabel({ summary }: { summary: Summary }) {
  if (summary.week.length < 6) return <span className="text-muted">Too few days</span>;
  const word = summary.direction === "up" ? "Going up" : summary.direction === "down" ? "Going down" : "Level";
  return (
    <span className="inline-flex items-center gap-1.5 text-ink">
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" className="flex-none text-muted">
        {summary.direction === "up" ? (
          <path d="M3 10.5 10.5 3M5 3h5.5v5.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        ) : summary.direction === "down" ? (
          <path d="M3 3.5 10.5 11M5 11h5.5V5.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M2 7h10M9 4l3 3-3 3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        )}
      </svg>
      {word}
    </span>
  );
}

function Chevron({ dir }: { dir: "left" | "right" }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" className="coach-chevron flex-none">
      <path
        d={dir === "right" ? "M5 3l4 4-4 4" : "M9 3 5 7l4 4"}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
