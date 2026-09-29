"use client";

import { useState } from "react";
import { countDay, parseSyncMarkdown, type DayCounts } from "../count/rule";
import { DayView } from "./DayView";
import { Info } from "./Info";

/**
 * Drop a Bee export here; nothing leaves the tab.
 *
 * `bee sync` writes one markdown file per conversation with a
 * "### Transcription" section of "- Speaker 1: ..." lines. This reads
 * the file in the browser, asks which label is the parent and which
 * the child, counts with the same rule the Python package uses, and
 * shows the day. The file is never uploaded: there is no request in
 * this component at all, and the network tab of the browser is the
 * proof.
 *
 * The export carries no times, so utterances are spaced at the average
 * speaking rate and the count is an estimate. The panel says so.
 */

export function DropZone() {
  const [labels, setLabels] = useState<string[]>([]);
  const [text, setText] = useState<string>("");
  const [adult, setAdult] = useState<string>("");
  const [child, setChild] = useState<string>("");
  const [day, setDay] = useState<DayCounts | null>(null);
  const [name, setName] = useState<string>("");

  const read = async (file: File) => {
    const md = await file.text();
    const utts = parseSyncMarkdown(md, new Date().toISOString().slice(0, 10));
    const seen = [...new Set(utts.map((u) => u.speaker))];
    setText(md);
    setLabels(seen);
    setName(file.name);
    setAdult(seen[0] ?? "");
    setChild(seen[1] ?? "");
    setDay(null);
  };

  const count = () => {
    const utts = parseSyncMarkdown(text, new Date().toISOString().slice(0, 10));
    setDay(countDay(utts, { adult: [adult], child: [child] }, new Date().toISOString().slice(0, 10)));
  };

  return (
    <div className="card p-6 sm:p-8">
      <p className="eyebrow">Count in this tab, upload nothing</p>
      <p className="mt-2 max-w-[60ch] leading-relaxed text-muted">
        Run <code className="font-mono text-xs">bee sync</code> on your computer and drop one of the conversation files it writes here. It is
        read in your browser and counted with the same rule <Info term="fiveSeconds" />; there is no upload in this panel at all.
      </p>
      <label
        className="mt-5 block cursor-pointer rounded-lg border border-dashed border-line-strong p-8 text-center text-muted"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files[0];
          if (f) void read(f);
        }}
      >
        <input type="file" accept=".md,text/markdown,text/plain" className="sr-only" onChange={(e) => e.target.files?.[0] && void read(e.target.files[0])} />
        {name ? `${name}: ${labels.length} speaker labels found` : "Drop a bee sync conversation file, or press to choose one"}
      </label>

      {labels.length > 0 && (
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <label className="text-sm text-muted">
            Which label is you
            <select className="mt-1 block w-full rounded border border-line bg-[var(--surface)] p-2 text-ink" value={adult} onChange={(e) => setAdult(e.target.value)}>
              {labels.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <label className="text-sm text-muted">
            Which label is your child
            <select className="mt-1 block w-full rounded border border-line bg-[var(--surface)] p-2 text-ink" value={child} onChange={(e) => setChild(e.target.value)}>
              {labels.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <div className="flex items-end">
            <button type="button" className="primary" onClick={count} disabled={!adult || !child || adult === child}>
              Count
            </button>
          </div>
        </div>
      )}

      {day && (
        <div className="mt-6">
          <DayView day={day} child={null} simulated={false} />
          <p className="mt-3 text-sm text-faint">
            An estimate: the export carries no times, so utterances were spaced at an average speaking rate. The command on your
            computer uses the Bee&apos;s real times.
          </p>
        </div>
      )}
    </div>
  );
}
