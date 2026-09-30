"""What the public text is allowed to say.

Every document a judge reads, and the site's own copy, are held to
three rules: no em dashes (house style, enforced rather than requested);
no claim that the count was validated on children, because it has not
been; and the video script must carry every narrated line from the
beats file, because the script is generated from it and a stale copy
would be the one public text nobody could reproduce.
"""

from __future__ import annotations

import json
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
        assert chr(0x2014) not in p.read_text(encoding="utf8"), p


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


def test_every_citation_in_public_text_is_resolved_in_the_citations_file():
    """No PMID or DOI appears on the site or in the documents unless the
    citations file carries it with what the study showed and what it
    did not. The file was resolved against PubMed and Crossref on the
    date it states, so a citation from memory cannot reach a judge."""
    record = json.loads((REPO / "docs" / "citations.json").read_text(encoding="utf8"))
    known_pmids = {c["pmid"] for c in record["citations"] if "pmid" in c}
    known_dois = {c["doi"].lower() for c in record["citations"] if "doi" in c}
    for c in record["citations"]:
        for field in ("key", "first", "year", "journal", "title", "showed", "did_not"):
            assert c.get(field), (c.get("key"), field)
        assert ("pmid" in c) or ("doi" in c), c["key"]
    seen_pmids: set[str] = set()
    seen_dois: set[str] = set()
    for p in PUBLIC:
        text = p.read_text(encoding="utf8")
        for m in re.finditer(r"PMID\s*(\d{7,9})", text):
            assert m.group(1) in known_pmids, (p.name, m.group(1))
            seen_pmids.add(m.group(1))
        for m in re.finditer(r"doi\s*(10\.\d{4,9}/[^\s,;)\"<]+)", text, re.I):
            doi = m.group(1).rstrip(".").lower()
            assert doi in known_dois, (p.name, doi)
            seen_dois.add(doi)
    # And the file is not padding: every study in it is used somewhere public.
    assert known_pmids <= seen_pmids, known_pmids - seen_pmids
    assert known_dois <= seen_dois, known_dois - seen_dois


def test_the_install_step_names_a_distribution_this_repository_owns():
    """`volley` on PyPI is somebody else's data validation library. The
    site's install step must name the distribution in apps/ingest."""
    pyproject = (REPO / "apps" / "ingest" / "pyproject.toml").read_text(encoding="utf8")
    name = re.search(r'^name = "([^"]+)"', pyproject, re.M).group(1)
    assert name != "volley"
    page = (REPO / "apps" / "web" / "src" / "app" / "page.tsx").read_text(encoding="utf8")
    assert f"pip install {name}" in page
    assert "pip install volley\"" not in page and "pip install volley\n" not in page
