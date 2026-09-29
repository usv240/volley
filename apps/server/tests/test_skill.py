"""The Agent Skill and the server must name the same tools.

A skill is read by an agent and quoted at a parent, which makes it the
least supervised surface here. If it lists a tool the server does not
implement, or forgets one it does, the agent will either call something
that fails or never learn a tool exists. So the two are pinned to each
other, and the skill's words are held to the same forbidden list as the
note.
"""

from __future__ import annotations

import re
from pathlib import Path

from serve_return.coach import FORBIDDEN
from volley_server import TOOLS

SKILL = Path(__file__).resolve().parents[3] / "skills" / "volley" / "SKILL.md"


def listed_tools() -> list[str]:
    text = SKILL.read_text(encoding="utf8")
    section = text.split("## The tools")[1].split("## What the numbers mean")[0]
    return re.findall(r"^- \*\*`([a-z_]+)`\*\*", section, flags=re.M)


def bullets_of(section: str) -> list[str]:
    """Each bullet as one line, however it wrapped in the file."""
    out: list[str] = []
    for paragraph in re.split(r"\n\s*\n", section):
        for part in re.split(r"\n(?=- )", paragraph):
            joined = " ".join(part.split())
            if joined:
                out.append(joined)
    return out


def test_the_skill_lists_every_tool_and_nothing_else():
    assert SKILL.exists()
    listed = listed_tools()
    assert len(listed) > 3
    assert sorted(listed) == sorted(t["name"] for t in TOOLS)


def test_the_skill_says_there_is_no_transcript_and_keeps_the_forbidden_words_out_of_its_advice():
    text = SKILL.read_text(encoding="utf8")
    assert "no transcript" in text.lower() or "none exists" in text.lower()
    advice = text.split("## What the numbers mean")[1]
    # The forbidden words may appear only in the bullet that forbids them.
    for bullet in bullets_of(advice):
        if "never mention" in bullet.lower():
            continue
        for word in FORBIDDEN:
            assert word.lower() not in bullet.lower(), (word, bullet)
