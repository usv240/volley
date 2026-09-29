import { describe, expect, it } from "vitest";
import { countDay, countTurns, parseSyncMarkdown, type Roles, type Utterance } from "./rule";

/**
 * The browser port against the same examples the Python package pins.
 * The fixture values here are copied from packages/serve-return/tests
 * and any drift between the two is a failure in both suites.
 */

const ROLES: Roles = { adult: ["MOT", "FAT"], child: ["CHI"] };
const T0 = 1_790_714_400;
const u = (offset: number, speaker: string, text: string, length?: number): Utterance =>
  ({ start: T0 + offset, speaker, text, end: length === undefined ? undefined : T0 + offset + length });

describe("the rule", () => {
  it("counts an answer within five seconds and not one after", () => {
    expect(countTurns([u(0, "MOT", "What is that?", 1), u(4.9, "CHI", "A dog.", 1)], ROLES)).toBe(1);
    expect(countTurns([u(0, "MOT", "What is that?", 1), u(6.1, "CHI", "A dog.", 1)], ROLES)).toBe(0);
  });

  it("measures the gap from the end of the first utterance", () => {
    expect(countTurns([u(0, "MOT", "Tell me about your day at school", 4), u(8, "CHI", "Fun.", 0.5)], ROLES)).toBe(1);
  });

  it("merges a monologue and counts every alternation", () => {
    expect(countTurns([u(0, "MOT", "One.", 1), u(1.5, "MOT", "Two.", 1), u(3, "MOT", "Three.", 1), u(4.5, "CHI", "Yes.", 1)], ROLES)).toBe(1);
    expect(countTurns([u(0, "MOT", "Hi?", 1), u(2, "CHI", "Hi.", 1), u(4, "MOT", "What now?", 1), u(6, "CHI", "Play.", 1), u(8, "MOT", "Which?", 1)], ROLES)).toBe(4);
  });

  it("ignores an unmapped speaker and counts nothing for two adults", () => {
    expect(countTurns([u(0, "MOT", "Dinner?", 1), u(2, "VISITOR", "Lovely.", 1), u(4, "CHI", "Yes!", 1)], ROLES)).toBe(1);
    expect(countTurns([u(0, "MOT", "Did you call?", 1), u(2, "FAT", "I did.", 1), u(4, "MOT", "And?", 1)], ROLES)).toBe(0);
  });

  it("breaks out the day the way the package does", () => {
    const day = countDay(
      [u(0, "CHI", "Mama look.", 1), u(2, "MOT", "What did you find?", 1), u(4, "CHI", "A bug.", 1), u(6, "MOT", "Where was it?", 1), u(20, "MOT", "Time for a bath.", 1), u(22, "CHI", "No.", 1)],
      ROLES,
      "2026-09-29",
    );
    expect(day.turns).toBe(4);
    expect(day.serves_child).toBe(1);
    expect(day.serves_adult).toBe(1);
    expect(day.responses_within_window).toBe(2);
    expect(day.response_latency_median_s).toBe(1);
    expect(day.questions_adult).toBe(2);
    expect(day.longest_volley).toBe(3);
    expect(day.words_discarded).toBe(16);
    expect(day.best_hour).toBe(20);
  });

  it("keeps no word in the output", () => {
    const names = ["Priya", "Arjun", "Mehta", "Bangalore"];
    const utts = Array.from({ length: 12 }, (_, i) => u(i * 2, i % 2 ? "CHI" : "MOT", `Tell ${names[i % 4]} about ${names[(i + 1) % 4]}?`, 1));
    const blob = JSON.stringify(countDay(utts, ROLES, "2026-09-29"));
    for (const n of names) expect(blob).not.toContain(n);
  });

  it("reads a bee sync export and says nothing about the words", () => {
    const md = "## Conversation 1\n### Transcription 456\n- Speaker 1: Hello, how are you?\n- Speaker 2: Fine.\n- Speaker 1: What did you do?\n";
    const utts = parseSyncMarkdown(md, "2026-09-29");
    expect(utts.length).toBe(3);
    expect(countTurns(utts, { adult: ["Speaker 1"], child: ["Speaker 2"] })).toBe(2);
  });
});
