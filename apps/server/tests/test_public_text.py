"""What the public text is allowed to say.

Every document a judge reads, and the site's own copy, are held to
three rules: no em dashes (house style, enforced rather than requested);
no claim that the count was validated on children, because it has not
been; and the video script must carry every narrated line from the
beats file, because the script is generated from it and a stale copy
would be the one public text nobody could reproduce.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

PUBLIC = [
    REPO / "README.md",
    REPO / "FRICTION_LOG.md",
    REPO / "PRODUCT_FEEDBACK.md",
    REPO / "skills" / "volley" / "SKILL.md",
    REPO / "packages" / "serve-return" / "README.md",
    *sorted((REPO / "docs").glob("*.md")),
    REPO / "apps" / "web" / "src" / "app" / "page.tsx",
    REPO / "apps" / "web" / "src" / "components" / "Info.tsx",
]


def test_every_public_document_exists_and_is_read():
    assert len(PUBLIC) > 8
    for p in PUBLIC:
        assert p.exists(), p


def test_no_em_dashes_anywhere_public():
    for p in PUBLIC:
        assert "—" not in p.read_text(encoding="utf8"), p


def test_no_public_text_claims_validation_on_children():
    pattern = re.compile(r"validated (?:on|with|against) (?:real |recruited |young )?(?:children|kids|toddlers|families|parents)", re.I)
    for p in PUBLIC:
        text = p.read_text(encoding="utf8")
        for m in pattern.finditer(text):
            # A quoted mention names the phrase as the thing forbidden; that is allowed.
            if m.start() > 0 and text[m.start() - 1] == '"':
                continue
            context = text[max(0, m.start() - 60): m.end() + 60]
            assert "not " in context or "has not" in context or "never" in context, (p, context)


def test_the_video_script_carries_every_narrated_line():
    beats = (REPO / "video" / "beats.py").read_text(encoding="utf8")
    script = (REPO / "docs" / "VIDEO_SCRIPT.md").read_text(encoding="utf8")
    lines = []
    for chunk in beats.split("say=(")[1:]:
        block = re.split(r"\n\s*\),", chunk)[0]
        lines.append("".join(re.findall(r'"((?:[^"\\]|\\.)*)"', block)).replace('\\"', '"'))
    assert len(lines) >= 8
    for line in lines:
        assert line in script, line[:60]
