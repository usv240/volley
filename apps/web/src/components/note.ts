/**
 * Tomorrow's note, as the service returns it from
 * GET /v1/households/{id}/note, and the one line the card puts under it.
 * Kept free of React so the wording is tested once.
 */

export interface Note {
  text: string;
  source: "bedrock" | "template";
  model: string | null;
  fact: { kind: string; hour: number | null; value: number | null };
  simulated: boolean;
}

/** "best_hour" as "best hour". */
export function factInWords(kind: string): string {
  return kind.replace(/_/g, " ");
}

/** Who wrote the sentence shown, and from which fact. */
export function noteSourceLabel(source: Note["source"], factKind: string): string {
  const who = source === "bedrock" ? "written by Claude on Amazon Bedrock" : "the template layer; the model was not used";
  return `${who}, from the fact: ${factInWords(factKind)}`;
}

/** The line under the template sentence when the service could not be read. */
export const FALLBACK_LABEL = "the template layer, shown because the live note could not be read just now; from the fact: best hour";

/** The body, checked for the shape the card needs; anything else is null. */
export function parseNote(body: unknown): Note | null {
  if (!body || typeof body !== "object") return null;
  const b = body as Record<string, unknown>;
  const f = b.fact as Record<string, unknown> | undefined;
  if (typeof b.text !== "string" || !b.text.trim() || !f || typeof f.kind !== "string") return null;
  return {
    text: b.text,
    source: b.source === "bedrock" ? "bedrock" : "template",
    model: typeof b.model === "string" ? b.model : null,
    fact: {
      kind: f.kind,
      hour: typeof f.hour === "number" ? f.hour : null,
      value: typeof f.value === "number" ? f.value : null,
    },
    simulated: b.simulated === true,
  };
}
