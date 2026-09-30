"""The gate an agent's answer must pass before a parent hears it.

The same two rules the note obeys on the server, applied to a whole
conversation: every number in the answer must have come back from a
tool, and no forbidden word may appear. A model that is asked "how was
our talking today" and has the day's counts in front of it has no
reason to say any other number; if it does, the sentence is not
repeated. The gate is a function of the answer and the tool results,
so a test can hand it both and see it refuse.

Numbers are collected from tool results as they appear (turns, hours,
dates, the target) plus the twelve-hour form of anything that names an
hour, since "18" and "six in the evening" are the same fact. Dates
contribute their pieces, so "the 28th" is allowed when the tool said
2026-09-28.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from serve_return.coach import FORBIDDEN, digits_in

try:
    from volley_server.bedrock import sanitise
except ImportError:  # the server package is optional here; the same rule, restated

    def sanitise(text: str) -> str:
        em, en = chr(0x2014), chr(0x2013)
        out = re.sub(r"(?<=\d)\s*[" + en + em + r"]\s*(?=\d)", " to ", text)
        for dash in (em, en):
            out = out.replace(f" {dash} ", ", ").replace(dash, ", ")
        while ", ," in out:
            out = out.replace(", ,", ",")
        return " ".join(out.replace(" ,", ",").replace(",,", ",").split()).strip()


def spoken(text: str) -> str:
    """House style, then no markdown: the answer is read aloud or shown
    as a sentence, and asterisks are neither."""
    return sanitise(text.replace("**", "").replace("*", "")).strip()


HOUR_KEYS = ("hour",)


def _walk(value, key: str = "", out: set[str] | None = None) -> set[str]:
    out = set() if out is None else out
    if isinstance(value, bool):
        return out
    if isinstance(value, (int, float)):
        out.add(str(value))
        if isinstance(value, float) and value.is_integer():
            out.add(str(int(value)))
        if isinstance(value, int) and any(k in key for k in HOUR_KEYS) and 0 <= value <= 23:
            out.add(str(value % 12 or 12))
            out.add(f"{value:02d}")
    elif isinstance(value, str):
        for piece in re.findall(r"\d+(?:\.\d+)?", value):
            out.add(piece)
            if piece.isdigit() and len(piece) == 2 and piece.startswith("0"):
                out.add(piece.lstrip("0") or "0")
    elif isinstance(value, dict):
        for k, v in value.items():
            _walk(v, str(k), out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _walk(v, key, out)
    return out


def numbers_returned(tool_results: list[str]) -> set[str]:
    """Every number any tool returned, as strings, with hour and date
    variants. Results that are not JSON are scanned as text."""
    out: set[str] = set()
    for text in tool_results:
        try:
            _walk(json.loads(text), "", out)
        except (ValueError, TypeError):
            _walk(text, "", out)
    return out


@dataclass
class Verdict:
    ok: bool
    invented: set[str] = field(default_factory=set)
    forbidden: list[str] = field(default_factory=list)

    def reason(self) -> str:
        parts = []
        if self.invented:
            parts.append("numbers no tool returned: " + ", ".join(sorted(self.invented)))
        if self.forbidden:
            parts.append("words the coach never uses: " + ", ".join(self.forbidden))
        return "; ".join(parts)


def check(answer: str, tool_results: list[str]) -> Verdict:
    lower = answer.lower()
    forbidden = [w for w in FORBIDDEN if w.lower() in lower]
    allowed = numbers_returned(tool_results)
    invented = {d for d in digits_in(answer) if d not in allowed}
    return Verdict(ok=not invented and not forbidden, invented=invented, forbidden=forbidden)


def plain_rendering(tool_results: list[str]) -> str:
    """What a parent hears when the model's sentence was refused twice:
    the tool results themselves, one line per number, no adjectives."""
    lines = ["Here is what Volley returned, without a sentence around it:"]
    for text in tool_results:
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        for k, v in data.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                lines.append(f"  {k.replace('_', ' ')}: {v}")
            elif isinstance(v, str) and k in ("date", "direction", "best_day"):
                lines.append(f"  {k.replace('_', ' ')}: {v}")
    return "\n".join(lines)
