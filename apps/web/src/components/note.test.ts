import { describe, expect, it } from "vitest";
import { FALLBACK_LABEL, noteSourceLabel, parseNote } from "./note";

describe("noteSourceLabel", () => {
  it("credits the model only when the model wrote it, and names the fact in words", () => {
    expect(noteSourceLabel("bedrock", "best_hour")).toBe("written by Claude on Amazon Bedrock, from the fact: best hour");
    expect(noteSourceLabel("template", "first_day")).toBe("the template layer; the model was not used, from the fact: first day");
    expect(FALLBACK_LABEL).toContain("could not be read");
  });
});

describe("parseNote", () => {
  it("keeps a well-formed body", () => {
    const n = parseNote({ text: "Around six.", source: "bedrock", model: "m", fact: { kind: "best_hour", hour: 18, value: 38 }, simulated: true });
    expect(n?.source).toBe("bedrock");
    expect(n?.fact.hour).toBe(18);
    expect(n?.simulated).toBe(true);
  });
  it("refuses a body without text or a fact, and reads any other source as the template", () => {
    expect(parseNote(null)).toBeNull();
    expect(parseNote({ text: "", fact: { kind: "best_hour" } })).toBeNull();
    expect(parseNote({ text: "x" })).toBeNull();
    expect(parseNote({ text: "x", source: "other", fact: { kind: "best_hour" } })?.source).toBe("template");
  });
});
