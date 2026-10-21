"use client";

import { useState } from "react";
import { clock } from "./DayView";
import { MCP_URL, PROTOCOL, rpc, toolJson } from "./mcpClient";
import { SIMULATED_DAY, dateInWords } from "./voiceRules";

/**
 * The agent, held to a real session from the visitor's own browser.
 *
 * The rules ask for the MCP server to be shown in action, and a
 * paragraph saying it works is not that. This opens a session against
 * the deployed endpoint, lists the tools, calls the one tool that
 * returns no data at all, and prints every request with its status and
 * the time it took. Nothing is recorded or mocked; the endpoint is the
 * one Alexa+ would use.
 *
 * It calls two tools. `what_volley_counts` describes the rule and
 * returns none of the numbers, which is the honest answer to "what is
 * this thing counting". `how_was_our_talking_today`, with no household
 * named, answers for the public simulated family, which is what Alexa+
 * would read out: counts and an hour, and no word of speech, because
 * the server never had one.
 *
 * Origin is the interesting part of this. The server validates it, the
 * site's own origin is handed to the server by the stack that knows it,
 * and a hostile origin gets 403. So this panel working from this page
 * is also the proof that the allowlist is wired rather than intended.
 */

interface Line {
  request: string;
  status: number;
  ok: boolean;
  ms: number;
  note?: string;
}

interface Today {
  date: string;
  turns: number;
  best_hour: number | null;
  quietest_hour_with_child: number | null;
  longest_volley: number | null;
  questions_adult: number | null;
  words_discarded: number | null;
  simulated: boolean;
  note?: string;
}

export function McpProof() {
  const [lines, setLines] = useState<Line[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [today, setToday] = useState<Today | null>(null);

  const run = async () => {
    setRunning(true);
    setError(null);
    setAnswer(null);
    setToday(null);
    const out: Line[] = [];
    const push = (l: Line) => {
      out.push(l);
      setLines([...out]);
    };
    try {
      const init = await rpc({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion: PROTOCOL,
          capabilities: {},
          clientInfo: { name: "volley-site", version: "1" },
        },
      });
      const session = init.session;
      if (!session || init.status !== 200) {
        throw new Error(`the server did not open a ${PROTOCOL} session (status ${init.status})`);
      }
      push({ request: "initialize", status: init.status, ok: true, ms: init.ms, note: `session ${session.slice(0, 8)}…` });

      const ready = await rpc({ jsonrpc: "2.0", method: "notifications/initialized" }, session);
      push({ request: "notifications/initialized", status: ready.status, ok: ready.status === 202, ms: ready.ms });

      const list = await rpc({ jsonrpc: "2.0", id: 2, method: "tools/list" }, session);
      const tools =
        (list.json as { result?: { tools?: { name: string }[] } })?.result?.tools?.map((t) => t.name) ?? [];
      push({ request: "tools/list", status: list.status, ok: tools.length === 7, ms: list.ms, note: `${tools.length} tools` });

      const call = await rpc(
        { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "what_volley_counts", arguments: {} } },
        session,
      );
      const parsed = toolJson<{ rule?: string }>(call.json);
      push({ request: "tools/call what_volley_counts", status: call.status, ok: !!parsed, ms: call.ms });
      setAnswer(parsed?.rule ?? null);

      const asked = await rpc(
        { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "how_was_our_talking_today", arguments: {} } },
        session,
      );
      const day = toolJson<Today>(asked.json);
      push({
        request: "tools/call how_was_our_talking_today",
        status: asked.status,
        ok: !!day,
        ms: asked.ms,
        note: day?.simulated ? "the simulated family" : undefined,
      });
      setToday(day);

      const bye = await fetch(MCP_URL, { method: "DELETE", headers: { "mcp-session-id": session } });
      push({ request: "DELETE session", status: bye.status, ok: bye.status === 204, ms: 0 });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="card p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-[60ch]">
          <p className="eyebrow">Live, from this page</p>
          <p className="mt-2 leading-relaxed text-muted">
            Open a session against the deployed server, list its tools, ask it what Volley
            counts, then ask how the talking went today for the simulated family, the way
            Alexa+ would. Every request below is real and timed, and no answer can hold a word
            of speech, because the server never had one.
          </p>
        </div>
        <button type="button" onClick={() => void run()} disabled={running} className="primary">
          {running ? "Running…" : "Hold a session"}
        </button>
      </div>

      {lines.length > 0 && (
        // One row per request. On a phone the request takes the full width and
        // its status and time sit on a line beneath it, each labelled; from
        // 640 px up the labels move into a header and the row is three columns.
        <div className="mt-6">
          <div
            className="hidden grid-cols-[minmax(0,1fr)_4.5rem_4.5rem] gap-x-4 pb-2 text-sm font-medium text-muted sm:grid"
            aria-hidden="true"
          >
            <span>Request</span>
            <span>Status</span>
            <span className="text-right">Time</span>
          </div>
          <ol className="font-mono text-[12px] tabular-nums" aria-label="Requests to the server, in order">
            {lines.map((l) => (
              <li
                key={l.request}
                className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 border-t border-line py-2 sm:grid-cols-[minmax(0,1fr)_4.5rem_4.5rem]"
              >
                <span className="col-span-2 min-w-0 break-words text-ink sm:col-span-1">
                  {l.request}
                  {l.note && <span className="block text-faint sm:ml-2 sm:inline">{l.note}</span>}
                </span>
                <span className={l.ok ? "text-ink" : "text-[var(--warn)]"}>
                  <span className="font-sans text-faint sm:sr-only">status </span>
                  {l.status}
                </span>
                <span className="whitespace-nowrap text-right text-muted">
                  {l.ms ? (
                    <>
                      <span className="sr-only">took </span>
                      {l.ms} ms
                    </>
                  ) : (
                    ""
                  )}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {(answer || today) && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {answer && (
            <figure className="rounded-lg border border-line bg-[var(--raised)] p-4">
              <figcaption className="font-mono text-[12px] text-muted">what_volley_counts</figcaption>
              <p className="mt-2 text-sm leading-relaxed text-ink">{answer}</p>
            </figure>
          )}
          {today && (
            <figure className="rounded-lg border border-line bg-[var(--raised)] p-4">
              <figcaption className="font-mono text-[12px] text-muted">how_was_our_talking_today</figcaption>
              <p className="mt-2 text-sm leading-relaxed text-ink">
                {today.simulated
                  ? `On ${SIMULATED_DAY}, there were ${today.turns} turns`
                  : `On ${dateInWords(today.date) ?? today.date}, this household had ${today.turns} turns`}
                {today.best_hour !== null ? `; the best hour was ${clock(today.best_hour)}` : ""}
                {today.longest_volley ? `, the longest exchange ${today.longest_volley} turns` : ""}
                {today.words_discarded !== null ? `, and ${today.words_discarded} words were read and thrown away to count it` : ""}.
              </p>
              {today.note && <p className="mt-2 text-xs leading-relaxed text-muted">The server adds: {today.note}</p>}
            </figure>
          )}
        </div>
      )}

      {error && <p className="mt-4 text-sm text-[var(--warn)]">{error}</p>}
    </div>
  );
}
