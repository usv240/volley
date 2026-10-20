"""The published running cost is recomputed, not remembered.

scripts/cost.py multiplies AWS list prices by usage measured on the live
stack and writes docs/cost.json. This fails if the file is stale against
the script, or if AWS.md quotes a different figure.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def _cost():
    spec = importlib.util.spec_from_file_location("cost", REPO / "scripts" / "cost.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.month()


def test_the_committed_cost_is_what_the_script_computes():
    assert json.loads((REPO / "docs" / "cost.json").read_text(encoding="utf-8")) == json.loads(json.dumps(_cost()))


def test_aws_md_quotes_the_computed_cost():
    cents = _cost()["cents"]
    assert f"About {cents} cents a family a month" in (REPO / "docs" / "AWS.md").read_text(encoding="utf-8")
