import { clock } from "./DayView";

/**
 * The week's plan, as the service returns it from
 * GET /v1/households/{id}/plan, and the few words the card puts around
 * it. Kept free of React so the wording is tested once.
 */

export interface PlanFacts {
  days: number;
  best_hour: number;
  best_turns: number;
  quiet_hour: number | null;
  quiet_turns: number | null;
}

export interface Plan {
  facts: PlanFacts;
  lines: string[];
  source: "bedrock" | "template";
  model: string | null;
  simulated: boolean;
}

export const SOURCE_LABEL: Record<Plan["source"], string> = {
  bedrock: "Written by Claude on Amazon Bedrock from the week's counts, behind the same number gate",
  template: "The rules' own words; the model was not used",
};

export function planSourceLabel(source: string): string {
  return source === "bedrock" ? SOURCE_LABEL.bedrock : SOURCE_LABEL.template;
}

function turnsADay(n: number): string {
  return `${n} ${n === 1 ? "turn" : "turns"} a day`;
}

/** The facts the plan was written from, in one short line of clock times. */
export function planFactsLine(f: PlanFacts): string {
  const span = `From ${f.days} ${f.days === 1 ? "day" : "days"}`;
  const best = `best hour ${clock(f.best_hour)}, about ${turnsADay(f.best_turns)}`;
  if (f.quiet_hour === null || f.quiet_turns === null) return `${span}: ${best}.`;
  return `${span}: ${best}; quiet hour ${clock(f.quiet_hour)}, about ${turnsADay(f.quiet_turns)}.`;
}

/**
 * What each line is for, in the order the service writes them: keep the
 * best hour, the quiet hour (or a second idea for the best hour when no
 * hour is quiet), the weekend. The template writes two lines when there
 * is no quiet hour, so the labels follow the count.
 */
export function planLineLabels(f: PlanFacts, count: number): string[] {
  const quiet = f.quiet_hour !== null;
  const middle = quiet ? `The quiet hour, ${clock(f.quiet_hour as number)}` : `Also at ${clock(f.best_hour)}`;
  const all = count >= 3 ? [`Keep ${clock(f.best_hour)}`, middle, "The weekend"] : [`Keep ${clock(f.best_hour)}`, "The weekend"];
  return Array.from({ length: count }, (_, i) => all[i] ?? "");
}

/** The body, checked for the shape the card needs; anything else is null. */
export function parsePlan(body: unknown): Plan | null {
  if (!body || typeof body !== "object") return null;
  const b = body as Record<string, unknown>;
  const f = b.facts as Record<string, unknown> | undefined;
  const lines = b.lines;
  if (!f || typeof f.best_hour !== "number" || typeof f.best_turns !== "number" || typeof f.days !== "number") return null;
  if (!Array.isArray(lines) || !lines.length || !lines.every((l) => typeof l === "string" && l.trim())) return null;
  const quiet = typeof f.quiet_hour === "number" && typeof f.quiet_turns === "number";
  return {
    facts: {
      days: f.days,
      best_hour: f.best_hour,
      best_turns: f.best_turns,
      quiet_hour: quiet ? (f.quiet_hour as number) : null,
      quiet_turns: quiet ? (f.quiet_turns as number) : null,
    },
    lines: lines as string[],
    source: b.source === "bedrock" ? "bedrock" : "template",
    model: typeof b.model === "string" ? b.model : null,
    simulated: b.simulated === true,
  };
}
