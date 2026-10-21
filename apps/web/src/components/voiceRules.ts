import { clock } from "./DayView";

/**
 * The voice panel's two rules, kept pure so they are tested without a
 * microphone: which MCP tool a spoken question maps to, and the sentence
 * read back from what that tool returned. Every number in the sentence
 * comes from the tool's JSON; nothing is added.
 */

export type Tool = "how_was_our_talking_today" | "one_thing_for_tomorrow" | "best_hour_this_week" | "week_trend";

export const QUESTIONS: { ask: string; tool: Tool }[] = [
  { ask: "How was our talking today?", tool: "how_was_our_talking_today" },
  { ask: "What's one thing for tomorrow?", tool: "one_thing_for_tomorrow" },
  { ask: "What was our best hour this week?", tool: "best_hour_this_week" },
];

/** A spoken question to a tool, or null when it is not one the server can answer. */
export function matchTool(said: string): Tool | null {
  const s = said.toLowerCase().replace(/[^a-z' ]+/g, " ");
  if (/\btomorrow\b|\bone thing\b|\bwhat should (i|we) try\b|\btry\b/.test(s)) return "one_thing_for_tomorrow";
  if (/\bbest\b.*\bhour\b|\bhour\b.*\bbest\b|\bbusiest hour\b/.test(s)) return "best_hour_this_week";
  if (/\bthis week\b|\bthe week\b|\bweek\b|\btrend\b/.test(s)) return "week_trend";
  if (/\btoday\b|\bhow was\b|\bhow did\b|\btalking\b|\bturns\b/.test(s)) return "how_was_our_talking_today";
  return null;
}

type J = Record<string, unknown>;

const num = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);
const str = (x: unknown): string | null => (typeof x === "string" && x ? x : null);

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/**
 * "2026-09-28" as "September 28". Read straight from the string, never
 * through Date, so no time zone can move the day. Anything that is not an
 * ISO date comes back null rather than read aloud as digits.
 */
export function dateInWords(iso: string | null): string | null {
  const m = iso ? /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso) : null;
  if (!m) return null;
  const month = MONTHS[Number(m[2]) - 1];
  const day = Number(m[3]);
  return month && day >= 1 && day <= 31 ? `${month} ${day}` : null;
}

/** "the last 7 days", or "the simulated family's last 7 days". */
function span(simulated: boolean, days: number | null): string {
  const whose = simulated ? "the simulated family's" : "the";
  if (days === 1) return `${whose} latest day`;
  return days !== null ? `${whose} last ${days} days` : `${whose} latest days`;
}

/**
 * The sentence read aloud and shown, written only from the tool's own
 * fields. The simulated household is always named as the simulated
 * family, and its day is given in words ("September 28"), never as
 * "today": the counts are fixed, so "today" would be a different day
 * from the one the listener is having.
 */
export function spokenAnswer(tool: Tool, data: J | null): string | null {
  if (!data) return null;
  const simulated = data.simulated === true;
  if (tool === "how_was_our_talking_today") {
    const turns = num(data.turns);
    const date = dateInWords(str(data.date));
    if (turns === null || !date) return null;
    const best = num(data.best_hour);
    const tail = `${turns} turns${best !== null ? `, and the best hour was ${clock(best)}` : ""}.`;
    return simulated ? `On the simulated family's latest day, ${date}, there were ${tail}` : `On ${date}, this household had ${tail}`;
  }
  if (tool === "one_thing_for_tomorrow") {
    const text = str(data.text);
    if (!text) return null;
    const date = dateInWords(str(data.date));
    if (simulated) return date ? `From the simulated family's latest day, ${date}: ${text}` : `For the simulated family: ${text}`;
    return date ? `From ${date}: ${text}` : text;
  }
  if (tool === "best_hour_this_week") {
    const hour = num(data.hour);
    const turns = num(data.turns_this_week);
    if (hour === null || turns === null) return null;
    return `Across ${span(simulated, num(data.days))}, ${clock(hour)} was the busiest hour: ${turns} turns in that hour altogether.`;
  }
  if (tool === "week_trend") {
    const direction = str(data.direction);
    if (!direction) return null;
    const best = dateInWords(str(data.best_day));
    const quiet = dateInWords(str(data.quietest_day));
    const days = Array.isArray(data.days) ? data.days.length : null;
    const dir = direction === "level" ? "holding level" : `going ${direction}`;
    return `Over ${span(simulated, days)}, turns are ${dir}${best ? `; the best day was ${best}` : ""}${quiet ? ` and the quietest ${quiet}` : ""}.`;
  }
  return null;
}
