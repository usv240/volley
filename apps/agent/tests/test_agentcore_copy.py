"""The Coach hosted on AgentCore is the same code as the one in the repository."""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOSTED = REPO / "apps" / "agentcore" / "app" / "coach"
PAIRS = [(REPO / "apps" / "agent" / "volley_agent" / f, HOSTED / "volley_agent" / f) for f in ("coach.py", "gate.py", "models.py")]
PAIRS += [(REPO / "packages" / "serve-return" / "serve_return" / f, HOSTED / "serve_return" / f) for f in ("__init__.py", "coach.py", "rule.py")]


@pytest.mark.parametrize("local,hosted", PAIRS, ids=[p[1].name + ":" + p[1].parent.name for p in PAIRS])
def test_the_hosted_copy_is_byte_for_byte_the_local_one(local, hosted):
    assert hosted.read_bytes() == local.read_bytes(), f"copy {local} into {hosted}"
