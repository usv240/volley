"""Bedrock phrases the one thing for tomorrow; rules decide what it is.

The fact comes from the counts, chosen by `serve_return.coach.pick`,
deterministic and tested. Claude on Bedrock may phrase it warmly. It may
not add a number, remove one, or say anything a parent would hear as a
verdict; the caller checks every digit against the fact and the
forbidden words against the text, and uses the template if either rule
is broken. Degrades in warmth, never in accuracy.

A model ladder, not a model. Three Claude models are tried in order;
VOLLEY_MODEL_IDS replaces the ladder outright, VOLLEY_MODEL_ID names a
preference tried first. Every note reports which rung wrote it.
"""

from __future__ import annotations

import os
import re

DEFAULT_LADDER = [
    "us.anthropic.claude-sonnet-5",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
]


def build_model_ladder(env=None) -> list[str]:
    env = os.environ if env is None else env
    explicit = env.get("VOLLEY_MODEL_IDS")
    if explicit:
        ladder = [m.strip() for m in explicit.split(",") if m.strip()]
        if ladder:
            return ladder
    preferred = (env.get("VOLLEY_MODEL_ID") or "").strip()
    return ([preferred] if preferred else []) + [m for m in DEFAULT_LADDER if m != preferred]


MODEL_LADDER = build_model_ladder()

SYSTEM = "\n".join(
    [
        "You phrase one thing for tomorrow for a parent, from a fact computed by a program that counted the back-and-forth between the parent and their child today.",
        "Rules, all mandatory:",
        "1. Use only the fact given. Never add events, causes, numbers, comparisons or reassurances that are not stated.",
        "2. Never alter a number or an hour. Do not introduce any number that is not in the fact.",
        "3. Never judge the parent, never compare with other families, never mention delay, risk, IQ, percentiles or development. It is a count, like steps.",
        "4. Two sentences. Warm, plain, second person, present tense. No emojis. No dashes of any kind as punctuation.",
        "5. Name the hour the way a person says it, for example 'around six in the evening'.",
        "Reply with the two sentences only.",
    ]
)


def facts_text(fact: dict, child: str | None) -> str:
    who = child or "your child"
    lines = [f"kind: {fact['kind']}", f"child: {who}"]
    if fact.get("hour") is not None:
        h = fact["hour"] % 24
        lines.append(f"hour: {h}:00 ({h % 12 or 12} in the {'morning' if h < 12 else 'afternoon' if h < 17 else 'evening'})")
    if fact.get("value") is not None:
        lines.append(f"value: {fact['value']}")
    if fact.get("target") is not None:
        lines.append(f"target: {fact['target']}")
    return "\n".join(lines)


def sanitise(text: str) -> str:
    """Enforce the house style instead of asking for it: dashes become
    commas or 'to', double commas collapse, whitespace settles."""
    out = re.sub(r"(?<=\d)\s*[–—]\s*(?=\d)", " to ", text)
    for dash in ("—", "–"):
        out = out.replace(f" {dash} ", ", ")
        out = out.replace(dash, ", ")
    while ", ," in out:
        out = out.replace(", ,", ",")
    out = out.replace(" ,", ",").replace(",,", ",")
    return " ".join(out.split()).strip()


def _bedrock_create_text(system: str, user: str, model: str) -> str:
    from anthropic import AnthropicBedrock  # lazy: tests inject a fake

    client = AnthropicBedrock(aws_region=os.environ.get("AWS_REGION", "us-east-1"))
    response = client.messages.create(model=model, max_tokens=200, system=system, messages=[{"role": "user", "content": user}])
    if getattr(response, "stop_reason", None) == "refusal":
        raise RuntimeError("model declined")
    text = " ".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
    if not text:
        raise RuntimeError("empty response")
    return text


def phrase_note(fact: dict, child: str | None, floor: str, accept, deps: dict | None = None) -> dict:
    """The note with its provenance. ``accept(text)`` is the caller's gate:
    every digit from the fact and no forbidden word, or the floor is used."""
    deps = deps or {}
    facts = facts_text(fact, child)
    fallback = {"text": floor, "source": "template", "facts_text": facts, "model": None, "attempts": []}
    enabled = deps.get("enabled", os.environ.get("VOLLEY_BEDROCK") == "1")
    create = deps.get("create_text")
    if not enabled and create is None:
        return fallback
    create = create or _bedrock_create_text
    models = deps.get("models") or MODEL_LADDER
    prompt = f"Fact:\n{facts}\n\nWrite the two sentences now."
    attempts: list[dict] = []
    for model in models:
        try:
            text = sanitise(create(SYSTEM, prompt, model))
            if len(text) > 400:
                attempts.append({"model": model, "ok": False, "reason": "response too long"})
                continue
            if not accept(text):
                attempts.append({"model": model, "ok": False, "reason": "a number or a word not allowed"})
                continue
            attempts.append({"model": model, "ok": True})
            return {"text": text, "source": "bedrock", "facts_text": facts, "model": model, "attempts": attempts}
        except Exception as err:  # noqa: BLE001
            attempts.append({"model": model, "ok": False, "reason": str(err)[:200]})
    return {**fallback, "attempts": attempts}
