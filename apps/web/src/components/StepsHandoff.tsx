"use client";

import { useEffect, useState } from "react";

/**
 * The phone's way past the terminal.
 *
 * "Count your own" leads to six commands, and the person who pressed it
 * is often on a phone, which cannot run any of them. So below the desk
 * breakpoint this says plainly where setup runs and hands the steps to
 * that computer: copied as plain text, or through the phone's own share
 * sheet where the browser has one. Nothing is sent anywhere by this page.
 */

export function StepsHandoff({ steps, note }: { steps: { title: string; body: string }[]; note: string }) {
  const [canShare, setCanShare] = useState(false);
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    setCanShare(typeof navigator.share === "function");
  }, []);

  const text = () =>
    [
      "Volley: count your own day. Run these on the computer where your Bee is signed in.",
      "",
      ...steps.flatMap((s, i) => [`${i + 1}. ${s.title}`, ...s.body.split("\n").map((line) => `   ${line}`), ""]),
      note,
      "",
      `${window.location.origin}/#yours`,
    ].join("\n");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text());
      setStatus("copied");
    } catch {
      setStatus("failed");
    }
  };

  const share = async () => {
    try {
      await navigator.share({ title: "Volley setup steps", text: text() });
    } catch {
      /* Dismissed, or the share sheet is unavailable; nothing to undo. */
    }
  };

  return (
    <div className="mt-8 rounded-2xl border border-line bg-surface p-4 md:hidden">
      <p className="text-[15px] leading-relaxed text-ink">
        Setup runs on the computer where your Bee is signed in, not on this phone. Send yourself the steps.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" className="secondary min-h-11 !px-4 !py-2 !text-[15px]" onClick={() => void copy()}>
          Copy the steps
        </button>
        {canShare && (
          <button type="button" className="secondary min-h-11 !px-4 !py-2 !text-[15px]" onClick={() => void share()}>
            Share
          </button>
        )}
      </div>
      <p className="mt-2 min-h-5 text-sm text-muted" aria-live="polite">
        {status === "copied"
          ? "Copied. Paste them into a note or a message to yourself."
          : status === "failed"
            ? "This browser would not copy. The steps are below; a long press selects them."
            : ""}
      </p>
    </div>
  );
}
