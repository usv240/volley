/**
 * The families a coach follows, remembered in this browser only.
 *
 * Every share link opened on /coach/ adds one entry: the household's id
 * and its read-only share token, plus the name the service returned the
 * last time it answered, so a family that later ends the share can still
 * be named in the list. Nothing here is sent anywhere; the list lives in
 * local storage and "Remove from this browser" only edits that list.
 *
 * Pure functions over a storage-shaped object, so the rules are tested
 * without a browser.
 */

export interface Family {
  id: string;
  share: string;
  name?: string;
  child?: string | null;
}

export interface KeyValue {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export const LIST_KEY = "volley-coach-families";
/** Before the list existed, /coach/ remembered one family under this key. */
export const LEGACY_KEY = "volley-coach";

function isFamily(x: unknown): x is Family {
  if (!x || typeof x !== "object") return false;
  const f = x as Record<string, unknown>;
  return typeof f.id === "string" && f.id.length > 0 && typeof f.share === "string" && f.share.length > 0;
}

function parse(raw: string | null): unknown {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function readFamilies(store: KeyValue): Family[] {
  const listed = parse(store.getItem(LIST_KEY));
  let list: Family[] = Array.isArray(listed) ? listed.filter(isFamily) : [];
  const legacy = parse(store.getItem(LEGACY_KEY)) as { id?: unknown; key?: unknown } | null;
  if (legacy && typeof legacy.id === "string" && typeof legacy.key === "string" && legacy.id && legacy.key) {
    list = addFamily(list, { id: legacy.id, share: legacy.key });
    writeFamilies(store, list);
    store.removeItem(LEGACY_KEY);
  }
  return list;
}

export function writeFamilies(store: KeyValue, list: Family[]): void {
  store.setItem(LIST_KEY, JSON.stringify(list));
}

/** A family already in the list keeps its place and takes the newer share; a new one goes first. */
export function addFamily(list: Family[], f: Family): Family[] {
  const at = list.findIndex((x) => x.id === f.id);
  if (at === -1) return [f, ...list];
  const next = list.slice();
  next[at] = { ...list[at], share: f.share };
  return next;
}

export function removeFamily(list: Family[], id: string): Family[] {
  return list.filter((x) => x.id !== id);
}

/** Remember the name the service gave, so a later refusal can still say whose share ended. */
export function nameFamily(list: Family[], id: string, name: string, child: string | null): Family[] {
  return list.map((x) => (x.id === id ? { ...x, name, child } : x));
}

/** `#h=<household>&s=<share>`, the fragment a parent's share link carries. */
export function parseShareLink(hash: string): { id: string; share: string } | null {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const id = params.get("h");
  const share = params.get("s");
  return id && share ? { id, share } : null;
}

/** `#family=<household>`, the list's own address for one family's page. */
export function parseOpenFamily(hash: string): string | null {
  return new URLSearchParams(hash.replace(/^#/, "")).get("family");
}

/**
 * The week's direction by the service's own rule (apps/server week_view):
 * the last three days against the ones before, ten percent either way,
 * and only once there are six days to compare.
 */
export function weekDirection(turns: number[]): "up" | "down" | "level" {
  const last = turns.slice(-7);
  if (last.length < 6) return "level";
  const recent = last.slice(-3).reduce((a, b) => a + b, 0) / 3;
  const earlier = last.slice(0, -3);
  const before = earlier.reduce((a, b) => a + b, 0) / Math.max(1, earlier.length);
  if (before > 0 && recent > before * 1.1) return "up";
  if (before > 0 && recent < before * 0.9) return "down";
  return "level";
}

/** "2026-09-28" as "Sep 28", read as a calendar date with no time zone shift. */
export function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

/**
 * The note is written to the parent ("you and Asha", "your best hour").
 * A coach reading it is not the "you", so the coach's view retells it in
 * the third person: the parent, the family, the two of them. Only the
 * pronouns change; every number and hour stays as the family received it.
 */
export function noteForCoach(text: string): string {
  const rules: [RegExp, string][] = [
    [/\bbetween you two\b/gi, "between the two of them"],
    [/\bthe two of you\b/gi, "the two of them"],
    [/\bboth of you\b/gi, "both of them"],
    [/\byou two\b/gi, "the two of them"],
    [/\byou and\b/gi, "the parent and"],
    [/\byourself\b/gi, "themselves"],
    [/\byours\b/gi, "the family's"],
    [/\byour child\b/gi, "the child"],
    [/\byour\b/gi, "the family's"],
    [/\byou['’]re\b/gi, "the parent is"],
    [/\byou['’]ve\b/gi, "the parent has"],
    [/\byou['’]ll\b/gi, "the parent will"],
    [/\byou['’]d\b/gi, "the parent would"],
    [/\byou are\b/gi, "the parent is"],
    [/\byou were\b/gi, "the parent was"],
    [/\byou have\b/gi, "the parent has"],
    [/\byou don['’]t\b/gi, "the parent doesn't"],
    [/\byou do\b/gi, "the parent does"],
    [/\byou\b/gi, "the parent"],
  ];
  let out = text;
  for (const [re, to] of rules) {
    out = out.replace(re, (m, offset: number, whole: string) => {
      // Keep a capital where the sentence starts.
      const start = offset === 0 || /[.!?]\s+$/.test(whole.slice(0, offset));
      return start && /^[A-Z]/.test(m) ? to[0].toUpperCase() + to.slice(1) : to;
    });
  }
  return out;
}
