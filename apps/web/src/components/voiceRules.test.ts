import { describe, expect, it } from "vitest";
import { QUESTIONS, matchTool, spokenAnswer } from "./voiceRules";

describe("a spoken question, mapped to the MCP tool that answers it", () => {
  it("maps the three asked questions, as said and as the chips say them", () => {
    expect(matchTool("how was our talking today")).toBe("how_was_our_talking_today");
    expect(matchTool("what's one thing for tomorrow")).toBe("one_thing_for_tomorrow");
    expect(matchTool("what was our best hour this week")).toBe("best_hour_this_week");
    for (const q of QUESTIONS) expect(matchTool(q.ask)).toBe(q.tool);
  });

  it("takes looser phrasings and refuses what no tool answers", () => {
    expect(matchTool("What should I try tomorrow?")).toBe("one_thing_for_tomorrow");
    expect(matchTool("How did we do today")).toBe("how_was_our_talking_today");
    expect(matchTool("how is the week going")).toBe("week_trend");
    expect(matchTool("play some music")).toBeNull();
    expect(matchTool("")).toBeNull();
  });
});

describe("the sentence read back", () => {
  it("uses only the tool's own fields", () => {
    expect(spokenAnswer("how_was_our_talking_today", { date: "2026-09-28", turns: 157, best_hour: 18, simulated: true })).toBe(
      "On 2026-09-28, the simulated family had 157 turns, and the best hour was 6pm.",
    );
    expect(spokenAnswer("best_hour_this_week", { hour: 19, turns_this_week: 309, days: 7, simulated: true })).toBe(
      "This week, the simulated family's best hour was 7pm, with 309 turns across 7 days.",
    );
    expect(spokenAnswer("one_thing_for_tomorrow", { text: "Keep six o'clock as it is.", simulated: true })).toBe(
      "Keep six o'clock as it is.",
    );
    expect(spokenAnswer("week_trend", { direction: "level", best_day: "2026-09-26", quietest_day: "2026-09-24", simulated: true })).toBe(
      "This week, the simulated family's turns are holding level; the best day was 2026-09-26 and the quietest 2026-09-24.",
    );
  });

  it("says nothing rather than guess when a field is missing", () => {
    expect(spokenAnswer("how_was_our_talking_today", { simulated: true })).toBeNull();
    expect(spokenAnswer("best_hour_this_week", null)).toBeNull();
  });
});
