"use client";

import { useEffect, useRef, useState } from "react";
import { callOnce } from "./mcpClient";
import { QUESTIONS, matchTool, spokenAnswer, type Tool } from "./voiceRules";

/**
 * Ask it out loud, in this browser.
 *
 * A stand-in for Alexa+'s voice: the browser's own speech recognition
 * hears the question, a small pure rule (voiceRules.ts) maps it to one of
 * the server's MCP tools, the tool is called live for the public
 * simulated household, and the browser's speech synthesis reads the
 * answer. Nothing here is Alexa, and the panel never says it is; what it
 * shares with Alexa+ is the server and the calls.
 *
 * Where the browser cannot hear (Firefox, most of Safari, a denied
 * microphone), three questions to tap do the same thing, and they are
 * always there, so the panel works with no microphone at all.
 */

interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
}

type RecognitionCtor = new () => Recognition;

function recognitionCtor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

interface Result {
  asked: string;
  via: "voice" | "tap";
  tool: Tool | null;
  answer: string | null;
  status?: number;
  ms?: number;
  spoken: boolean;
}

const HEARD_ERROR: Record<string, string> = {
  "not-allowed": "The browser was not allowed to use the microphone. Tap a question instead.",
  "service-not-allowed": "This browser's speech service is turned off. Tap a question instead.",
  "no-speech": "Nothing was heard. Try again, or tap a question.",
  "audio-capture": "No microphone was found. Tap a question instead.",
  network: "The browser's speech service could not be reached. Tap a question instead.",
};

export function VoiceAsk() {
  const [canHear, setCanHear] = useState<boolean | null>(null);
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState("");
  const [asking, setAsking] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const rec = useRef<Recognition | null>(null);

  useEffect(() => {
    setCanHear(recognitionCtor() !== null);
    return () => {
      rec.current?.abort();
      if (typeof window !== "undefined" && window.speechSynthesis) window.speechSynthesis.cancel();
    };
  }, []);

  const speak = (text: string): boolean => {
    const synth = typeof window !== "undefined" ? window.speechSynthesis : undefined;
    if (!synth || typeof SpeechSynthesisUtterance === "undefined") return false;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    synth.speak(u);
    return true;
  };

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  };

  const ask = async (question: string, via: "voice" | "tap", known?: Tool) => {
    const tool = known ?? matchTool(question);
    setError(null);
    if (!tool) {
      const answer = "That is not a question the server answers. Ask how the talking went today, one thing for tomorrow, or the best hour this week.";
      setResult({ asked: question, via, tool: null, answer, spoken: speak(answer) });
      return;
    }
    setAsking(question);
    setResult(null);
    try {
      const { data, ms, status } = await callOnce<Record<string, unknown>>(tool);
      const answer = spokenAnswer(tool, data);
      if (!answer) throw new Error(`the tool answered ${status} with nothing to read`);
      setResult({ asked: question, via, tool, answer, status, ms, spoken: speak(answer) });
    } catch (e) {
      setError(`Could not reach the server just now (${e instanceof Error ? e.message : String(e)}). Try again.`);
    } finally {
      setAsking(null);
    }
  };

  const listen = () => {
    if (listening) {
      rec.current?.stop();
      return;
    }
    const Ctor = recognitionCtor();
    if (!Ctor) return;
    stopSpeaking();
    const r = new Ctor();
    r.lang = "en-US";
    r.interimResults = true;
    r.continuous = false;
    r.maxAlternatives = 1;
    let final = "";
    let failed = false;
    r.onresult = (e) => {
      const said = Array.from(e.results)
        .map((x) => x[0].transcript)
        .join("")
        .trim();
      setHeard(said);
      if (e.results[e.results.length - 1].isFinal) final = said;
    };
    r.onerror = (e) => {
      failed = true;
      if (e.error !== "aborted") setError(HEARD_ERROR[e.error] ?? `The browser could not hear (${e.error}). Tap a question instead.`);
    };
    r.onend = () => {
      setListening(false);
      rec.current = null;
      if (final) void ask(final, "voice");
      else if (!failed) setError(HEARD_ERROR["no-speech"]);
    };
    rec.current = r;
    setHeard("");
    setError(null);
    setResult(null);
    setListening(true);
    try {
      r.start();
    } catch {
      setListening(false);
      setError("The browser could not start listening. Tap a question instead.");
    }
  };

  const busy = asking !== null;

  return (
    <div className="card mt-6 p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-5">
        <div className="max-w-[60ch]">
          <p className="font-semibold text-ink">By voice, in this browser</p>
          <p className="mt-2 leading-relaxed text-muted">
            A stand-in for Alexa+&apos;s voice, in this browser: the same MCP calls Alexa+ would make. The question is mapped to one of the
            server&apos;s tools, the tool is called live for the simulated family, and this browser reads the answer aloud.
          </p>
        </div>
        {canHear && (
          <button
            type="button"
            className={`voice-mic${listening ? " is-listening" : ""}`}
            onClick={listen}
            disabled={busy}
            aria-pressed={listening}
          >
            <span className="voice-mic-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 20 20">
                <rect x="7" y="2.5" width="6" height="10" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
                <path d="M4.5 9.5a5.5 5.5 0 0 0 11 0M10 15v2.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </span>
            {listening ? "Listening, tap to stop" : "Ask out loud"}
          </button>
        )}
      </div>

      <div className="mt-6">
        <p className="text-sm text-muted">
          {canHear === false ? "This browser cannot listen. Tap a question; it makes the same call." : "Or tap a question; it makes the same call."}
        </p>
        <ul className="mt-3 flex flex-wrap gap-2" aria-label="Questions to ask">
          {QUESTIONS.map((q) => (
            <li key={q.tool}>
              <button
                type="button"
                className="voice-chip"
                onClick={() => void ask(q.ask, "tap", q.tool)}
                disabled={busy || listening}
                aria-busy={asking === q.ask}
              >
                {q.ask}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 min-h-[1.5rem]" aria-live="polite">
        {listening && (
          <p className="text-sm text-muted">
            Heard so far: <span className="text-ink">{heard || "listening"}</span>
          </p>
        )}
        {asking && (
          <p className="text-sm text-muted">
            Asking the server: <span className="text-ink">&ldquo;{asking}&rdquo;</span>
          </p>
        )}
        {result && (
          <dl className="voice-result">
            <div>
              <dt>{result.via === "voice" ? "Heard" : "Asked"}</dt>
              <dd className="text-ink">&ldquo;{result.asked}&rdquo;</dd>
            </div>
            <div>
              <dt>Tool called</dt>
              <dd className="font-mono text-[13px] text-ink break-words">
                {result.tool ? `tools/call ${result.tool}` : "none; no tool answers that"}
                {result.ms ? <span className="ml-2 text-muted">{`${result.status} in ${result.ms} ms, session opened and closed`}</span> : null}
              </dd>
            </div>
            <div>
              <dt>Answer</dt>
              <dd>
                <p className="text-[17px] leading-relaxed text-ink">{result.answer}</p>
                <p className="mt-2 flex flex-wrap items-center gap-x-3 text-sm text-muted">
                  <span>{result.spoken ? "Read aloud by this browser's speech synthesis." : "This browser has no speech synthesis, so the answer is shown only."}</span>
                  {speaking && (
                    <button type="button" className="coach-text-btn" onClick={stopSpeaking}>
                      Stop reading
                    </button>
                  )}
                </p>
              </dd>
            </div>
          </dl>
        )}
        {error && (
          <p className="text-sm text-[var(--warn-strong)]" role="alert">
            {error}
          </p>
        )}
      </div>

      <p className="mt-6 border-t border-line pt-4 text-sm leading-relaxed text-muted">
        Speech recognition is the browser&apos;s own: Chrome sends the audio to its speech service to write it down. Volley&apos;s server
        receives only the tool call, and every tool answers for the public simulated family here.
      </p>
    </div>
  );
}
