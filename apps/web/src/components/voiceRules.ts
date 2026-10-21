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

/** The sentence read aloud and shown, written only from the tool's own fields. */
export function spokenAnswer(tool: Tool, data: J | null): string | null {
  if (!data) return null;
  const who = data.simulated ? "the simulated family" : "this household";
  if (tool === "how_was_our_talking_today") {
    const turns = num(data.turns);
    const date = str(data.date);
    if (turns === null || !date) return null;
    const best = num(data.best_hour);
    return `On ${date}, ${who} had ${turns} turns${best !== null ? `, and the best hour was ${clock(best)}` : ""}.`;
  }
  if (tool === "one_thing_for_tomorrow") {
    return str(data.text);
  }
  if (tool === "best_hour_this_week") {
    const hour = num(data.hour);
    const turns = num(data.turns_this_week);
    const days = num(data.days);
    if (hour === null || turns === null) return null;
    return `This week, ${who}'s best hour was ${clock(hour)}, with ${turns} turns${days !== null ? ` across ${days} days` : ""}.`;
  }
  if (tool === "week_trend") {
    const direction = str(data.direction);
    const best = str(data.best_day);
    const quiet = str(data.quietest_day);
    if (!direction) return null;
    const dir = direction === "level" ? "holding level" : `going ${direction}`;
    return `This week, ${who}'s turns are ${dir}${best ? `; the best day was ${best}` : ""}${quiet ? ` and the quietest ${quiet}` : ""}.`;
  }
  return null;
}
