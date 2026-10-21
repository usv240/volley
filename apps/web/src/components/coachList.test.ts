import { describe, expect, it } from "vitest";
import {
  LEGACY_KEY,
  LIST_KEY,
  addFamily,
  nameFamily,
  parseOpenFamily,
  parseShareLink,
  readFamilies,
  removeFamily,
  shortDate,
  weekDirection,
  type KeyValue,
} from "./coachList";

function memory(seed: Record<string, string> = {}): KeyValue & { data: Record<string, string> } {
  const data = { ...seed };
  return {
    data,
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => {
      data[k] = v;
    },
    removeItem: (k) => {
      delete data[k];
    },
  };
}

describe("the coach's list of families", () => {
  it("starts empty and survives a corrupt entry", () => {
    expect(readFamilies(memory())).toEqual([]);
    expect(readFamilies(memory({ [LIST_KEY]: "{not json" }))).toEqual([]);
    expect(readFamilies(memory({ [LIST_KEY]: JSON.stringify([{ id: "h_1" }, { id: "h_2", share: "s" }]) }))).toEqual([
      { id: "h_2", share: "s" },
    ]);
  });

  it("moves the one family the old page remembered into the list", () => {
    const store = memory({ [LEGACY_KEY]: JSON.stringify({ id: "h_old", key: "tok" }) });
    expect(readFamilies(store)).toEqual([{ id: "h_old", share: "tok" }]);
    expect(store.data[LEGACY_KEY]).toBeUndefined();
    expect(JSON.parse(store.data[LIST_KEY])).toEqual([{ id: "h_old", share: "tok" }]);
  });

  it("adds a new family first and replaces the share of one already there", () => {
    let list = addFamily([], { id: "a", share: "1" });
    list = addFamily(list, { id: "b", share: "2" });
    expect(list.map((f) => f.id)).toEqual(["b", "a"]);
    list = nameFamily(list, "a", "The Okafors", "Ada");
    list = addFamily(list, { id: "a", share: "3" });
    expect(list).toEqual([
      { id: "b", share: "2" },
      { id: "a", share: "3", name: "The Okafors", child: "Ada" },
    ]);
    expect(removeFamily(list, "b")).toEqual([{ id: "a", share: "3", name: "The Okafors", child: "Ada" }]);
  });

  it("reads a share link and the list's own address", () => {
    expect(parseShareLink("#h=h_1&s=abc")).toEqual({ id: "h_1", share: "abc" });
    expect(parseShareLink("#h=h_1")).toBeNull();
    expect(parseOpenFamily("#family=h_1")).toBe("h_1");
    expect(parseOpenFamily("")).toBeNull();
  });
});

describe("the week's direction, by the service's rule", () => {
  it("says nothing until six days", () => {
    expect(weekDirection([100, 200, 300, 400, 500])).toBe("level");
  });
  it("compares the last three days with the ones before, ten percent either way", () => {
    expect(weekDirection([100, 100, 100, 100, 120, 120, 120])).toBe("up");
    expect(weekDirection([100, 100, 100, 100, 80, 80, 80])).toBe("down");
    expect(weekDirection([100, 100, 100, 100, 105, 105, 105])).toBe("level");
  });
  it("reads only the last seven days", () => {
    expect(weekDirection([1, 1, 1, 100, 100, 100, 100, 100, 100, 100])).toBe("level");
  });
});

it("prints a date without shifting it by the time zone", () => {
  expect(shortDate("2026-09-28")).toBe("Sep 28");
  expect(shortDate("nonsense")).toBe("nonsense");
});
