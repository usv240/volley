import { describe, expect, it } from "vitest";
import { QUESTIONS, dateInWords, matchTool, spokenAnswer } from "./voiceRules";

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
      "On the simulated family's latest counted day, there were 157 turns, and the best hour was 6pm.",
    );
    expect(spokenAnswer("best_hour_this_week", { hour: 19, turns_this_week: 309, days: 7, simulated: true })).toBe(
      "Across the simulated family's last 7 days, 7pm was the busiest hour across the week: 309 turns in that hour altogether.",
    );
    expect(spokenAnswer("one_thing_for_tomorrow", { date: "2026-09-28", text: "Ask Asha about one thing.", simulated: true })).toBe(
      "On the simulated family's latest counted day, the one thing for tomorrow was: Ask Asha about one thing.",
    );
    expect(
      spokenAnswer("week_trend", {
        direction: "level",
        days: [{}, {}, {}, {}, {}, {}, {}],
        best_day: "2026-09-26",
        quietest_day: "2026-09-24",
        simulated: true,
      }),
    ).toBe("Over the simulated family's last 7 days, turns are holding level.");
  });

  it("says a real household's day as a date in words", () => {
    expect(spokenAnswer("how_was_our_talking_today", { date: "2026-09-28", turns: 157, best_hour: 18, simulated: false })).toBe(
      "On September 28, this household had 157 turns, and the best hour was 6pm.",
    );
    expect(spokenAnswer("one_thing_for_tomorrow", { date: "2026-09-28", text: "Ask one question.", simulated: false })).toBe(
      "From September 28: Ask one question.",
    );
    expect(
      spokenAnswer("week_trend", { direction: "up", days: [{}, {}], best_day: "2026-09-26", quietest_day: "2026-09-27", simulated: false }),
    ).toBe("Over the last 2 days, turns are going up; the best day was September 26 and the quietest September 27.");
  });

  it("says a week's busiest hour as that hour's total across the week, not as one day's", () => {
    expect(spokenAnswer("best_hour_this_week", { hour: 19, turns_this_week: 309, days: 7, simulated: false })).toBe(
      "Across the last 7 days, 7pm was the busiest hour across the week: 309 turns in that hour altogether.",
    );
  });

  it("never says the simulated family's day as a date or as today", () => {
    const answers = [
      spokenAnswer("how_was_our_talking_today", { date: "2026-09-28", turns: 157, best_hour: 18, simulated: true }),
      spokenAnswer("one_thing_for_tomorrow", { date: "2026-09-28", text: "Ask one question.", simulated: true }),
      spokenAnswer("one_thing_for_tomorrow", { text: "Ask one question.", simulated: true }),
      spokenAnswer("best_hour_this_week", { hour: 19, turns_this_week: 309, days: 7, simulated: true }),
      spokenAnswer("week_trend", { direction: "up", days: [{}, {}], best_day: "2026-09-26", quietest_day: "2026-09-27", simulated: true }),
    ];
    for (const a of answers) {
      expect(a).toContain("the simulated family");
      expect(a).not.toMatch(/\d{4}-\d{2}-\d{2}/);
      expect(a).not.toMatch(/\btoday\b/i);
      expect(a).not.toMatch(/January|February|March|April|May|June|July|August|September|October|November|December/);
    }
  });

  it("writes a date in words from the string alone", () => {
    expect(dateInWords("2026-09-28")).toBe("September 28");
    expect(dateInWords("2026-01-01")).toBe("January 1");
    expect(dateInWords("2026-13-01")).toBeNull();
    expect(dateInWords("yesterday")).toBeNull();
    expect(dateInWords(null)).toBeNull();
  });

  it("says nothing rather than guess when a field is missing", () => {
    expect(spokenAnswer("how_was_our_talking_today", { simulated: true })).toBeNull();
    expect(spokenAnswer("how_was_our_talking_today", { date: "not a date", turns: 3, simulated: true })).toBeNull();
    expect(spokenAnswer("one_thing_for_tomorrow", { date: "2026-09-28", simulated: true })).toBeNull();
    expect(spokenAnswer("best_hour_this_week", null)).toBeNull();
  });
});
