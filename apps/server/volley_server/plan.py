"""The week's plan: what a home visitor would write, from the counts alone.

A home visitor looks at a family's week and says where to spend the
effort: keep the hour that already works, try one small thing in the
hour that is quiet while the child is there, and one thing for the
weekend. This does that from the last seven days of counts. The rules
choose the hours and the numbers; Claude on Bedrock writes the three
lines, as warm and specific as a good visitor would; the same gate as the
note refuses any line with a number the facts do not hold, or a line
with nothing to do. A plain template is the floor.

Only counts go in: hours, turns and the week's direction. No word was
ever stored, so none can be sent.
"""

from __future__ import annotations

import re

from serve_return.coach import FORBIDDEN, digits_in, has_action

from .bedrock import MODEL_LADDER, _bedrock_create_text, sanitise


def _clock(hour: int) -> str:
    h = hour % 24
    return "noon" if h == 12 else "midnight" if h == 0 else f"{h % 12} in the {'morning' if h < 12 else 'afternoon' if h < 17 else 'evening'}"


def week_facts(days: list[dict]) -> dict | None:
    """The hours worth a plan: the hour with most turns across the week, and
    the hour with fewest while the child was there (as days record it)."""
    last = days[-7:]
    if not last:
        return None
    totals: dict[int, list[int]] = {}
    for d in last:
        for h in d.get("hours", []):
            if h.get("utterances_child", 0) > 0:
                totals.setdefault(int(h["hour"]), []).append(int(h.get("turns", 0)))
    if not totals:
        return None
    avg = {hr: round(sum(v) / len(v)) for hr, v in totals.items()}
    best = max(avg, key=lambda hr: (avg[hr], -hr))
    quiet = min(avg, key=lambda hr: (avg[hr], hr))
    return {"days": len(last), "best_hour": best, "best_turns": avg[best],
            "quiet_hour": quiet if quiet != best else None, "quiet_turns": avg[quiet] if quiet != best else None}


def allowed(f: dict) -> set[str]:
    out = {str(f["days"]), str(f["best_turns"]), str(f["best_hour"] % 12 or 12), str(f["best_hour"] % 24), "1", "2"}
    if f.get("quiet_hour") is not None:
        out |= {str(f["quiet_turns"]), str(f["quiet_hour"] % 12 or 12), str(f["quiet_hour"] % 24)}
    return out


def template(f: dict, child: str | None) -> list[str]:
    who = child or "your child"
    lines = [f"Around {_clock(f['best_hour'])} is your best hour, about {f['best_turns']} turns a day. Keep it: ask {who} one question then and wait for the whole answer."]
    if f.get("quiet_hour") is not None:
        lines.append(f"Around {_clock(f['quiet_hour'])} {who} is with you but the talk is quiet. Try naming what you are both doing and ask what comes next.")
    lines.append(f"At the weekend, try one meal with no screens and let {who} tell the story of their day.")
    return lines


SYSTEM = "\n".join([
    "You are a warm, practical home visitor writing a family's plan for the coming week, from counts of the back-and-forth between a parent and their child.",
    "Write exactly three lines, each one sentence or two, each naming one small thing to do and when.",
    "Each line must contain one of the words try, ask, let or wait, because it tells the parent what to do; 'keep doing what you do' is not a thing to do.",
    "Line one keeps the best hour going. Line two gives the quiet hour one gentle idea, or if there is none, a second idea for the best hour. Line three is for the weekend.",
    "Use only the numbers and hours given; never add a number. Name hours as a person says them, for example 'around six in the evening'.",
    "Never judge, never compare with other families, never mention delay, risk, IQ, percentiles or development. No emojis. No dashes as punctuation.",
    "Reply with the three lines only, one per line.",
])


def accept(lines: list[str], f: dict) -> bool:
    if len(lines) != 3:
        return False
    ok_numbers = allowed(f)
    for line in lines:
        low = line.lower()
        if any(w.lower() in low for w in FORBIDDEN) or not has_action(line):
            return False
        if not digits_in(line) <= ok_numbers:
            return False
    return True


def phrase(f: dict, child: str | None, deps: dict | None = None) -> dict:
    deps = deps or {}
    floor = template(f, child)
    out = {"lines": floor, "source": "template", "model": None, "attempts": []}
    enabled = deps.get("enabled")
    create = deps.get("create_text")
    if not enabled and create is None:
        import os

        if os.environ.get("VOLLEY_BEDROCK") != "1":
            return out
    create = create or _bedrock_create_text
    facts = [f"days counted: {f['days']}", f"best hour: {f['best_hour']}:00 ({_clock(f['best_hour'])}), about {f['best_turns']} turns a day"]
    if f.get("quiet_hour") is not None:
        facts.append(f"quiet hour with the child there: {f['quiet_hour']}:00 ({_clock(f['quiet_hour'])}), about {f['quiet_turns']} turns a day")
    if child:
        facts.append(f"child's name: {child}")
    prompt = "Facts:\n" + "\n".join(facts) + "\n\nWrite the three lines now."
    for model in deps.get("models") or MODEL_LADDER:
        try:
            raw = create(SYSTEM, prompt, model)
            # Split before cleaning: sanitise joins whitespace, newlines included.
            lines = [sanitise(re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", l)) for l in raw.splitlines() if l.strip()]
            if accept(lines, f):
                out["attempts"].append({"model": model, "ok": True})
                return {"lines": lines, "source": "bedrock", "model": model, "attempts": out["attempts"]}
            out["attempts"].append({"model": model, "ok": False, "reason": "a number, a word, or a line with nothing to do"})
        except Exception as err:  # noqa: BLE001
            out["attempts"].append({"model": model, "ok": False, "reason": str(err)[:200]})
    return out
