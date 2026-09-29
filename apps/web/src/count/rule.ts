/**
 * The turn rule, in the browser, for the drop zone.
 *
 * A port of `serve_return.rule` so a visitor can drop a `bee sync`
 * export on the page and see it counted without anything leaving the
 * tab. A test in this package runs the same fixtures through both and
 * fails if the two ever disagree, which is the only reason a second
 * implementation is tolerable.
 *
 * A conversational turn is one alternation between an adult and a
 * child within five seconds of the first utterance's end. Same-role
 * runs merge while their gaps stay inside the window. Nothing textual
 * survives into the output.
 */

export const WINDOW_SECONDS = 5;
const WORDS_PER_SECOND = 2.5;
const MIN_UTTERANCE_SECONDS = 1;
const WH = /^\s*(who|what|when|where|why|how|which|whose|do|does|did|can|could|would|will|is|are|was|were|shall|should)\b/i;

export interface Utterance {
  start: number; // seconds since the epoch, UTC
  speaker: string;
  text: string;
  end?: number;
}

export interface Roles {
  adult: string[];
  child: string[];
}

export interface HourCounts {
  hour: number;
  turns: number;
  serves_adult: number;
  serves_child: number;
  responses_within_window: number;
  response_latency_median_s: number | null;
  questions_adult: number;
  longest_volley: number;
  talk_seconds_adult: number;
  talk_seconds_child: number;
  utterances_adult: number;
  utterances_child: number;
  words_discarded: number;
}

export interface DayCounts {
  date: string;
  hours: HourCounts[];
  turns: number;
  serves_adult: number;
  serves_child: number;
  responses_within_window: number;
  response_latency_median_s: number | null;
  questions_adult: number;
  longest_volley: number;
  talk_seconds_adult: number;
  talk_seconds_child: number;
  words_discarded: number;
  best_hour: number | null;
  quietest_hour_with_child: number | null;
}

interface Block {
  role: "adult" | "child";
  start: number;
  end: number;
  words: number;
  question: boolean;
}

const norm = (s: string) => s.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");

function roleOf(roles: Roles, speaker: string): "adult" | "child" | null {
  const s = norm(speaker);
  if (roles.adult.map(norm).includes(s)) return "adult";
  if (roles.child.map(norm).includes(s)) return "child";
  return null;
}

const words = (t: string) => t.trim().split(/\s+/).filter(Boolean).length;
const finish = (u: Utterance) =>
  u.end !== undefined && u.end >= u.start ? u.end : u.start + Math.max(MIN_UTTERANCE_SECONDS, words(u.text) / WORDS_PER_SECOND);

function blocks(utterances: Utterance[], roles: Roles, window: number): Block[] {
  const out: Block[] = [];
  for (const u of [...utterances].sort((a, b) => a.start - b.start)) {
    const role = roleOf(roles, u.speaker);
    if (!role || !u.text.trim()) continue;
    const question = role === "adult" && (u.text.trimEnd().endsWith("?") || WH.test(u.text));
    const last = out[out.length - 1];
    if (last && last.role === role && u.start - last.end <= window) {
      last.end = Math.max(last.end, finish(u));
      last.words += words(u.text);
      last.question = last.question || question;
    } else {
      out.push({ role, start: u.start, end: finish(u), words: words(u.text), question });
    }
  }
  return out;
}

const isTurn = (a: Block, b: Block, window: number) => a.role !== b.role && b.start - a.end <= window;

function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return Math.round((s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2) * 100) / 100;
}

export function countTurns(utterances: Utterance[], roles: Roles, window = WINDOW_SECONDS): number {
  const bs = blocks(utterances, roles, window);
  let n = 0;
  for (let i = 1; i < bs.length; i++) if (isTurn(bs[i - 1], bs[i], window)) n++;
  return n;
}

export function countDay(utterances: Utterance[], roles: Roles, date: string, tzOffsetHours = 0, window = WINDOW_SECONDS): DayCounts {
  const bs = blocks(utterances, roles, window);
  const hours = new Map<number, HourCounts & { lat: number[] }>();
  const hourOf = (t: number) => Math.floor((((t + tzOffsetHours * 3600) % 86400) + 86400) % 86400 / 3600);
  const hc = (t: number) => {
    const h = hourOf(t);
    if (!hours.has(h)) {
      hours.set(h, {
        hour: h, turns: 0, serves_adult: 0, serves_child: 0, responses_within_window: 0, response_latency_median_s: null,
        questions_adult: 0, longest_volley: 0, talk_seconds_adult: 0, talk_seconds_child: 0, utterances_adult: 0,
        utterances_child: 0, words_discarded: 0, lat: [],
      });
    }
    return hours.get(h)!;
  };
  for (const b of bs) {
    const h = hc(b.start);
    const seconds = Math.max(0, b.end - b.start);
    if (b.role === "adult") {
      h.utterances_adult++;
      h.talk_seconds_adult += seconds;
      if (b.question) h.questions_adult++;
    } else {
      h.utterances_child++;
      h.talk_seconds_child += seconds;
    }
    h.words_discarded += b.words;
  }
  let volley = 0;
  for (let i = 1; i < bs.length; i++) {
    const a = bs[i - 1], b = bs[i];
    const gap = b.start - a.end;
    if (isTurn(a, b, window)) {
      const h = hc(b.start);
      h.turns++;
      if (volley === 0) {
        if (a.role === "adult") h.serves_adult++;
        else h.serves_child++;
      }
      volley++;
      h.longest_volley = Math.max(h.longest_volley, volley);
      if (a.role === "child" && b.role === "adult") {
        h.responses_within_window++;
        h.lat.push(Math.max(0, gap));
      }
    } else {
      volley = 0;
    }
  }
  const ordered = [...hours.keys()].sort((a, b) => a - b).map((k) => hours.get(k)!);
  for (const h of ordered) h.response_latency_median_s = median(h.lat);
  const allLat = ordered.flatMap((h) => h.lat);
  const withChild = ordered.filter((h) => h.utterances_child > 0);
  const best = ordered.length && ordered.some((h) => h.turns) ? ordered.reduce((m, h) => (h.turns > m.turns ? h : m)).hour : null;
  const quiet = withChild.length ? withChild.reduce((m, h) => (h.turns < m.turns ? h : m)).hour : null;
  const strip = ({ lat: _lat, ...rest }: HourCounts & { lat: number[] }): HourCounts => ({
    ...rest,
    talk_seconds_adult: Math.round(rest.talk_seconds_adult * 10) / 10,
    talk_seconds_child: Math.round(rest.talk_seconds_child * 10) / 10,
  });
  const sum = (k: keyof HourCounts) => ordered.reduce((s, h) => s + (h[k] as number), 0);
  return {
    date,
    hours: ordered.map(strip),
    turns: sum("turns"),
    serves_adult: sum("serves_adult"),
    serves_child: sum("serves_child"),
    responses_within_window: sum("responses_within_window"),
    response_latency_median_s: median(allLat),
    questions_adult: sum("questions_adult"),
    longest_volley: ordered.reduce((m, h) => Math.max(m, h.longest_volley), 0),
    talk_seconds_adult: Math.round(sum("talk_seconds_adult") * 10) / 10,
    talk_seconds_child: Math.round(sum("talk_seconds_child") * 10) / 10,
    words_discarded: sum("words_discarded"),
    best_hour: best,
    quietest_hour_with_child: quiet,
  };
}

/**
 * A `bee sync` markdown export, to utterances. The export writes one
 * conversation per file under a "### Transcription" heading with lines
 * like "- Speaker 1: text". Times are not in the export, so utterances
 * are spaced at the average speaking rate from the file's date; the
 * count is then an estimate, and the drop zone says so.
 */
export function parseSyncMarkdown(md: string, date: string): Utterance[] {
  const out: Utterance[] = [];
  const base = Date.parse(`${date}T12:00:00Z`) / 1000;
  let t = base;
  let inTranscript = false;
  for (const line of md.split(/\r?\n/)) {
    if (/^###\s+Transcription/i.test(line)) {
      inTranscript = true;
      continue;
    }
    if (/^##\s/.test(line)) inTranscript = false;
    if (!inTranscript) continue;
    const m = /^\s*-\s*([^:]{1,40}):\s*(.+?)\s*$/.exec(line);
    if (!m) continue;
    const text = m[2];
    const dur = Math.max(MIN_UTTERANCE_SECONDS, words(text) / WORDS_PER_SECOND);
    out.push({ start: t, speaker: m[1], text, end: t + dur });
    t += dur + 1.5;
  }
  return out;
}
