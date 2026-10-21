import { describe, expect, it } from "vitest";
import { SOURCE_LABEL, parsePlan, planFactsLine, planLineLabels, planSourceLabel } from "./plan";

const FACTS = { days: 7, best_hour: 18, best_turns: 22, quiet_hour: 8, quiet_turns: 3 };

describe("planFactsLine", () => {
  it("names both hours as clock times, the best as the week's, and turns as that hour's average", () => {
    expect(planFactsLine(FACTS)).toBe(
      "From 7 days: best hour across the week 6pm, about 22 turns in that hour, on average; quiet hour 8am, about 3 turns in that hour, on average.",
    );
  });
  it("drops the quiet hour when there is none, and counts one day and one turn in the singular", () => {
    expect(planFactsLine({ days: 1, best_hour: 12, best_turns: 1, quiet_hour: null, quiet_turns: null })).toBe(
      "From 1 day: best hour across the week 12pm, about 1 turn in that hour, on average.",
    );
  });
});

describe("planSourceLabel", () => {
  it("credits the model only when the model wrote it", () => {
    expect(planSourceLabel("bedrock")).toBe(SOURCE_LABEL.bedrock);
    expect(planSourceLabel("template")).toBe("The rules' own words; the model was not used");
    expect(planSourceLabel("anything else")).toBe(SOURCE_LABEL.template);
  });
});

describe("planLineLabels", () => {
  it("labels keep, quiet hour, weekend", () => {
    expect(planLineLabels(FACTS, 3)).toEqual(["Keep 6pm", "The quiet hour, 8am", "The weekend"]);
  });
  it("labels a second best-hour idea when no hour is quiet, and the template's two lines", () => {
    const f = { ...FACTS, quiet_hour: null, quiet_turns: null };
    expect(planLineLabels(f, 3)).toEqual(["Keep 6pm", "Also at 6pm", "The weekend"]);
    expect(planLineLabels(f, 2)).toEqual(["Keep 6pm", "The weekend"]);
  });
});

describe("parsePlan", () => {
  it("keeps a well-formed body and nulls a missing quiet hour", () => {
    const p = parsePlan({ facts: { ...FACTS, quiet_hour: null, quiet_turns: null }, lines: ["a", "b"], source: "template", model: null, simulated: true });
    expect(p?.facts.quiet_hour).toBeNull();
    expect(p?.simulated).toBe(true);
    expect(p?.source).toBe("template");
  });
  it("refuses a body without facts or lines", () => {
    expect(parsePlan(null)).toBeNull();
    expect(parsePlan({ facts: FACTS, lines: [] })).toBeNull();
    expect(parsePlan({ lines: ["a"] })).toBeNull();
    expect(parsePlan({ facts: FACTS, lines: ["a", ""] })).toBeNull();
  });
});
