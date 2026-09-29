"use client";

import { useState } from "react";

/**
 * The privacy claim, pressed rather than read.
 *
 * One request sends a day to the live API with everything a transcript
 * could carry attached: the transcript itself, the child's words, a
 * name, a doctor, an address, an account number, a place, and a text
 * field inside an hour. The server keeps what it keeps, reads it back,
 * and searches for every one of those strings. The response is shown
 * whole. The interesting result is an absence.
 *
 * The server runs this against a fresh in-memory store, so nothing a
 * visitor presses can write into the deployed table; the response says
 * so, and this panel prints that line.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8791";

interface Finding {
  what: string;
  value: string;
  found: boolean;
}

interface Result {
  status: number;
  fields_sent: string[];
  fields_dropped: string[];
  fields_stored: string[];
  strings_stored: string[];
  findings: Finding[];
  leaked: boolean;
  turns_stored: number | null;
  ms: number;
  sandbox_note: string;
}

export function PrivacyProof() {
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/privacy-check`, { method: "POST" });
      setResult((await res.json()) as Result);
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
            Send a day to the real intake route with a transcript, a name, a doctor, an address and an account number attached, then
            read back what was stored and search it for every one of them.
          </p>
        </div>
        <button type="button" onClick={() => void run()} disabled={running} className="primary">
          {running ? "Sending..." : "Send a transcript"}
        </button>
      </div>

      {result && (
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div>
            <p className="text-sm font-semibold text-ink">
              {result.leaked ? "Something got through" : "Nothing got through"}, in {result.ms} ms, status {result.status}
            </p>
            <table className="mt-3 w-full text-sm">
              <thead>
                <tr className="text-left text-muted">
                  <th className="pb-2 font-medium">Sent</th>
                  <th className="pb-2 font-medium">Stored</th>
                </tr>
              </thead>
              <tbody>
                {result.findings.map((f) => (
                  <tr key={f.what} className="border-t border-line">
                    <td className="py-2 text-ink">
                      {f.what}: <span className="font-mono text-[12px]">{f.value}</span>
                    </td>
                    <td className={`py-2 font-mono text-[12px] ${f.found ? "text-[var(--warn)]" : "text-ink"}`}>{f.found ? "found" : "gone"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-sm text-muted">
            <p>
              Fields sent: <span className="font-mono text-[12px] text-ink">{result.fields_sent.join(", ")}</span>
            </p>
            <p className="mt-2">
              Dropped at the door: <span className="font-mono text-[12px] text-ink">{result.fields_dropped.join(", ") || "none"}</span>
            </p>
            <p className="mt-2">
              The only string stored: <span className="font-mono text-[12px] text-ink">{result.strings_stored.join(", ")}</span>
            </p>
            <p className="mt-2">
              Turns stored: <span className="font-mono text-[12px] text-ink">{result.turns_stored}</span>
            </p>
            <p className="mt-3 text-xs text-faint">{result.sandbox_note}.</p>
          </div>
        </div>
      )}
      {error && <p className="mt-4 text-sm text-[var(--warn)]">{error}</p>}
    </div>
  );
}
